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
from openerp.osv import osv
from openerp.tools.translate import _
from openerp.tools import float_compare

class stock_move(osv.osv):
    _inherit = "stock.move" 

    def action_consume_done_before(self, cr, uid, ids, context=None):
        '''
        called by action_consume before do the action done
        @return: True - can done; False - do not done
        '''
        return True
    
'''
johnw, 04/26/2015, add hook on action_consume

will be used for the mrp production(mo.action_produce()) to produce a product
generated one new move but not finish it automatically.
'''    
from openerp.addons.stock.stock import stock_move as stock_move_patch
def action_consume_hook(self, cr, uid, ids, quantity, location_id=False, context=None):
    """ Consumed product with specific quatity from specific source location
    @param cr: the database cursor
    @param uid: the user id
    @param ids: ids of stock move object to be consumed
    @param quantity : specify consume quantity
    @param location_id : specify source location
    @param context: context arguments
    @return: Consumed lines
    """
    #quantity should in MOVE UOM
    if context is None:
        context = {}
    if quantity <= 0:
        raise osv.except_osv(_('Warning!'), _('Please provide proper quantity.'))
    res = []
    for move in self.browse(cr, uid, ids, context=context):
        move_qty = move.product_qty
        if move_qty <= 0:
            raise osv.except_osv(_('Error!'), _('Cannot consume a move with negative or zero quantity.'))
        quantity_rest = move.product_qty
        quantity_rest -= quantity
        uos_qty_rest = quantity_rest / move_qty * move.product_uos_qty
        if quantity_rest <= 0:
            quantity_rest = 0
            uos_qty_rest = 0
            quantity = move.product_qty

        uos_qty = quantity / move_qty * move.product_uos_qty
        if float_compare(quantity_rest, 0, precision_rounding=move.product_id.uom_id.rounding):
            default_val = {
                'product_qty': quantity,
                'product_uos_qty': uos_qty,
                'state': move.state,
                'location_id': location_id or move.location_id.id,
            }
            current_move = self.copy(cr, uid, move.id, default_val)
            res += [current_move]
            update_val = {}
            update_val['product_qty'] = quantity_rest
            update_val['product_uos_qty'] = uos_qty_rest
            self.write(cr, uid, [move.id], update_val)

        else:
            quantity_rest = quantity
            uos_qty_rest =  uos_qty
            res += [move.id]
            update_val = {
                    'product_qty' : quantity_rest,
                    'product_uos_qty' : uos_qty_rest,
                    'location_id': location_id or move.location_id.id,
            }
            self.write(cr, uid, [move.id], update_val)
    #johnw, 04/26/2015, add before book for the move done
    #self.action_done(cr, uid, res, context=context)    
    if self.action_consume_done_before(cr, uid, res, context=None):
        self.action_done(cr, uid, res, context=context)

    return res    

stock_move_patch.action_consume = action_consume_hook   