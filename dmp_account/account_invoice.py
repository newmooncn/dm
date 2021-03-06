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


from openerp.osv import fields, osv, orm
from openerp.addons.account.account_invoice import account_invoice as account_invoice_super
import openerp.exceptions

def account_invoice_unlink(self, cr, uid, ids, context=None):
	if context is None:
		context = {}
	invoices = self.read(cr, uid, ids, ['state','internal_number'], context=context)
	unlink_ids = []

	for t in invoices:
		if t['state'] not in ('draft', 'cancel'):
			raise openerp.exceptions.Warning(_('You cannot delete an invoice which is not draft or cancelled. You should refund it instead.'))
		#allow to cancel invoice that have been validated, johnw, 07/24/2015
#		elif t['internal_number']:
#			raise openerp.exceptions.Warning(_('You cannot delete an invoice after it has been validated (and received a number).  You can set it back to "Draft" state and modify its content, then re-confirm it.'))
		else:
			unlink_ids.append(t['id'])

	osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
	return True
	
account_invoice_super.unlink = 	account_invoice_unlink