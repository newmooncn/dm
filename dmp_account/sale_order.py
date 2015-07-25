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

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        '''
        johnw, 
        07/20/2015, change the invoice partner to be same as sale order, do not use partner_invoice_id,
        07/24/2015, set new invoice.name to order.client_order_ref or order.name 
        since we need make the AP and accounting data to be one partner_id
        '''
        invoice_vals = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context=context)
        invoice_vals.update({'account_id': order.partner_id.property_account_receivable.id,
                            'partner_id': order.partner_id.id,
                            'name': order.client_order_ref or order.name,})
        return invoice_vals