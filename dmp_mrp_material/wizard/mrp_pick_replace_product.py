# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP SA (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

class mrp_pick_replace_product_line(osv.TransientModel):
    _name = "mrp.pick.replace.product.line"
    _rec_name = 'move_id'
    _columns = {
        'replace_id' : fields.many2one('mrp.pick.replace.product', "Picking Replace", readonly=True),
        'move_id' : fields.many2one('stock.move', "Stock Move", readonly=True),
        'location_id' : fields.related('move_id','location_id', type='many2one', relation='stock.location',string="Location", readonly=True),
        'prod_old_id': fields.many2one('product.product', 'Current Product', readonly=True),
        'prod_new_id' : fields.many2one('product.product', 'Replaced Product', readonly=False),
        'product_qty': fields.float("Product Quantity", digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'prod_new_available': fields.float("Replaced Product Available Quantity", digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
    }
    def onchange_prod_new_id(self,cr ,uid, ids, prod_new_id, location_id, context=None):
        field_names=['qty_onhand','qty_out_assigned','qty_out_available']
        prod_qty = self.pool.get('product.product')._product_available(cr, uid, [prod_new_id], field_names, arg=False, context={'location':location_id})[prod_new_id]['qty_out_available']
        return {'value':{'prod_new_available':prod_qty}}

class mrp_pick_replace_product(osv.osv_memory):
    _name = "mrp.pick.replace.product"
    _rec_name = 'picking_id'
    _columns = {
        'picking_id' : fields.many2one('stock.picking.out', string="Picking", readonly=True),
        'replace_line_ids' : fields.one2many('mrp.pick.replace.product.line', "replace_id", string="Product Replacement", required=True),
    }

    def do_replace(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        order = self.browse(cr, uid, ids[0], context=context)
        
        field_names=['qty_onhand','qty_out_assigned','qty_out_available']
        prod_obj = self.pool.get('product.product')
        move_obj = self.pool.get('stock.move')
        for line in order.replace_line_ids:
            prod = line.prod_new_id
            '''
            1.check the available quantity
            '''
            context={'location':line.move_id.location_id.id}
            prod_qty = prod_obj._product_available(cr, uid, [prod.id], field_names, arg=False, context=context)[prod.id]['qty_out_available']
            if prod_qty < line.product_qty:
                raise osv.except_osv(_('Error!'), _('[%s]%s available quantity is %s, less than the moving quantity %s.') % (prod.default_code, prod.name, prod_qty, line.product_qty))
            ''''
            2.update
            1)stock_move (product_id, product_uom)
            2)mrp consuming move: stock_move.move_dest_id (product_id, product_uom)
            3)mrp material product line: mrp_production_product_line.consume_move_id=stock_move.move_dest_id(product_id, product_uom)
            4)related procurement.order
            '''
            vals = {'product_id':prod.id, 'product_uom':prod.uom_id.id}
            move_obj.write(cr, uid, line.move_id.id, vals, context=context)
            
            move_dest_id = line.move_id.move_dest_id.id
            move_obj.write(cr, uid, move_dest_id, vals, context=context)
            cr.execute("update mrp_production_product_line set product_id=%s, product_uom=%s where consume_move_id=%s and product_qty=%s",(prod.id, prod.uom_id.id, move_dest_id, line.product_qty))
            cr.execute("update procurement_order set product_id=%s, product_uom=%s where move_id=%s and product_qty=%s",(prod.id, prod.uom_id.id, move_dest_id, line.product_qty))            
                    
        self.pool.get('stock.picking').action_assign(cr, uid, [order.picking_id.id], context)
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
