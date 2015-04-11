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
from openerp.osv import fields,osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
          
class stock_picking(osv.osv):
    _inherit = "stock.picking" 

    def action_done(self, cr, uid, ids, context=None):
        """Changes picking state to done.
        
        This method is called at the end of the workflow by the activity "done".
        @return: True
        """
        po_obj = self.pool.get('purchase.order')
        for pick in self.browse(cr,uid,ids,context):
            if pick.purchase_id:
                #if this is a out, then check  the purchase return                
                if pick.type=='out':
                    if pick.purchase_id:
                        #if this is purchase return
                        #1.then set the related purchase order shipped to False
                        po_obj.write(cr,uid,[pick.purchase_id.id],{'shipped':False})
                        '''
                        remove the auto invoice generating, by johnw, 10/10/2014
                        '''
                        '''
                        #2.if need create invoices after picking, then auto generate the invoie
                        if pick.invoice_state == '2binvoiced':
                            inv_create_obj = self.pool.get("stock.invoice.onshipping")
                            if not context:
                                context = {}
                            context.update({'active_model':'stock.picking.out','active_ids':[pick.id],'active_id':pick.id})
                            journal_id = inv_create_obj._get_journal(cr,uid,context)
                            inv_create_id = inv_create_obj.create(cr,uid,{'journal_id':journal_id},context)
                            pick_inv_ids = inv_create_obj.create_invoice(cr,uid,[inv_create_id],context)
                        '''
                #if this is related to a PO and need to create invoices after picking, then auto generate the invoie and valid the invoice.
                if pick.type=='in' and pick.invoice_state == '2binvoiced':
                    '''
                    remove the auto invoice generating, by johnw, 10/09/2014, for the price chaning, 
                    need user to adjust price on stock_move, 
                    otherwise user change the price on invoice, 
                    then the move price will be wrong, then the FIFO price will be wrong
                    '''
                    '''
                    inv_create_obj = self.pool.get("stock.invoice.onshipping")
                    if not context:
                        context = {}
                    context.update({'active_model':'stock.picking.in','active_ids':[pick.id],'active_id':pick.id})
                    journal_id = inv_create_obj._get_journal(cr,uid,context)
                    inv_create_id = inv_create_obj.create(cr,uid,{'journal_id':journal_id},context)
                    pick_inv_ids = inv_create_obj.create_invoice(cr,uid,[inv_create_id],context)
                    invoice_ids = pick_inv_ids.values()
                    '''
                    '''
                    #remove the auto validate, need the accoutant to validate manually.
                    wf_service = netsvc.LocalService("workflow")
                    for invoice_id in invoice_ids:
                        wf_service.trg_validate(uid, 'account.invoice', invoice_id, 'invoice_open', cr)
                    '''   

        return super(stock_picking,self).action_done(cr,uid,ids,context)

    def _prepare_invoice_line(self, cr, uid, group, picking, move_line, invoice_id, invoice_vals, context=None):
        invoice_line_vals = super(stock_picking, self)._prepare_invoice_line(cr, uid, group, picking, move_line, invoice_id, invoice_vals, context=context)
        if invoice_vals['type'] in ('in_invoice', 'in_refund'):
            #check the 'property_stock_valuation_account_id' for the incoming stock, if it is true, then replace the invoice line account_id
            use_valuation_account = move_line.product_id.categ_id.prop_use_value_act_as_invoice
            if use_valuation_account:
                invoice_line_vals['account_id'] = move_line.product_id.categ_id.property_stock_valuation_account_id.id
        return invoice_line_vals
    
class product_category(osv.osv):
    _inherit = 'product.category'
    _columns = {
        #use valuation account as invoice account
        #使用存货科目作为生成凭据明细的会计科目,也就是凭据确认时应付账款的对方科目
        'prop_use_value_act_as_invoice': fields.property(None,
            type='boolean',
            string="Use valuation as invoice",
            view_load=True,
            help="Use Stock Valuation Account as the invoice counterpart account to the payable."),
    }    

product_category()
