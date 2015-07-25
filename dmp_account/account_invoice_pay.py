# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP S.A. <http://www.openerp.com>
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

'''
Add account_voucher.invoice_id and auto set it when do payment on the invoice
Add account_move.invoice_id for the voucher payment, and auto set it from account_voucher.invoice_id
'''
class account_move(osv.osv):
    _inherit = "account.move"        
    _columns={
        'invoice_id': fields.many2one('account.invoice', 'Invoice', readonly=True)
    }
        
class account_voucher(osv.osv):
    _inherit = "account.voucher"        
    _columns={
        'invoice_id': fields.many2one('account.invoice', 'Invoice', readonly=True)
    }
    def account_move_get(self, cr, uid, voucher_id, context=None):
        resu = super(account_voucher,self).account_move_get(cr, uid, voucher_id, context=context)
        voucher = self.browse(cr,uid,voucher_id,context=context)
        if voucher.invoice_id:
            resu['invoice_id'] = voucher.invoice_id.id
        return resu 
        
class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    def invoice_pay_customer(self, cr, uid, ids, context=None):
        resu = super(account_invoice,self).invoice_pay_customer(cr, uid, ids, context=context)
        resu['context']['default_invoice_id'] = resu['context']['invoice_id']
        return resu