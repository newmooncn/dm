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
from openerp.osv import fields,osv,orm
import openerp.addons.decimal_precision as dp

class sale_order(osv.osv):
    _inherit="sale.order"    
        
    def _get_amount(self, cr, uid, ids, field_names, args, context=None):
        """ Finds the payment mount and set the paid flag
        @return: Dictionary of values
        """
        if not field_names:
            field_names = []
        if context is None:
            context = {}
        res = {}
        for id in ids:
            res[id] = {}.fromkeys(field_names)

        for order in self.browse(cr, uid, ids, context=context):
            pre_paid = 0.0
            inv_paid = 0.0
            #check the prepaymenys
            for line in order.payment_ids:    
                if not line.reconcile_id:
                    if not line.reconcile_partial_id:
                        if line.currency_id:
                            pre_paid += abs(line.amount_residual_currency)
                        else:
                            pre_paid += line.amount_residual                        
                    else:
                        #if move is partial reconciled, then only the amount_residual is negative then this line is also need more lines to reconcile it
                        if line.amount_residual > 0:
                            if line.currency_id:
                                pre_paid += abs(line.amount_residual_currency)
                            else:
                                pre_paid += line.amount_residual
                
            #check the invoice paid            
            for invoice in order.invoice_ids:
                if invoice.state not in ('draft','cancel'):
                    if invoice.type == 'in_refund':
                        inv_paid -= (invoice.amount_total - invoice.residual)
                    else:                        
                        inv_paid += (invoice.amount_total - invoice.residual)
               
            res[order.id] = {
                    'amount_paid': inv_paid + pre_paid, 
                    'residual': order.amount_total - inv_paid - pre_paid
                    }
        return res

    def _inv_pay_ids(self, cr, uid, ids, field_names=None, arg=False, context=None):
        """ Finds the payment list by invoice
        @return: Dictionary of values
        """
        if not field_names:
            field_names = []
        if context is None:
            context = {}
        res = {}
        for id in ids:
            res[id] = {}.fromkeys(field_names)

        for order in self.browse(cr, uid, ids, context=context):
            #check the invoice paid  
            inv_pay_ids = []          
            for invoice in order.invoice_ids:
                if invoice.state not in ('draft','cancel'):
                    inv_pay_ids.extend(map(lambda x: x.id, invoice.payment_ids))
            res[order.id] = inv_pay_ids
        return res
    
    _columns={
        #links to account_move        
        'payment_moves': fields.many2many('account.move', string='Payment Moves', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'agreed': [('readonly', False)]}),
        #redefine the columns in sale_payment_method/sale.py
        'residual': fields.function(
            _get_amount,
            digits_compute=dp.get_precision('Account'),
            string='Balance',
            store=False,
            multi='payment'),
        'amount_paid': fields.function(
            _get_amount,
            digits_compute=dp.get_precision('Account'),
            string='Amount Paid',
            store=False,
            multi='payment'),
        #new field include the invoice payment move lines         
        'inv_pay_ids': fields.function(_inv_pay_ids,relation='account.move.line', type='many2many', string='Invoice Payments'),
    }

    #from the sale_payment_method.sale.py, add the sale_id
    def _prepare_payment_move(self, cr, uid, move_name, sale, journal,
                              period, date, description, context=None):
        resu = super(sale_order,self)._prepare_payment_move(cr,uid,move_name,sale,journal,period,date,description,context)
        resu.update({'sale_ids':[(4, sale.id)]})
        return resu
    
    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default['payment_moves'] = False
        return super(sale_order, self).copy(cr, uid, id, default, context=context)

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        '''
        johnw, 07/20/2015, change the invoice partner to be same as sale order, do not use partner_invoice_id, 
        since we need make the AP and accounting data to be one partner_id
        '''
        invoice_vals = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context=context)
        invoice_vals.update({'partner_id': order.partner_id.id,})
        return invoice_vals
        
class account_move(osv.osv):
    _inherit="account.move"
    _columns = {
        'sale_ids': fields.many2many('sale.order', string='Sales Orders'),
    }       
    def unlink(self, cr, uid, ids, context=None, check=True):
        #if the move's line generated by the sales payment, then cancel this entry firstly
        moves = self.browse(cr,uid,ids,context)
        for move in moves:
            if move.state == 'posted' and move.sale_ids:
                self.button_cancel(cr,uid,[move.id],context=context)
        #execute the delete action
        result = super(account_move, self).unlink(cr, uid, ids, context=context)
        return result
    
class pay_sale_order(orm.TransientModel):
    _inherit = 'pay.sale.order'       
    _columns = {
        'amount_max': fields.float('Max Amount'),
    }
    def _get_amount(self, cr, uid, context=None):
        if context is None:
            context = {}
        if context.get('active_id'):
            sale_obj = self.pool.get('sale.order')
            order = sale_obj.browse(cr, uid, context['active_id'],
                                    context=context)
            return order.residual
        return False    
    _defaults = {
        'amount': 0,
        'amount_max':_get_amount,
    }    
    def _check_amount(self, cr, uid, ids, context=None):
        for pay in self.browse(cr, uid, ids, context=context):
            if pay.amount <= 0 or pay.amount > pay.amount_max:
                return False
        return True
    _constraints = [(_check_amount, 'Pay amount only can be between zero and the balance.', ['amount'])]
        