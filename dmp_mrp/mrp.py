# -*- encoding: utf-8 -*-
from openerp.osv import fields,osv
import datetime

class mrp_bom(osv.osv):
    _inherit = 'mrp.bom'
    _order = "sequence asc, id desc"
    
    def _get_full_name(self, cr, uid, ids, name=None, args=None, context=None):
        if context == None:
            context = {}
        res = {}
        for elmt in self.browse(cr, uid, ids, context=context):
            res[elmt.id] = self._get_one_full_name(elmt)
        return res

    def _get_one_full_name(self, elmt, level=20):
        if level<=0:
            return '...'
        if elmt.bom_id:
            parent_path = self._get_one_full_name(elmt.bom_id, level-1) + " / "
        else:
            parent_path = ''
        return parent_path + elmt.name  
       
    def _check_product(self, cr, uid, ids, context=None):
        """
            johnw, Override original one, only check the duplicated products on same BOM level, the duplicated products under variance BOM level are allowed
        """
        all_prod = []
        res = True
        for bom in self.browse(cr, uid, ids, context=context):
            if bom.product_id.id in all_prod:
                res = False
                break
            all_prod.append(bom.product_id.id)
        return res
    
    _columns = {
                'code': fields.char('Reference', size=16, required=True, readonly=True),
                'complete_name': fields.function(_get_full_name, type='char', string='Full Name'),
                }
    
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'BOM Reference must be unique!'),
        ('name_uniq', 'unique(bom_id,name)', 'BOM Name must be unique per parent BOM!'),
        ]
    
    _constraints = [
        (_check_product, 'BoM line product should not be duplicate under one BoM.', ['product_id']),
        ] 
    
    '''
    SQL to update current data
    update mrp_bom set code = trim(to_char(id,'0000'))
    '''
    def default_get(self, cr, uid, fields_list, context=None):
        values = super(mrp_bom,self).default_get(cr, uid, fields_list, context)
        values.update({'code':self.pool.get('ir.sequence').get(cr, uid, 'mrp.bom')})
        return values
    
    #add the code return in the name
    def name_get(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not len(ids):
            return []
        result = []
        for bom in self.browse(cr, user, ids, context=context):
            if bom.id <= 0:
                result.append((bom.id,''))
                continue
            result.append((bom.id,'[%s]%s'%(bom.code,self._get_one_full_name(bom))))
                          
        return result
    
    #add the code search in the searching
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name:
            ids = self.search(cr, user, [('code','=',name)]+ args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('name','=',name)]+ args, limit=limit, context=context)
            if not ids:
                ids = set()
                ids.update(self.search(cr, user, args + [('code',operator,name)], limit=limit, context=context))
                if not limit or len(ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    ids.update(self.search(cr, user, args + [('name',operator,name)], limit=(limit and (limit-len(ids)) or False) , context=context))
                ids = list(ids)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result    
                
    def copy_data(self, cr, uid, id, default=None, context=None):
        res = super(mrp_bom,self).copy_data(cr, uid, id, default=default, context=context)
        if res:
            res.update({'bom_id':False,'code':self.pool.get('ir.sequence').get(cr, uid, 'mrp.bom'),'bom_routing_ids':False})
        return res  
    
class mrp_production(osv.osv):
    _inherit = 'mrp.production'
    _order = 'id desc, priority, date_planned asc';
    _columns = {
        'location_src_id': fields.property(
            'stock.location',
            type='many2one',
            relation='stock.location',
            string="Raw Materials Location",
            view_load=True,
            required=True,
            readonly=True, 
            states={'draft':[('readonly',False)]},
            help="Location where the system will look for components."),
        'location_dest_id': fields.property(
            'stock.location',
            type='many2one',
            relation='stock.location',
            string="Finished Products Location",
            view_load=True,
            required=True,
            readonly=True, 
            states={'draft':[('readonly',False)]},
            help="Location where the system will stock the finished products."),     
    }
    
    _defaults={'name': '/',}
        
    def create(self, cr, uid, vals, context=None):
        if vals.get('name','/')=='/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'mrp.production') or '/'
        return super(mrp_production,self).create(cr, uid, vals, context=context)
    
    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update({
            'workcenter_lines' : [],
            'date_start' : None,
            'date_finished' : None,
        })
        return super(mrp_production, self).copy(cr, uid, id, default, context)
    
    def _compute_planned_workcenter(self, cr, uid, ids, context=None, mini=False):
        resu = super(mrp_production, self)._compute_planned_workcenter(cr, uid, ids, context, mini) 
        #remove the end date setting
        super(mrp_production, self).write(cr, uid, ids, {'date_finished': False})
        return resu    

    def action_in_production(self, cr, uid, ids, context=None):
        resu = super(mrp_production,self).action_in_production(cr, uid, ids)
        #fix the time issue to use utc now, by johnw
        self.write(cr, uid, ids, {'date_start': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')})
        return resu
    
    def action_production_end(self, cr, uid, ids, context=None):
        resu = super(mrp_production,self).action_production_end(cr, uid, ids)
        #fix the time issue to use utc now, by johnw
        self.write(cr, uid, ids, {'date_finished': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')})
        return resu
        
class mrp_production_workcenter_line(osv.osv):
    _inherit = 'mrp.production.workcenter.line'
            
    _columns = {
        'code': fields.char('Reference', size=16, required=True, readonly=True),    
        }
    _defaults = {'code':lambda self, cr, uid, obj, ctx=None: self.pool.get('ir.sequence').get(cr, uid, 'mrp.production.workcenter.line') or '/',}
                 
    #add the code return in the name
    def name_get(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not len(ids):
            return []
        result = []
        for wo in self.browse(cr, user, ids, context=context):
            if wo.id <= 0:
                result.append((wo.id,''))
                continue
            result.append((wo.id,'[%s]%s'%(wo.code,wo.name)))
                          
        return result
    
    #add the code search in the searching
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name:
            ids = self.search(cr, user, [('code','=',name)]+ args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('name','=',name)]+ args, limit=limit, context=context)
            if not ids:
                ids = set()
                ids.update(self.search(cr, user, args + [('code',operator,name)], limit=limit, context=context))
                if not limit or len(ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    ids.update(self.search(cr, user, args + [('name',operator,name)], limit=(limit and (limit-len(ids)) or False) , context=context))
                ids = list(ids)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result