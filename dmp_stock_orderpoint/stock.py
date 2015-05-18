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
from openerp.osv import fields,osv
import openerp.addons.decimal_precision as dp
from openerp.addons.procurement.procurement import stock_warehouse_orderpoint as stock_warehouse_orderpoint_sup

def stock_warehouse_orderpoint_default_get(self, cr, uid, fields, context=None):
    res = super(stock_warehouse_orderpoint_sup, self).default_get(cr, uid, fields, context)
    # default 'warehouse_id' and 'location_id'
    if 'warehouse_id' not in res:
        '''
        override the parent's logic, to avoid the warehouse reading right issue under multi company's environment
        '''
#            warehouse = self.pool.get('ir.model.data').get_object(cr, uid, 'stock', 'warehouse0', context)
        warehouse_ids = self.pool.get('stock.warehouse').search(cr, uid, [],context=context)
        res['warehouse_id'] = warehouse_ids[0]
    if 'location_id' not in res:
        warehouse = self.pool.get('stock.warehouse').browse(cr, uid, res['warehouse_id'], context)
        res['location_id'] = warehouse.lot_stock_id.id
    return res

stock_warehouse_orderpoint_sup.default_get = stock_warehouse_orderpoint_default_get      

class stock_warehouse_orderpoint(osv.osv):
    _inherit = "stock.warehouse.orderpoint"
    
    def _product_available(self, cr, uid, ids, field_names=None, arg=False, context=None):
        """ Finds the incoming and outgoing quantity of product.
        @return: Dictionary of values
        """
        if not field_names:
            field_names = []
        if context is None:
            context = {}
        res = {}
        for id in ids:
            res[id] = {}.fromkeys(field_names, 0.0)
        prod_obj = self.pool.get('product.product')
        for f in field_names:
            for op in self.browse(cr, uid, ids, context=context):
                c = context.copy()
                c['location'] = op.location_id.id
                if f == 'virtual_available':
                    c.update({ 'states': ('confirmed','waiting','assigned','done'), 'what': ('in', 'out') })
                prod_id = op.product_id.id
                stock = prod_obj.get_product_available(cr, uid, [prod_id], context=c)
                res[op.id][f] = stock.get(prod_id, 0.0)
        return res
        
    _columns = {
        'virtual_available': fields.function(_product_available, multi='qty_available',
            type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
            string='Forecasted Quantity',)
        }
    def create(self, cr, uid, vals, context=None):
        if not 'product_uom' in vals:
            prod = self.pool.get('product.product').browse(cr, uid, vals['product_id'], context=context)
            if prod:
                vals.update({'product_uom':prod.uom_id.id})
        return super(stock_warehouse_orderpoint,self).create(cr, uid, vals, context)