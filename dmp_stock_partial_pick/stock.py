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
from openerp import netsvc
from openerp.osv import fields,osv
import openerp.addons.decimal_precision as dp
          
class stock_move(osv.osv):
    _inherit = "stock.move" 
        
    _columns = {   
        'quantity_out_available' : fields.float("Avail Quantity", digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'quantity_out_missing' : fields.float("Missing Quantity", digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
    } 
                   
    '''
    Improve the product reserve logic, to update the quantity_out_available and quantity_out_missing
    '''
    def check_assign(self, cr, uid, ids, context=None):
        """ Checks the product type and accordingly writes the state.
        @return: No. of moves done
        """
        done = []
        count = 0
        pickings = {}
        if context is None:
            context = {}
        for move in self.browse(cr, uid, ids, context=context):
            if move.product_id.type == 'consu' or move.location_id.usage == 'supplier':
                if move.state in ('confirmed', 'waiting'):
                    #johnw, for the move from consu or supplier, update the quantity_out_available direct
                    self.write(cr, uid, [move.id], {'quantity_out_available':move.product_qty, 'quantity_out_missing':0})
                    done.append(move.id)
                pickings[move.picking_id.id] = 1
                continue
            if move.state in ('confirmed', 'waiting'):
                # Important: we must pass lock=True to _product_reserve() to avoid race conditions and double reservations
                #johnw, 04/25/2014, Improve the product reserve logic, to update the quantity_out_available and quantity_out_missing
                #res = self.pool.get('stock.location')._product_reserve(cr, uid, [move.location_id.id], move.product_id.id, move.product_qty, {'uom': move.product_uom.id}, lock=True)
                #if res:
                res, qty_missing, total_avail = self.pool.get('stock.location')._product_out_avail(cr, uid, [move.location_id.id], move.product_id.id, move.product_qty, {'uom': move.product_uom.id}, lock=True)
                if total_avail < 0:
                    total_avail = 0
                if move.type == 'in':
                    total_avail = move.product_qty
                self.write(cr, uid, [move.id], {'quantity_out_available':total_avail, 'quantity_out_missing':move.product_qty-min(total_avail,move.product_qty)})
                if qty_missing <= 0:
                    #_product_available_test depends on the next status for correct functioning
                    #the test does not work correctly if the same product occurs multiple times
                    #in the same order. This is e.g. the case when using the button 'split in two' of
                    #the stock outgoing form
                    self.write(cr, uid, [move.id], {'state':'assigned'})
                    done.append(move.id)
                    pickings[move.picking_id.id] = 1
                    r = res.pop(0)
                    product_uos_qty = self.pool.get('stock.move').onchange_quantity(cr, uid, [move.id], move.product_id.id, r[0], move.product_id.uom_id.id, move.product_id.uos_id.id)['value']['product_uos_qty']
                    cr.execute('update stock_move set location_id=%s, product_qty=%s, product_uos_qty=%s where id=%s', (r[1], r[0],product_uos_qty, move.id))

                    while res:
                        r = res.pop(0)
                        product_uos_qty = self.pool.get('stock.move').onchange_quantity(cr, uid, [move.id], move.product_id.id, r[0], move.product_id.uom_id.id, move.product_id.uos_id.id)['value']['product_uos_qty']
                        move_id = self.copy(cr, uid, move.id, {'product_uos_qty': product_uos_qty, 'product_qty': r[0], 'location_id': r[1]})
                        done.append(move_id)
                else:
                    count += 1
                    pickings[move.picking_id.id] = 1                    
                    
        if done:
            count += len(done)
            self.write(cr, uid, done, {'state': 'assigned'})

        if count:
            for pick_id in pickings:
                wf_service = netsvc.LocalService("workflow")
                wf_service.trg_write(uid, 'stock.picking', pick_id, cr)
        return count
          
class stock_picking(osv.osv):
    _inherit = "stock.picking" 
    def _partial_assigned(self, cr, uid, ids, field_names, arg, context=None):
        if not ids: return {}
        res = {}
        for pick in self.browse(cr, uid, ids, context=context):
            res[pick.id] = False
            if pick.state not in('confirmed', 'assigned'):
                continue
            for move in pick.move_lines:
                if move.state == 'confirmed':
                    res[pick.id] = True
                    break
        return res
    _columns = {   
        'partial_assigned' : fields.function(_partial_assigned, string="Partial Assigned", type = "boolean", readonly=True),
    }   
    '''
    Improve confirmed-->assigned logic, if the move is partial available(quantity_out_available>0), also make the picking state to assigned
    '''                         
    def test_assigned(self, cr, uid, ids):
        """ Tests whether the move is in assigned state or not.
        @return: True or False
        """
        #TOFIX: assignment of move lines should be call before testing assigment otherwise picking never gone in assign state
        ok = True
        for pick in self.browse(cr, uid, ids):
            mt = pick.move_type
            # incoming shipments are always set as available if they aren't chained
            if pick.type == 'in':
                if all([x.state != 'waiting' for x in pick.move_lines]):
                    return True
            for move in pick.move_lines:
                if (move.state in ('confirmed', 'draft')) and (mt == 'one'):
                    return False
                #Improve confirmed-->assigned logic, if the move is partial available(quantity_out_available>0), also make the picking state to assigned
                #if (mt == 'direct') and (move.state == 'assigned') and (move.product_qty):
                if (mt == 'direct') and(\
                    (move.state == 'assigned' and move.product_qty)\
                    or (move.state == 'confirmed' and move.product_qty and move.quantity_out_available)):
                    return True
                ok = ok and (move.state in ('cancel', 'done', 'assigned'))
        return ok
    
class stock_picking_out(osv.osv):
    _inherit = "stock.picking.out"  
    _columns = {   
        'partial_assigned' : fields.function(stock_picking._partial_assigned, string="Partial Assigned", type = "boolean", readonly=True),
    }  