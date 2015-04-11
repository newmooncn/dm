# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from dateutil.relativedelta import relativedelta
import time
import datetime
from openerp import netsvc
from openerp.osv import fields,osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT


class material_request(osv.osv):
    _name = "material.request"
    _inherit = "stock.picking"
    _table = "stock_picking"
    _description = "Material Request"
    _order = "name desc"        
    
    _columns = {
        'type': fields.selection([('out', 'Sending Goods'), ('in', 'Getting Goods'), ('internal', 'Internal'), ('mr', 'Material Request'), ('mrr', 'Material Return')], 
                                 'Request Type', required=True, select=True, readonly=True, states={'creating':[('readonly',False)]}),
        'move_lines': fields.one2many('material.request.line', 'picking_id', 'Request Products', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}),
        'mr_dept_id': fields.many2one('hr.department', 'Department', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'create_uid': fields.many2one('res.users', 'Creator',readonly=True),
        'account_move_ids': fields.one2many('account.move', 'picking_id',string = 'Stock Accout Move', readonly=False),
        'message_ids': fields.one2many('mail.message', 'res_id',
            domain=lambda self: [('model', '=', 'stock.picking')],
            auto_join=True,
            string='Messages',
            help="Messages and communication history"),
    }
    _defaults = {
        'type': 'mr',
        'move_type': 'one',
        'state': 'creating',
    }
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Order Reference must be unique!'),
    ]
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'move_type':self._defaults['move_type'],
        })
        res = super(material_request, self).copy(cr, uid, id, default, context)
        return res       

    def check_access_rights(self, cr, uid, operation, raise_exception=True):
        #override in order to redirect the check of acces rights on the stock.picking object
        return self.pool.get('stock.picking').check_access_rights(cr, uid, operation, raise_exception=raise_exception)

    def check_access_rule(self, cr, uid, ids, operation, context=None):
        #override in order to redirect the check of acces rules on the stock.picking object
        return self.pool.get('stock.picking').check_access_rule(cr, uid, ids, operation, context=context)

    def _workflow_trigger(self, cr, uid, ids, trigger, context=None):
        #override in order to trigger the workflow of stock.picking at the end of create, write and unlink operation
        #instead of it's own workflow (which is not existing)
        return self.pool.get('stock.picking')._workflow_trigger(cr, uid, ids, trigger, context=context)

    def _workflow_signal(self, cr, uid, ids, signal, context=None):
        #override in order to fire the workflow signal on given stock.picking workflow instance
        #instead of it's own workflow (which is not existing)
        return self.pool.get('stock.picking')._workflow_signal(cr, uid, ids, signal, context=context)
        
    def create(self, cr, uid, vals, context=None):
        vals['state'] = 'draft'
        if not vals.get('name') or vals.get('name','/')=='/':
            if vals['type'] == 'mrr':
                vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'material.request.return') or '/'
            else:
                vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'material.request') or '/'
                
        order =  super(material_request, self).create(cr, uid, vals, context=context)
        return order

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        #deal the 'date' datetime field query
        new_args = deal_args(self,args)
        return super(material_request,self).search(cr, user, new_args, offset, limit, order, context, count)    
                
class material_request_line(osv.osv):
    _name = "material.request.line"
    _inherit = "stock.move"
    _table = "stock_move"
    _description = "Material Request Line"
    def _amount_line(self, cr, uid, ids, prop, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.product_qty * line.price_unit
        return res    
    _columns = {
        'picking_id': fields.many2one('material.request', 'MR#', select=True,states={'done': [('readonly', True)]}),
        'mr_emp_id': fields.many2one('hr.employee','Employee'),
        'mr_notes': fields.text('Reason and use'),
        'mr_dept_id': fields.related('picking_id','mr_dept_id',string='Department',type='many2one',relation='hr.department',select=True),
        'mr_date_order': fields.related('picking_id','date',string='Order Date',type='datetime'),
        'pick_type': fields.related('picking_id','type',string='Picking Type',type='char'),
        'create_uid': fields.many2one('res.users', 'Creator',readonly=True),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
        #make the price's decimal precision as the 'Product Price'
        'price_unit': fields.float('Unit Price', digits_compute= dp.get_precision('Product Price'), help="Technical field used to record the product cost set by the user during a picking confirmation (when average price costing method is used)"),
        'product_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product Price'),
            required=True,states={'done': [('readonly', True)]},
            help="This is the quantity of products from an inventory "
                "point of view. For moves in the state 'done', this is the "
                "quantity of products that were actually moved. For other "
                "moves, this is the quantity of product that is planned to "
                "be moved. Lowering this quantity does not generate a "
                "backorder. Changing this quantity on assigned moves affects "
                "the product reservation, and should be done with care."
        ),
        'prod_categ_id': fields.related('product_id','categ_id',string='Product Category Type',type='many2one',relation="product.category",select=True),
    }
    _order = 'id'
    def default_mr_loc(self, cr, uid, context=None):
        if context is None:
            context = {}
        #material_request.type: mr or mrr
        req_type = context.get('req_type')
        if not req_type:
            req_type = 'mr'
        loc_stock_id = None
        loc_prod_id = None
        #get the default stock location
        cr.execute('select c.id \n'+
                    'from res_users a  \n'+
                    'left join stock_warehouse b on a.company_id = b.company_id  \n'+
                    'left join stock_location c on b.lot_stock_id = c.id \n'
                    'where a.id = %s', (uid,))
        loc_src = cr.fetchone()
        if loc_src:
            loc_stock_id = loc_src[0]           
        #get the default production location
        loc_obj = self.pool.get('stock.location')
        prod_loc_ids = loc_obj.search(cr,uid,[('usage','=','production')],context=context)
        if prod_loc_ids and prod_loc_ids[0]:
            prod_loc = loc_obj.browse(cr,uid,prod_loc_ids[0],context=context)
            loc_prod_id = prod_loc.id
        #set the locations by the request type
        loc_from_id = 0
        loc_to_id = 0
        if req_type == 'mr':
            if loc_stock_id:
                loc_from_id = loc_stock_id
            if loc_prod_id:
                loc_to_id = loc_prod_id
        if req_type == 'mrr':
            if loc_prod_id:
                loc_from_id = loc_prod_id
            if loc_stock_id:
                loc_to_id = loc_stock_id
        return loc_from_id, loc_to_id
                       
    def default_get(self, cr, uid, fields_list, context=None):
        resu = super(material_request_line,self).default_get(cr, uid, fields_list, context)
        loc_from_id, loc_to_id = self.default_mr_loc(cr, uid, context=context)
        resu.update({'location_id':loc_from_id, 'location_dest_id':loc_to_id})
        return resu
    
    def onchange_product_id(self, cr, uid, ids, prod_id=False, loc_id=False,
                            loc_dest_id=False, ):
        """ On change of product id, if finds UoM, UoS, quantity and UoS quantity.
        @param prod_id: Changed Product id
        @param loc_id: Source location id
        @param loc_dest_id: Destination location id
        @param partner_id: Address id of partner
        @return: Dictionary of values
        """
        if not prod_id:
            return {}
        user = self.pool.get("res.users").browse(cr,uid,uid)
        
        ctx = {'lang': user.lang,'location':loc_id}

        product = self.pool.get('product.product').browse(cr, uid, [prod_id], context=ctx)[0]
        uos_id  = product.uos_id and product.uos_id.id or False
        result = {
            'product_uom': product.uom_id.id,
            'product_uos': uos_id,
            'product_qty': product.qty_available,
            'product_uos_qty' : self.pool.get('stock.move').onchange_quantity(cr, uid, ids, prod_id, 1.00, product.uom_id.id, uos_id)['value']['product_uos_qty'],
            'prodlot_id' : False,
        }
        if not ids:
            result['name'] = product.partner_ref
        if loc_id:
            result['location_id'] = loc_id
        if loc_dest_id:
            result['location_dest_id'] = loc_dest_id
            
        #update the price_unit the and price_currency_id
        #default is the product's cost price
        price_unit = product.standard_price
        price_currency_id = None
        #get the final purchase price
        move_obj = self.pool.get('stock.move')
        #get the final purchase price
        move_ids = move_obj.search(cr,uid,[('product_id','=',prod_id),('state','=','done'),('type','=','in')],limit=1,order='create_date desc')
        if move_ids:
            move_price = move_obj.read(cr,uid,move_ids[0],['price_unit','price_currency_id'],context=ctx)
            price_unit = move_price['price_unit']
            price_currency_id = move_price['price_currency_id']
        result['price_unit'] = price_unit
        result['price_currency_id'] = price_currency_id
        
        return {'value': result}
    def check_access_rights(self, cr, uid, operation, raise_exception=True):
        #override in order to redirect the check of acces rights on the stock.picking object
        return self.pool.get('stock.move').check_access_rights(cr, uid, operation, raise_exception=raise_exception)

    def check_access_rule(self, cr, uid, ids, operation, context=None):
        #override in order to redirect the check of acces rules on the stock.picking object
        return self.pool.get('stock.move').check_access_rule(cr, uid, ids, operation, context=context)

    def _workflow_trigger(self, cr, uid, ids, trigger, context=None):
        #override in order to trigger the workflow of stock.picking at the end of create, write and unlink operation
        #instead of it's own workflow (which is not existing)
        return self.pool.get('stock.move')._workflow_trigger(cr, uid, ids, trigger, context=context)

    def _workflow_signal(self, cr, uid, ids, signal, context=None):
        #override in order to fire the workflow signal on given stock.picking workflow instance
        #instead of it's own workflow (which is not existing)
        return self.pool.get('stock.move')._workflow_signal(cr, uid, ids, signal, context=context)  
    
    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        #deal the 'date' datetime field query
        new_args = deal_args(self,args)
        return super(material_request_line,self).search(cr, user, new_args, offset, limit, order, context, count)   
    def create(self, cr, user, vals, context=None):
        #add the procut_uom set by product's purchase uom
        if 'product_uom' not in vals:
            prod = self.pool.get('product.product').browse(cr, user, vals['product_id'], context=context)
            vals.update({'product_uom':prod.uom_id.id})            
        resu = super(material_request_line,self).create(cr, user, vals, context=context)
        return resu  
    
class stock_move(osv.osv):
    _inherit = "stock.move" 
    _columns = {
        'type': fields.related('picking_id', 'type', type='selection', selection=[('out', 'Sending Goods'), ('in', 'Getting Goods'), ('internal', 'Internal'), ('mr', 'Material Request'), ('mrr', 'Material Return')], string='Shipping Type'),
    }    


from openerp.addons.stock.stock import stock_picking as stock_picking_super     

def fields_view_get_pick(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
    if view_type == 'form' and not view_id:
        mod_obj = self.pool.get('ir.model.data')
        if self._name == "stock.picking.in":
            model, view_id = mod_obj.get_object_reference(cr, uid, 'stock', 'view_picking_in_form')
        if self._name == "stock.picking.out":
            model, view_id = mod_obj.get_object_reference(cr, uid, 'stock', 'view_picking_out_form')
        if self._name == "material.request":
            model, view_id = mod_obj.get_object_reference(cr, uid, 'dmp_stock_mt', 'view_material_request_form')
    return super(stock_picking_super, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)

stock_picking_super.fields_view_get = fields_view_get_pick
    
def deal_args(obj,args):  
    new_args = []
    for arg in args:
        fld_name = arg[0]
        if fld_name in ('date', 'date_done'):
            fld_operator = arg[1]
            fld_val = arg[2]
            fld = obj._columns.get(fld_name)
            #['date','=','2013-12-12 16:00:00'] the '16' was generated for the timezone
            if fld._type == 'datetime' and fld_operator == "=" and fld_val.endswith('00:00'):
                time_start = [fld_name,'>=',fld_val]
                time_obj = datetime.datetime.strptime(fld_val,DEFAULT_SERVER_DATETIME_FORMAT)
                time_obj += relativedelta(days=1)
                time_end = [fld_name,'<=',time_obj.strftime(DEFAULT_SERVER_DATETIME_FORMAT)]
                new_args.append(time_start)
                new_args.append(time_end)
            else:
                new_args.append(arg)
        else:
            new_args.append(arg)    
    return new_args    
    
    