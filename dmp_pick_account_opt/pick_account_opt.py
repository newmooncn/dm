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

class sale_order(osv.osv):
    _inherit="sale.order"

    def procurement_needed(self, cr, uid, ids, context=None):
        #when sale is installed only, there is no need to create procurements, that's only
        #further installed modules (sale_service, sale_stock) that will change this.
        sale_line_obj = self.pool.get('sale.order.line')
        res = []
        for order in self.browse(cr, uid, ids, context=context):
            #if accounting only then do not generate picking, johnw, 07/21/2015
            if order.pick_account_opt == 'account':
                continue
            res.append(sale_line_obj.need_procurement(cr, uid, [line.id for line in order.order_line if line.state != 'cancel'], context=context))
        return any(res)
    
    _columns = {
        'pick_account_opt': fields.selection([
            ('all', 'All'),
            ('pick', 'Picking Only'),
            ('account', 'Accounting Only')], 
            'Picking/Accounting'),                  
    }  
    
class purchase_order(osv.osv):
    _inherit="purchase.order"
    
    def has_stockable_product(self, cr, uid, ids, *args):
        for order in self.browse(cr, uid, ids):
            #if accounting only then do not generate picking, johnw, 07/21/2015
            if order.pick_account_opt == 'account':
                #if accounting only then do not generate picking
                continue
            for order_line in order.order_line:
                if order_line.state == 'cancel':
                    continue
                if order_line.product_id and order_line.product_id.type in ('product', 'consu'):
                    return True
        return False
    
    _columns = {
        'pick_account_opt': fields.selection([
            ('all', 'All'),
            ('pick', 'Picking Only'),
            ('account', 'Accounting Only')], 
            'Picking/Accounting'),                  
    }      