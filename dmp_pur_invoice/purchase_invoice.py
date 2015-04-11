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
    
    def _invoiced_rate(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for purchase in self.browse(cursor, user, ids, context=context):
            tot = 0.0
            for invoice in purchase.invoice_ids:
                if invoice.state not in ('draft','cancel'):
                    tot += invoice.amount_total
            if purchase.amount_total:
                res[purchase.id] = tot * 100.0 / purchase.amount_total
            else:
                res[purchase.id] = 0.0
        return res 
            
    _columns = {
        'invoiced': fields.function(purchase.purchase_order._invoiced, string='Invoice Received', type='boolean', help="It indicates that an invoice is open"),
        'invoiced_rate': fields.function(_invoiced_rate, string='Invoiced', type='float'),
    }
    
    def _get_inv_pay_acc_id(self,cr,uid,order):
        property_obj = self.pool.get('ir.property')
        pay_acc = property_obj.get(cr, uid, 'property_account_payable', 'res.partner', 
                                      res_id = 'res.partner,%d'%order.partner_id.id, context = {'force_company':order.company_id.id})
        if not pay_acc:
            pay_acc = property_obj.get(cr, uid, 'property_account_payable', 'res.partner', context = {'force_company':order.company_id.id})
        if not pay_acc:
            raise osv.except_osv(_('Error!'), 
                _('Define account payable for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))
        return pay_acc.id
                            
    def _get_inv_line_exp_acc_id(self,cr,uid,order,po_line):  
        property_obj = self.pool.get('ir.property')
        acc = None
        if po_line.product_id:
            acc = po_line.product_id.property_account_expense or  po_line.product_id.categ_id.property_account_expense_categ
#        if po_line.product_id:
#            acc = property_obj.get(cr, uid, 'property_account_expense', 'product.template', 
#                              res_id = 'product.template,%d'%po_line.product_id.id, context = {'force_company':order.company_id.id})
#            if not acc:
#                acc = property_obj.get(cr, uid, 'property_account_expense_categ', 'product.category', 
#                                  res_id = 'product.category,%d'%po_line.product_id.categ_id.id, context = {'force_company':order.company_id.id})
        if not acc:
            acc = property_obj.get(cr, uid, 'property_account_expense', 'product.template', 
                              context = {'force_company':order.company_id.id})                                
        if not acc:
            acc = property_obj.get(cr, uid, 'property_account_expense_categ', 'product.category', 
                                   context = {'force_company':order.company_id.id})
            
        #check the 'property_stock_valuation_account_id', if it is true, then replace the invoice line account_id, by johnw, 10/08/2014
        use_valuation_account = po_line.product_id.type == 'product' and po_line.product_id.categ_id.prop_use_value_act_as_invoice
        if use_valuation_account:
            acc = po_line.product_id.categ_id.property_stock_valuation_account_id
        
        if not acc:
                raise osv.except_osv(_('Error!'),
                        _('Define purchase journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))
        return acc.id
                                                        
    def action_invoice_create(self, cr, uid, ids, context=None):
        """Generates invoice for given ids of purchase orders and links that invoice ID to purchase order.
        :param ids: list of ids of purchase orders.
        :return: ID of created invoice.
        :rtype: int
        """
        res = False

        journal_obj = self.pool.get('account.journal')
        inv_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')
        fiscal_obj = self.pool.get('account.fiscal.position')

        for order in self.browse(cr, uid, ids, context=context):
#            pay_acc_id = order.partner_id.property_account_payable.id
            #use a new method to get the account_id
            pay_acc_id = self._get_inv_pay_acc_id(cr,uid,order)                
            journal_ids = journal_obj.search(cr, uid, [('type', '=','purchase'),('company_id', '=', order.company_id.id)], limit=1)
            if not journal_ids:
                raise osv.except_osv(_('Error!'),
                    _('Define purchase journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))

            # generate invoice line correspond to PO line and link that to created invoice (inv_id) and PO line
            inv_lines = []
            for po_line in order.order_line:
                #check if this line have quantity to generate invoice, by johnw
                if po_line.product_qty <= po_line.invoice_qty:
                    continue                
#                if po_line.product_id:
#                    acc_id = po_line.product_id.property_account_expense.id
#                    if not acc_id:
#                        acc_id = po_line.product_id.categ_id.property_account_expense_categ.id
#                    if not acc_id:
#                        raise osv.except_osv(_('Error!'), _('Define expense account for this company: "%s" (id:%d).') % (po_line.product_id.name, po_line.product_id.id,))
#                else:
#                    acc_id = property_obj.get(cr, uid, 'property_account_expense_categ', 'product.category').id      
                #use a new method to get the account_id, by johnw          
                acc_id = self._get_inv_line_exp_acc_id(cr,uid,order,po_line)
                fpos = order.fiscal_position or False
                acc_id = fiscal_obj.map_account(cr, uid, fpos, acc_id)

                inv_line_data = self._prepare_inv_line(cr, uid, acc_id, po_line, context=context)
                #update the quantity to the quantity, by johnw
                inv_line_data.update({'quantity':(po_line.product_qty - po_line.invoice_qty)})
                inv_line_id = inv_line_obj.create(cr, uid, inv_line_data, context=context)
                inv_lines.append(inv_line_id)

                po_line.write({'invoiced':True, 'invoice_lines': [(4, inv_line_id)]}, context=context)
            
            #if no lines then return direct, by johnw
            if len(inv_lines) == 0:
                continue
            
            # get invoice data and create invoice
            inv_data = {
                'name': order.partner_ref or order.name,
                'reference': order.partner_ref or order.name,
                'account_id': pay_acc_id,
                'type': 'in_invoice',
                'partner_id': order.partner_id.id,
                'currency_id': order.pricelist_id.currency_id.id,
                'journal_id': len(journal_ids) and journal_ids[0] or False,
                'invoice_line': [(6, 0, inv_lines)],
                'origin': order.name,
                'fiscal_position': order.fiscal_position.id or False,
                'payment_term': order.payment_term_id.id or False,
                'company_id': order.company_id.id,
            }
            inv_id = inv_obj.create(cr, uid, inv_data, context=context)

            # compute the invoice
            inv_obj.button_compute(cr, uid, [inv_id], context=context, set_total=True)

            # Link this new invoice to related purchase order
            order.write({'invoice_ids': [(4, inv_id)]}, context=context)
            res = inv_id
        return res   
    
class purchase_order_line(osv.osv):  
    _name = "purchase.order.line"
    _inherit = 'purchase.order.line' 

    def _get_invoice_info(self, cr, uid, ids, fields, args, context=None):
        result = {}
        for id in ids:
            result[id] = {'invoice_qty':0}
        for line in self.browse(cr,uid,ids,context=context):
            invoice_qty = 0
            if line.invoice_lines:
                for inv_line in line.invoice_lines:
                    if inv_line.invoice_id.state != 'cancel':
                        invoice_qty += inv_line.quantity
            result[line.id].update({'invoice_qty':invoice_qty,})
        return result
    
    _columns = {
        'invoice_qty' : fields.function(_get_invoice_info, type='float', digits_compute=dp.get_precision('Product Unit of Measure'), string='Invoice Quantity', multi="invoice_info"),
    }      