# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
'''
johnw, 04/28/2015
for the move with state is not assigned, the consume quantity can not be greater than move.quantity_out_available
This is used for the MRP material consuming now.
'''
class stock_move_consume(osv.osv_memory):
    _inherit = "stock.move.consume"
    _description = "Consume Products"

    _columns = {
        'quantity_out_available': fields.float('Quantity Available', digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
        'state': fields.char('State', size=10)
    }

    def default_get(self, cr, uid, fields, context=None):
        default = super(stock_move_consume,self).default_get(cr, uid, fields, context=context)
        move = self.pool.get('stock.move').browse(cr, uid, context['active_id'], context=context)
        default.update({'state':move.state, 'quantity_out_available':move.quantity_out_available})        
        return default

    def do_move_consume(self, cr, uid, ids, context=None):
        for data in self.browse(cr, uid, ids, context=context):
            if data.state != 'assigned' and data.product_qty > data.quantity_out_available:
                raise osv.except_osv(_('Error!'), _('Consume quantity (%d) can not be greater than available quantity (%d)!') \
                        % (data.product_qty, data.quantity_out_available))
        return super(stock_move_consume, self).do_move_consume(cr, uid, ids, context=context)

stock_move_consume()


class stock_move(osv.osv):
    _inherit = "stock.move" 
    def action_cusume_partial_write_before(self, cr, uid, move, update_val, context=None):
        '''
        if this is a partial consume, called by action_consume before write to the original move
        @param move_id: 
        @param update_val: the dict values will be update, keys:product_qty, product_uos_qty
        @return: True - can write; False - can not write
        We can update the update_val in our program, to update more values of the move
        '''
        #johnw, check the consumed_qty, and update the quantity_out_available for the moves not assigned
        product = move.product_id
        consumed_qty = move.product_qty - update_val['product_qty']
        if consumed_qty > move.product_qty:
            raise osv.except_osv(_('Error!'), _('[%s]%s consume quantity (%d) can not be greater than move quantity (%d)!') \
                    % (product.default_code, product.name, consumed_qty, move.product_qty))
        if move.state != 'assigned':
            if consumed_qty > move.quantity_out_available:
                raise osv.except_osv(_('Error!'), _('[%s]%s consume quantity (%d) can not be greater than available quantity (%d)!') \
                        % (product.default_code, product.name, consumed_qty, move.quantity_out_available))
            update_val['quantity_out_available'] = move.quantity_out_available - consumed_qty            
        return super(stock_move,self).action_cusume_partial_write_before(cr, uid, move, update_val, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
