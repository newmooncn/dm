# -*- encoding: utf-8 -*-
from openerp.osv import fields,osv
from openerp.tools.translate import _
from openerp import netsvc
import time
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from lxml import etree
from openerp.addons.mrp.mrp import rounding as mrp_rounding
from openerp import tools
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp

class mrp_bom(osv.osv):
    _inherit = 'mrp.bom'

    def _domain_bom_routing(self, cr=None, uid=None, ids=None, field_name=None, context=None):
        if cr is None:
            return []
        domain = []
        if field_name == 'bom_routing_ids':
            bom = self.read(cr, uid, ids[0], ['routing_id'],context=context)
            if bom.get('routing_id'):
                domain = domain + [('routing_id','=',bom.get('routing_id')[0])]
        if field_name == 'comp_routing_workcenter_ids':
            bom = self.browse(cr, uid, ids[0], context=context)
            if bom.bom_id and bom.bom_id.routing_id:
                domain = domain + [('routing_id','=',bom.bom_id.routing_id.id)]
        return domain 
    
    _columns = {
                #for top bom, define the work center and the components relationship
                'bom_routing_ids': fields.one2many('mrp.bom.routing.operation', 'bom_id', string='Routing BOM Matrix', domain_fnct=_domain_bom_routing),
#johnw, 01/10/2015, comment the field 'comp_routing_workcenter_ids', it will cause the table 
#mrp_bom_routing_operation creation without ID
#there are designment issues on this table, so only use it by "bom_routing_ids" now
#the code in mrp_view.xml are comment before, do not know the exact reason
                #for the component, define the sub components related work center from parent bom's routing definition, 
                #only show for the bom components(bom_id is not false)
                #'comp_routing_workcenter_ids': fields.many2many('mrp.routing.workcenter','mrp_bom_routing_operation','bom_comp_id','routing_workcenter_id',
                #                                                string='Work Centers', domain=_domain_bom_routing),
                }
    def copy_data(self, cr, uid, id, default=None, context=None):
        res = super(mrp_bom,self).copy_data(cr, uid, id, default=default, context=context)
        if res:
            res.update({'bom_routing_ids':False})
        return res            
          
class mrp_bom_routing_operation(osv.osv):
    _name = 'mrp.bom.routing.operation'
    _order = 'id desc'
    _rec_name = 'bom_comp_id'
    '''
    bom_comp_id:
    the component is the BOM that need manufacture, can be:
    1.same as bom_id
    2.the sub bom_id's sub BOM having bom_lines
    '''    
    _columns = {
        'bom_id': fields.many2one('mrp.bom', string='BOM', required=True),
        'routing_id': fields.many2one('mrp.routing', string='Routing', required=True),
        'routing_workcenter_id': fields.many2one('mrp.routing.workcenter', string='Routing Work Center', required=True ),
        'bom_comp_id': fields.many2one('mrp.bom', string='BOM Component', required=True ),
        'consume_material': fields.boolean('Consume Material')
    }
    _sql_constraints = [
        ('routing_wc_comp_uniq', 'unique(routing_workcenter_id,bom_comp_id)', 'You can not add duplicated "Routing Work Center"-"Component" with same BOM and Routing!'),
    ]
    _defaults = {'consume_material': True}
    def create(self, cr, uid, vals, context=None):
        if vals.has_key('bom_comp_id'):
            #added from the bom components screen
            if not vals.has_key('bom_id'):
                bom_comp = self.pool.get('mrp.bom').browse(cr, uid, vals['bom_comp_id'],context=context)
                vals['bom_id'] = bom_comp.bom_id.id
                vals['routing_id'] = bom_comp.bom_id.routing_id
        super(mrp_bom_routing_operation,self).create(cr, uid, vals, context=context)
        
class mrp_production(osv.osv):
    _inherit = 'mrp.production'
    _order = 'id desc, priority, date_planned asc';
    _columns = {
        'comp_lines': fields.one2many('mrp.wo.comp', 'mo_id', string='Components'),      
    }

    def action_compute(self, cr, uid, ids, properties=None, context=None):
        resu = super(mrp_production,self).action_compute(cr, uid, ids, properties, context)
        #johnw, generate manufacture/work order's components
        bom_oper_obj = self.pool.get('mrp.bom.routing.operation')
        wo_comp_obj = self.pool.get('mrp.wo.comp')
        for mo in self.browse(cr, uid, ids, context=context):
            if not mo.workcenter_lines:
                continue            
            for wo in mo.workcenter_lines:
                domain = [('bom_id','=',wo.bom_id.id),('routing_id','=',wo.routing_id.id,),('routing_workcenter_id','=',wo.routing_operation_id.id)]                
                comp_ids = bom_oper_obj.search(cr, uid, domain, context=context)
                for comp in bom_oper_obj.browse(cr, uid, comp_ids, context=context):
                    vals = {'mo_id':mo.id, 'wo_id':wo.id, 'comp_id': comp.bom_comp_id.id, 'bom_route_oper_id': comp.id, 'qty': comp.bom_comp_id.product_qty*mo.product_qty}
                    wo_comp_obj.create(cr, uid, vals, context=context)
                    
        return resu

class mrp_wo_comp(osv.osv):
    _name = 'mrp.wo.comp'    
    _columns = {
        'mo_id': fields.many2one('mrp.production', string='Manufacture Order', required=True),
        'wo_id': fields.many2one('mrp.production.workcenter.line', string='Work Order', required=True),
        'comp_id': fields.many2one('mrp.bom', string='Component', required=True ),
        #related bom/routing matrix id, can be empty if user add this component manually
        'bom_route_oper_id': fields.many2one('mrp.bom.routing.operation', string='Bom Routing Matrix'),
        #quantity need to be manufacture, from the bom definition if craeated by system
        'qty': fields.float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
        #quantity done
        'qty_done': fields.float('Quantity Done', digits_compute=dp.get_precision('Product Unit of Measure')),
        'state': fields.selection([('draft','Draft'),('cancel','Cancelled'),('startworking', 'In Progress'),('done','Finished')], string = 'Status'),
        'note': fields.text('Description', ),
    }
    _sql_constraints = [
        ('wo_comp_uniq', 'unique(wo_id,comp_id)', 'You can not add duplicated "Work Order Component" with same WorkOrder and Component!'),
    ]
    
class mrp_production_workcenter_line(osv.osv):
    _inherit = 'mrp.production.workcenter.line'
    _columns = {
        #the work order related components from bom, can generated from mrp_bom_workcenter_operation when executing action_compute()
        'comp_lines': fields.one2many('mrp.wo.comp', 'wo_id', string='Components'),    
    }  
