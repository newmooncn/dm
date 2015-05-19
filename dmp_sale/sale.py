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
from osv import fields,osv,orm
from openerp import netsvc
from openerp.addons.dm_base.utils import set_seq_o2m
import openerp.addons.decimal_precision as dp

class sale_order(osv.osv):
    _inherit="sale.order"
    _order = 'id desc'
#    _columns = {
#        'minimum_planned_date':fields.function(_minimum_planned_date, fnct_inv=_set_minimum_planned_date, string='Expected Date', type='date', select=True, help="This is computed as the minimum scheduled date of all purchase order lines' products.",
#            store = {
#                'purchase.order.line': (_get_order, ['date_planned'], 10),
#            }
#        ),           
#    }  
       
    def default_get(self, cr, uid, fields, context=None):
        vals = super(sale_order, self).default_get(cr, uid, fields, context=context)
        vals['company_id'] = company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        return vals

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        resu = super(sale_order,self).onchange_partner_id(cr, uid, ids, part, context)
        if not part:
            return resu

        part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        #if the chosen partner is not a company and has a parent company, use the parent to choose the delivery, the 
        #invoicing addresses and all the fields related to the partner.
        if part.parent_id and not part.is_company:
            part = part.parent_id
        if part.country_id and part.country_id.currency_id:
            pricelist_obj = self.pool.get('product.pricelist')
            pricelist_ids = pricelist_obj.search(cr, uid, [('currency_id', '=', part.country_id.currency_id.id)], context=context)
            if pricelist_ids:
                resu['value']['pricelist_id'] = pricelist_ids[0]  
        return resu
            
    def get_report_name(self, cr, uid, id, rpt_name, context=None):
        state = self.pool.get('sale.order').read(cr, uid, id, ['state'],context=context)['state']
        if state == 'draft' or state == 'sent':
            return "Quote"
        else:
            return "SalesOrder"
           
    def create(self, cr, uid, data, context=None):        
        set_seq_o2m(cr, uid, data.get('order_line'), context=context)
        return super(sale_order, self).create(cr, uid, data, context)
        
    def write(self, cr, uid, ids, vals, context=None):      
        if not isinstance(ids,list):
            ids = [ids]
        set_seq_o2m(cr, uid, vals.get('order_line'), 'sale_order_line', 'order_id', ids[0], context=context)  
        return super(sale_order, self).write(cr, uid, ids, vals, context=context)

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    _columns = {        
        'date_planned': fields.date('Scheduled Date', required=True, select=True),
    }        
    
    def name_get(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not len(ids):
            return []
        result = []
        for line in self.browse(cr, user, ids, context=context):
            result.append((line.id, '%s@%s'%(line.name, line.order_id.name)))
        return result