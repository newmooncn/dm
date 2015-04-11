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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from openerp.osv import fields,osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.addons.purchase import purchase
class purchase_order(osv.osv):  
    _inherit = "purchase.order"
        
    def _create_pickings(self, cr, uid, order, order_lines, picking_id=False, context=None):
        if not picking_id:
            picking_id = self.pool.get('stock.picking').create(cr, uid, self._prepare_order_picking(cr, uid, order, context=context))
        todo_moves = []
        stock_move = self.pool.get('stock.move')
        wf_service = netsvc.LocalService("workflow")
        for order_line in order_lines:
            if not order_line.product_id:
                continue
#            if order_line.product_id.type in ('product', 'consu'):
            move_qty = order_line.product_qty
            if order_line.move_ids:
                #get all the valid move picking quantity of this purchase order line
                for move in order_line.move_ids:
                    if move.state != 'cancel':
                        if move.type == 'in':
                            move_qty -= move.product_qty
                        if move.type == 'out':
                            move_qty += move.product_qty
            if order_line.product_id.type in ('product', 'consu') and move_qty > 0:
                order_line.product_qty = move_qty 
                move = stock_move.create(cr, uid, self._prepare_order_line_move(cr, uid, order, order_line, picking_id, context=context))
                if order_line.move_dest_id:
                    order_line.move_dest_id.write({'location_id': order.location_id.id})
                todo_moves.append(move)
        if len(todo_moves) > 0:
            stock_move.action_confirm(cr, uid, todo_moves)
            stock_move.force_assign(cr, uid, todo_moves)
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
            return [picking_id]
        else:
            self.pool.get('stock.picking').unlink(cr,uid,[picking_id],context)
            return []
        
    def view_picking(self, cr, uid, ids, context=None):
        #create the picking for unshipped orders
        for po in self.read(cr,uid,ids,['shipped']):
            if not po['shipped']:
                self.action_picking_create(cr,uid,ids,context) 
        return super(purchase_order,self).view_picking(cr, uid, ids, context)   
    
class purchase_order_line(osv.osv):  
    _name = "purchase.order.line"
    _inherit = 'purchase.order.line' 

    def _get_picking_info(self, cr, uid, ids, fields, args, context=None):
        result = {}
        for id in ids:
            result[id] = {'receive_qty':0,'return_qty':0}
        for line in self.browse(cr,uid,ids,context=context):
            rec_qty = 0
            return_qty = 0
            if line.move_ids:
                #once there are moving, then can not change product, 06/07/2014 by johnw
                for move in line.move_ids:
                    if move.state == 'done':
                        if move.type == 'in':
                            rec_qty += move.product_qty
                        if move.type == 'out':
                            return_qty += move.product_qty
            result[line.id].update({'receive_qty':rec_qty,
                                    'return_qty':return_qty,})
        return result
    
    _columns = {
        'receive_qty' : fields.function(_get_picking_info, type='float', digits_compute=dp.get_precision('Product Unit of Measure'), string='Received Quantity', multi="picking_info"),
        'return_qty' : fields.function(_get_picking_info, type='float', digits_compute=dp.get_precision('Product Unit of Measure'), string='Returned Quantity', multi="picking_info"),
    }            
    _defaults = {
        'receive_qty': 0,
        'return_qty': 0,
    }                 