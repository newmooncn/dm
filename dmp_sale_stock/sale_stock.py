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
import openerp.addons.decimal_precision as dp

class sale_order(osv.osv):
    _inherit = 'sale.order'

    def _picked_rate(self, cr, uid, ids, name, arg, context=None):
        if not ids:
            return {}
        res = {}
        tmp = {}
        for order_id in ids:
            tmp[order_id] = {'picked': 0.0, 'total': 0.0}
        #picked quantity
        cr.execute('''select b.sale_id, sum(case when b.type='out' then a.product_qty else -a.product_qty end) as picked_qty
                    from stock_move a
                    join stock_picking b on a.picking_id = b.id
                    where b.sale_id IN %s
                    and a.state = 'done'
                    group by b.sale_id''', (tuple(ids),))
        for item in cr.dictfetchall():
            tmp[item['sale_id']]['picked'] = item['picked_qty']
        #total quantity
        cr.execute('''select order_id, sum(product_uom_qty) as product_qty
                    from sale_order_line
                    where order_id IN %s
                    group by order_id''', (tuple(ids),))
        for item in cr.dictfetchall():
            tmp[item['order_id']]['total'] = item['product_qty']
        
        for order_id in ids:
            res[order_id] = tmp[order_id]['total'] and (100.0 * tmp[order_id]['picked'] / tmp[order_id]['total']) or 0.0
                
        return res

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    
    def _get_picking_info(self, cr, uid, ids, fields, args, context=None):
        result = {}
        for id in ids:
            result[id] = {'deliver_qty':0,'return_qty':0}
        for line in self.browse(cr,uid,ids,context=context):
            rec_qty = 0
            return_qty = 0
            if line.move_ids:
                #once there are moving, then can not change product, 06/07/2014 by johnw
                for move in line.move_ids:
                    if move.state == 'done':
                        if move.type == 'out':
                            rec_qty += move.product_qty
                        if move.type == 'in':
                            return_qty += move.product_qty
            result[line.id].update({'deliver_qty':rec_qty,
                                    'return_qty':return_qty,})
        return result
        
    _columns = { 
        'deliver_qty' : fields.function(_get_picking_info, type='float', digits_compute=dp.get_precision('Product UoS'), string='Delivered Quantity', multi="picking_info"),
        'return_qty' : fields.function(_get_picking_info, type='float', digits_compute=dp.get_precision('Product UoS'), string='Returned Quantity', multi="picking_info"),
        }
    _defaults={'deliver_qty':0, 'return_qty':0}