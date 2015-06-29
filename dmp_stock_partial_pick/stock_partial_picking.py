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

class stock_partial_picking_line(osv.TransientModel):
    _inherit = "stock.partial.picking.line"
    _columns = {
        'quantity_max' : fields.float("Max Quantity", digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'quantity_out_available' : fields.float("Avail Quantity", digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'pick_type': fields.selection([('out', 'Sending Goods'), ('in', 'Getting Goods'), ('internal', 'Internal')], 'Shipping Type', readonly=True),
        'state': fields.char('Move State', size=8)
    }

class stock_partial_picking(osv.osv_memory):
    _inherit = "stock.partial.picking"
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        #do the stock move available checking again, if there are any not ready fully. 
        picking_id = context.get('active_id')
        if picking_id:
            pick = self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context)
            move_ids = [x.id for x in pick.move_lines if x.state == 'confirmed']
            if move_ids:
                self.pool.get('stock.move').action_assign(cr, uid, move_ids)      
        return super(stock_partial_picking, self).default_get(cr, uid, fields, context=context)   
            
    def _partial_move_for(self, cr, uid, move, context=None):
        partial_move = super(stock_partial_picking, self)._partial_move_for(cr, uid, move)
        #for the internal/out picking, need control the available out quantity        
        if move.picking_id.type in('internal', 'out'):
            quantity = min(partial_move['quantity'], move.quantity_out_available)
            partial_move.update({'quantity': quantity,'quantity_out_available':move.quantity_out_available})
            
        #the max quantity that user can deliver and the picking type
        partial_move.update({'quantity_max':move.product_qty, 'pick_type':move.picking_id.type, 'state':move.state})
        return partial_move

    def do_partial(self, cr, uid, ids, context=None):
        partial = self.browse(cr, uid, ids[0], context=context)
        picking_type = partial.picking_id.type
        prod_obj = self.pool.get('product.product')
        move_obj = self.pool.get('stock.move')
        for wizard_line in partial.move_ids:
            if wizard_line.quantity <= 0:
                raise osv.except_osv(_('Error!'), _('[%s]%s, quantity %s must be greater than zero!') % (wizard_line.product_id.default_code, wizard_line.product_id.name, wizard_line.quantity))
            #user deliver quantity can not be larger than the stock move's original quantity
            if wizard_line.quantity > wizard_line.quantity_max:
                raise osv.except_osv(_('Error!'), _('[%s]%s, quantity %s is larger than the original quantity %s') % (wizard_line.product_id.default_code, wizard_line.product_id.name, wizard_line.quantity,  wizard_line.quantity_max))
            #for the internal/out picking, the  deliver quantity can not be larger than the available quantity
            #if picking_type in('internal', 'out') and wizard_line.quantity > wizard_line.quantity_out_available:
            #    raise osv.except_osv(_('Error!'), _('[%s]%s, quantity %s is larger than the available quantity %s') % (wizard_line.product_id.default_code, wizard_line.product_id.name, wizard_line.quantity,  wizard_line.quantity_out_available))
            #johnw, 06/29/2015, remove the reservation logic, use onhand as the out available
            if picking_type in('internal', 'out'):
                #get onhand quantity as out available quantity
                c = context.copy()
                c['location'] = wizard_line.location_id.id
                prod_id = wizard_line.product_id.id
                qty_onhand = prod_obj._product_available(cr,uid,[prod_id],['qty_onhand'],context=c)
                quantity_out_available = qty_onhand[prod_id]['qty_onhand']
                if wizard_line.quantity > quantity_out_available:
                    #if quantity exceed available, refresh the original move's available data
                    move_obj.write(cr, uid, [wizard_line.move_id.id],
                                   {'quantity_out_available':quantity_out_available, 
                                    'quantity_out_missing':wizard_line.move_id.product_qty - quantity_out_available,
                                    'state':'confirmed'},
                                   context=context)
                    #must commit manually, otherwise data can not be saved because the error raised later
                    cr.commit()
                    #raise error
                    raise osv.except_osv(_('Error!'), _('[%s]%s, quantity %s is larger than the available quantity %s') % (wizard_line.product_id.default_code, wizard_line.product_id.name, wizard_line.quantity,  quantity_out_available))
            
        return super(stock_partial_picking,self).do_partial(cr, uid, ids, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
