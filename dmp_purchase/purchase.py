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
    def __init__(self, pool, cr):
        super(purchase_order,self).__init__(pool,cr)
    _track = {
        'state': {
            'purchase.mt_rfq_confirmed': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'confirmed',
            'purchase.mt_rfq_approved': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'approved',
            'dmp_purchase.mt_rfq_rejected': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'rejected',
        },
    }

    STATE_SELECTION = [
        ('draft', 'Draft PO'),
        ('sent', 'RFQ Sent'),
        ('confirmed', 'Waiting Approval'),
        ('rejected', 'Rejected'),
        ('approved', 'Purchase Order'),
        ('changing', 'In Changing'),
        ('changing_confirmed', 'Changing Waiting Approval'),
        ('changing_rejected', 'Changing Rejected'),
        ('except_picking', 'Shipping Exception'),
        ('except_invoice', 'Invoice Exception'),
        ('wait_receipt', 'Waitting Receipt'),
        ('done', 'Done'),
        ('done_except', 'Done with Exception'),
        ('cancel', 'Cancelled'),
        ('cancel_except', 'Cancelled with Exception')
    ] 
    
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

    def _change_log_line(self, cr, uid, ids, field_names=None, arg=False, context=None):
        """ Finds the line change log
        @return: Dictionary of values
        """
        if not field_names:
            field_names = []
        if context is None:
            context = {}
        res = {}
        for id in ids:
            res[id] = {}.fromkeys(field_names)

        for purchase in self.browse(cr, uid, ids, context=context):
            #check the invoice paid  
            change_log_ids = []          
            for line in purchase.order_line:
                change_log_ids.extend([change_log.id for change_log in line.change_log])
            res[purchase.id] = change_log_ids
        return res
            
    _columns = {
        'warehouse_id': fields.many2one('stock.warehouse', 'Destination Warehouse',states={'confirmed':[('readonly',True)],'approved':[('readonly',True)],'done':[('readonly',True)]}),            
        'state': fields.selection(STATE_SELECTION, 'Status', readonly=True, help="The status of the purchase order or the quotation request. A quotation is a purchase order in a 'Draft' status. Then the order has to be confirmed by the user, the status switch to 'Confirmed'. Then the supplier must confirm the order to change the status to 'Approved'. When the purchase order is paid and received, the status becomes 'Done'. If a cancel action occurs in the invoice or in the reception of goods, the status becomes in exception.", select=True),
        'reject_msg': fields.text('Rejection Message', track_visibility='onchange'),
        'create_uid':  fields.many2one('res.users', 'Creator', readonly=True),
        'create_date': fields.datetime('Creation Date', readonly=True, select=True),
        'inform_type': fields.char('Informer Type', size=10, readonly=True, select=True),
        'is_sent_supplier': fields.boolean('Sent to Supplier', select=True),
        'taxes_id': fields.many2many('account.tax', 'po_tax', 'po_id', 'tax_id', 'Taxes', states={'confirmed':[('readonly',True)],'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'invoiced': fields.function(purchase.purchase_order._invoiced, string='Invoice Received', type='boolean', help="It indicates that an invoice is open"),
        'invoiced_rate': fields.function(_invoiced_rate, string='Invoiced', type='float'),
        'has_freight': fields.boolean('Has Freight', states={'confirmed':[('readonly',True)],'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'amount_freight': fields.float('Freight', states={'confirmed':[('readonly',True)],'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'receipt_number': fields.char('Receipt Number', size=64, help="The reference of this invoice as provided by the partner."),
        'comments': fields.text('Comments'),       
#        'change_log_line': fields.function(_change_log_line, type='one2many', relation='change.log.po.line', string='Line Changing'),
        'change_log_line': fields.one2many('change.log.po.line','po_id','Line Changing Log', readonly=True),  
        #partner bank info
        'bank_name': fields.related('partner_id', 'bank_name', type='char', string='Bank Name'),
        'bank_account': fields.related('partner_id', 'bank_account', type='char', string='Bank Account Name'),
    }
    _defaults = {
        'is_sent_supplier': False,
    }    
    def _check_duplicated_products(self, cr, uid, ids, context=None):
        for po in self.browse(cr, uid, ids, context=context):
            if po.state in('done','approved', 'wait_receipt'):
                continue
            products = {}
            for line in po.order_line:
                product = line.product_id
                product_id = product.id
                if product_id not in products:
                    products[product_id] = 1
                else:
#                    products[product_id] = products[product_id] + 1
                    raise osv.except_osv(_('Error!'), _('[%s]%s is duplicated in this order!')%(product.default_code,product.name))
        return True 
    _constraints = [
        (_check_duplicated_products, 'Error ! You can not add duplicated products!', ['order_line'])
    ]    
    def new_po(self, cr, uid, pos, context=None):
        """
        Create New RFQ for Supplier
        """
        if context is None:
            context = {}
        purchase_order = self.pool.get('purchase.order')
        purchase_order_line = self.pool.get('purchase.order.line')
        res_partner = self.pool.get('res.partner')
        fiscal_position = self.pool.get('account.fiscal.position')
        warehouse_obj = self.pool.get('stock.warehouse')
        product_obj = self.pool.get('product.product')
        pricelist_obj = self.pool.get('product.pricelist')
        for po_data in pos:
            assert po_data['partner_id'], 'Supplier should be specified'
            assert po_data['warehouse_id'], 'Warehouse should be specified'            
            supplier = res_partner.browse(cr, uid, po_data['partner_id'], context=context)
            warehouse = warehouse_obj.browse(cr, uid, po_data['warehouse_id'], context=context)
            
            if not po_data.has_key('location_id'):
                po_data['location_id'] = warehouse.lot_input_id.id
            if not po_data.has_key('pricelist_id'):
                supplier_pricelist = supplier.property_product_pricelist_purchase or False
                po_data['pricelist_id'] = supplier_pricelist.id
            if not po_data.has_key('fiscal_position'):
                po_data['fiscal_position'] = supplier.property_account_position and supplier.property_account_position.id or False
            if not po_data.has_key('company_id'):
                company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'purchase.order', context=context)
                po_data['company_id'] = company_id
            #add the default value of notes
            po_data.update(purchase_order.default_get(cr,uid,['notes'],context=context))
            new_po_id = purchase_order.create(cr, uid, po_data)
            #assign the new po id to po data, then the caller call get the new po's info
            po_data['new_po_id'] = new_po_id
            pricelist_id = po_data['pricelist_id'];
            for line in po_data['lines']:
                product = product_obj.browse(cr,uid, line['product_id'], context=context)
                #taxes
                taxes_ids = product.supplier_taxes_id
                taxes = fiscal_position.map_tax(cr, uid, supplier.property_account_position, taxes_ids)
                taxes_id = [(6, 0, taxes)]
                
                line.update({'order_id':new_po_id,'taxes_id':taxes_id})
                
                #set the line description
                name = product.name
                if product.description_purchase:
                    name += '\n' + product.description_purchase
                if line.get('name'):
                    name += '\n' + line.get('name')      
                line.update({'name': name})    
                       
                #unit price
                if not line.has_key('price_unit'):
                    price_unit = seller_price = pricelist_obj.price_get(cr, uid, [pricelist_id], product.id, line['product_qty'], False, {'uom': line['product_uom']})[pricelist_id]
                    line['price_unit'] = price_unit
                new_po_line_id = purchase_order_line.create(cr,uid,line,context=context)
                line['new_po_line_id'] = new_po_line_id
                
        return pos
    def _get_lines(self,cr,uid,ids,states=None,context=None):
        todo = []
        for po in self.browse(cr, uid, ids, context=context):
            if not po.order_line:
                continue
            for line in po.order_line:
                if states == None or line.state in states:
                    todo.append(line.id)
        return todo
        
    def button_update_uom(self, cr, uid, ids, context=None):
        po_lines = {}
        if context and context.get("uom_todo"):
            po_lines = context.get("uom_todo")
        else:
            for po in self.browse(cr, uid, ids, context=context):
                for line in po.order_line:
                    if line.product_id.id not in po_lines and line.product_uom.id != line.product_id.uom_po_id.id:
                        po_lines.update({line.id:line.product_id.uom_po_id.id})
                        
        po_line_obj = self.pool.get('purchase.order.line')
        for po_line in po_lines:
            cr.execute('update purchase_order_line set product_uom=%s where id=%s',(po_lines[po_line],po_line))
            
        return True
    
    def wkf_confirm_order(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        todo = []
        uom_todo = {}
        for po in self.browse(cr, uid, ids, context=context):
            if not po.order_line:
                raise osv.except_osv(_('Error!'),_('You cannot confirm a purchase order without any purchase order line.'))
            for line in po.order_line:
                if line.state=='draft' or line.state=='rejected':
                    todo.append(line.id)
                    if line.product_uom.id != line.product_id.uom_po_id.id:
                        uom_todo.update({line.id:line.product_id.uom_po_id.id})        
        self.pool.get('purchase.order.line').write(cr, uid, todo, {'state':'confirmed'},context)
        for id in ids:
            self.write(cr, uid, [id], {'state' : 'confirmed', 'validator' : uid, 'inform_type':'1'})
        #update the product uom to po line
        context.update({'uom_todo':uom_todo})
        self.button_update_uom(cr, uid, ids, context)
        return True    
            
    def wkf_approve_order(self, cr, uid, ids, context=None):                    
#        lines = self._get_lines(cr,uid,ids,['confirmed','rejected'],context=context)
        lines = []
        for po in self.browse(cr, uid, ids, context=context):
            for line in po.order_line:
                if line.state=='rejected':
                    raise osv.except_osv(_('Error!'),_('You cannot approve a purchase order with rejected purchase order lines.'))
                if line.state=='confirmed':
                    lines.append(line.id)
        self.pool.get('purchase.order.line').write(cr, uid, lines, {'state':'approved'},context)
        self.write(cr, uid, ids, {'state': 'approved', 'date_approve': fields.date.context_today(self,cr,uid,context=context), 'inform_type':'3'})
        return True
    
    def wkf_done(self, cr, uid, ids, context=None):
        #check the receipt number field
        order = self.browse(cr,uid,ids[0],context=context)
        #to see if there are taxes code
        has_tax = order.taxes_id and len(order.taxes_id) > 0
        if has_tax:
            # to see if the tax code has amount, since there is a 'No Tax' tax in system
            has_tax_amt = False
            for tax in order.taxes_id:
                if tax.amount > 0:
                    has_tax_amt = True
                    break
            if not has_tax_amt:
                has_tax = False
                    
        if  (not has_tax and order.amount_tax <= 0) or (order.receipt_number and order.receipt_number != ''):
            #only when get the receipt, then update status to 'done'
            #update lines to 'done'  
            lines = self._get_lines(cr,uid,ids,['approved'],context=context)
            self.pool.get('purchase.order.line').write(cr, uid, lines, {'state':'done'},context)
            self.write(cr, uid, ids, {'state': 'done'})
        else:
            #update status to 'waiting receipt'
            self.write(cr, uid, ids, {'state': 'wait_receipt'})       
            
    def write(self, cr, user, ids, vals, context=None):
        if vals.get('receipt_number') and vals.get('receipt_number') != '':
            #if the state is 'wait_receipt' then update the state to done when user entered the receipt_number
            order = self.browse(cr,user,ids[0],context=context)
            if order.state == 'wait_receipt':
                vals.update({'state':'done'})
        #if user changed the expected plan date, then update the associated pickings
        if vals.get('minimum_planned_date') and vals.get('minimum_planned_date') != '':
            order = self.browse(cr,user,ids[0],context=context)
            if order.picking_ids:
                pick_ids = []
                for pick in order.picking_ids:
                    if pick.state != 'cancel' and pick.state !='done':
                        pick_ids.append(pick.id)
                self.pool.get('stock.picking.in').write(cr,user,pick_ids,{'min_date':vals.get('minimum_planned_date')})
            
            
        return super(purchase_order,self).write(cr,user,ids,vals,context=context)      
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'receipt_number':None,
        })
        return super(purchase_order, self).copy(cr, uid, id, default, context)        
    def action_reject(self, cr, uid, ids, message, context=None):
#        lines = self._get_lines(cr,uid,ids,['confirmed'],context=context)
        lines = []
        for po in self.browse(cr, uid, ids, context=context):
            for line in po.order_line:
                if line.state=='approved':
                    raise osv.except_osv(_('Error!'),_('You cannot reject a purchase order with approved purchase order lines.'))
                if line.state=='confirmed':
                    lines.append(line.id)
        self.pool.get('purchase.order.line').write(cr, uid, lines, {'state':'rejected'},context)         
        wf_service = netsvc.LocalService("workflow")
        self.write(cr,uid,ids,{'state':'rejected','reject_msg':message, 'inform_type':'2'})

        for (id, name) in self.name_get(cr, uid, ids):
            wf_service.trg_validate(uid, 'purchase.order', id, 'purchase_reject', cr)
        return True

    '''
    Change the picking/invoice "cancel" to "unlink"
    '''
    def action_cancel(self, cr, uid, ids, context=None):
        for purchase in self.browse(cr, uid, ids, context=context):
            del_pick_ids = []
            for pick in purchase.picking_ids:
                if pick.state == 'done':
                    raise osv.except_osv(
                        _('Unable to cancel this purchase order.'),
                        _('First cancel all receptions related to this purchase order.'))
                if pick.state not in ('cancel','done'):
                    del_pick_ids.append(pick.id)
            if del_pick_ids:
                self.pool.get('stock.picking').unlink(cr, uid, del_pick_ids, context=context)
                
            del_inv_ids = []
            for inv in purchase.invoice_ids:
                if inv and inv.state not in ('cancel','draft'):
                    raise osv.except_osv(
                        _('Unable to cancel this purchase order.'),
                        _('You must first cancel all receptions related to this purchase order.'))
                if inv.state == 'draft':
                    del_inv_ids.append(inv.id)
            if del_inv_ids:
                self.pool.get('account.invoice').unlink(cr, uid, del_inv_ids, context=context)
        self.write(cr,uid,ids,{'state':'cancel'})
        return True
                        
    def button_cancel_except(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for purchase in self.browse(cr, uid, ids, context=context):
            invoice_qty = 0
            rec_qty = 0
            for line in purchase.order_line:
                rec_qty += line.receive_qty - line.return_qty
                invoice_qty += line.invoice_qty
            for pick in purchase.picking_ids:
                if pick.state not in ('draft','cancel'):
                    if rec_qty > 0:
                        raise osv.except_osv(
                        _('Unable to cancel this purchase order.'),
                        _('There are received products  or receptions not in draft/cancel related to this purchase order.'))
            for pick in purchase.picking_ids:
                if pick.state == 'draft':
                    wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_cancel', cr)
            for inv in purchase.invoice_ids:
                if inv and inv.state not in ('cancel','draft'):
                    if invoice_qty > 0:
                        raise osv.except_osv(
                        _('Unable to cancel this purchase order.'),
                        _('There are invoiced products or invoices not in draft/cancel related to this purchase order.'))
                if inv and inv.state == 'draft':
                    wf_service.trg_validate(uid, 'account.invoice', inv.id, 'invoice_cancel', cr)
        self.write(cr,uid,ids,{'state':'cancel_except'})
        #cancel_excep all order lines
        lines = self._get_lines(cr,uid,ids,context=context)
        self.pool.get('purchase.order.line').write(cr, uid, lines, {'state': 'cancel_except'},context)
        
        return True    
    def action_cancel_draft(self, cr, uid, ids, context=None):
        for po in self.browse(cr, uid, ids, context=context):
            if po.state not in('cancel','sent','confirmed'):
                raise osv.except_osv(_('Error!'), 
                    _('Only purchase order with cancel/sent/confirmed can be deleted!'))                
        resu = super(purchase_order,self).action_cancel_draft(cr,uid,ids,context)
        lines = self._get_lines(cr,uid,ids,context=context)
        self.pool.get('purchase.order.line').write(cr, uid, lines, {'state': 'draft'},context)
        return resu
    
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
    
    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        #deal the 'date' datetime field query
        new_args = deal_args(self,args)    
        return super(purchase_order,self).search(cr, user, new_args, offset, limit, order, context, count)
    
    def _update_po_lines(self,cr,uid,ids,values,context=None):
        pos = self.browse(cr,uid,ids,context)
        #update order lines
        line_ids = []
        for po in pos:
            lines = po.order_line
            for line in lines:
                if line.state != 'cancel':
                    line_ids.append(line.id)
        self.pool.get('purchase.order.line').write(cr,uid,line_ids,values)
          
    def button_to_changing(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single order at a time'
        wf_service = netsvc.LocalService("workflow")
        for purchase in self.browse(cr, uid, ids, context=context):
#            for pick in purchase.picking_ids:
#                if pick.state not in ('draft','cancel','done'):
#                    raise osv.except_osv(
#                        _('Unable to change this purchase order.'),
#                        _('First cancel all receptions not in draft/cancel/done related to this purchase order.'))
#            for pick in purchase.picking_ids:
#                if pick.state == 'draft':
#                    wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_cancel', cr)
            #johnw, 01/15/2015, change the po changing logic on the picking, delete the related picking not in cancel/done directly, other pickings are OK to change PO. 
            del_pick_ids = []
            for pick in purchase.picking_ids:
                if pick.state not in ('cancel','done'):
                    del_pick_ids.append(pick.id)
            if del_pick_ids:
                self.pool.get('stock.picking').unlink(cr, uid, del_pick_ids, context=context)
                
            del_inv_ids = []
            for inv in purchase.invoice_ids:
                if inv and inv.state not in ('cancel','draft','paid'):
                    raise osv.except_osv(
                        _('Unable to change this purchase order.'),
                        _('You must first cancel all invoices not in draft/cancel/paid related to this purchase order.'))
                if inv.state == 'draft':
#                    wf_service.trg_validate(uid, 'account.invoice', inv.id, 'invoice_cancel', cr)
                    #johnw, 01/15/2015, change the related draft invoice logic, delete them directly
                    del_inv_ids.append(inv.id)
            if del_inv_ids:
                self.pool.get('account.invoice').unlink(cr, uid, del_inv_ids, context=context)
                             
        self.write(cr,uid,ids,{'state':'changing'},context)
        self._update_po_lines(cr,uid,ids,{'state':'changing'})        
        
    def button_to_changing_confirmed(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single order at a time'
        self.write(cr,uid,ids,{'state':'changing_confirmed','inform_type':'4'},context)
        self._update_po_lines(cr,uid,ids,{'state':'changing_confirmed'},context)
        #changing notification 
        self.pool.get('order.informer')._inform_po_changing(cr, uid, context)
        
    def button_to_changing_rejected(self, cr, uid, ids, reject_msg, context=None):
        assert len(ids) == 1, 'This option should only be used for a single order at a time'
        self.write(cr,uid,ids,{'state':'changing_rejected','reject_msg':reject_msg,'inform_type':'5'},context)
        self._update_po_lines(cr,uid,ids,{'state':'changing_rejected'},context)
        #changing notification 
        self.pool.get('order.informer')._inform_po_changing(cr, uid, context)
        
    def _create_pickings(self, cr, uid, order, order_lines, picking_id=False, context=None):
        if not picking_id:
            picking_id = self.pool.get('stock.picking').create(cr, uid, self._prepare_order_picking(cr, uid, order, context=context))
        todo_moves = []
        stock_move = self.pool.get('stock.move')
        wf_service = netsvc.LocalService("workflow")
        for order_line in order_lines:
            if not order_line.product_id:
                continue
#            if order_line.product_id.type in ('product', 'consu'):
            move_qty = order_line.product_qty
            if order_line.move_ids:
                #get all the valid move picking quantity of this purchase order line
                for move in order_line.move_ids:
                    if move.state != 'cancel':
                        if move.type == 'in':
                            move_qty -= move.product_qty
                        if move.type == 'out':
                            move_qty += move.product_qty
            if order_line.product_id.type in ('product', 'consu') and move_qty > 0:
                order_line.product_qty = move_qty 
                move = stock_move.create(cr, uid, self._prepare_order_line_move(cr, uid, order, order_line, picking_id, context=context))
                if order_line.move_dest_id:
                    order_line.move_dest_id.write({'location_id': order.location_id.id})
                todo_moves.append(move)
        if len(todo_moves) > 0:
            stock_move.action_confirm(cr, uid, todo_moves)
            stock_move.force_assign(cr, uid, todo_moves)
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
            return [picking_id]
        else:
            self.pool.get('stock.picking').unlink(cr,uid,[picking_id],context)
            return []
            
    def button_to_changing_approved(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single order at a time'
        id = ids[0]
        #if po shipped, and there are unreceived quantiy, then set the shipped to False
        po = self.browse(cr,uid,id,context)
        shipped = po.shipped
        if po.shipped:
            for line in po.order_line:
                if line.product_qty > line.receive_qty - line.return_qty:
                    shipped = False
                    break
        self.write(cr,uid,ids,{'shipped':shipped, 'state':'approved','inform_type':'3'},context)
        self._update_po_lines(cr,uid,ids,{'state':'approved'},context)   
        if not shipped:
           self.action_picking_create(cr,uid,ids,context) 
    def view_picking(self, cr, uid, ids, context=None):
        #create the picking for unshipped orders
        for po in self.read(cr,uid,ids,['shipped']):
            if not po['shipped']:
                self.action_picking_create(cr,uid,ids,context) 
        return super(purchase_order,self).view_picking(cr, uid, ids, context)      
    
    def button_manual_done(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single order at a time'
        po = self.browse(cr, uid, ids[0], context=context)
        ready_done = True
        if po.state == 'approved' and po.shipped and po.invoiced and po.paid_done:
            for po_line in po.order_line:
                if po_line.product_qty > po_line.invoice_qty:
                    #no invoice quantity completely, then can not be done
                    ready_done = False
                    break
            if ready_done:
                for inv in po.invoice_ids:
                    if inv.state not in('cancel', 'paid'):
                        #if there are invoices with other states, then that invoices need to process to cancel or paid, then the purchase order can be done
                        ready_done = False
                        break  
        else:
            ready_done = False          
        if not ready_done:
                raise osv.except_osv(_('Error!'),
                                     _('The PO only can be done when it is approved, shipped, invoiced and paid completely'))          

        self.wkf_done(cr, uid, ids, context=context)

    def button_done_except(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single order at a time'
        self.write(cr,uid,ids,{'state':'done_except'},context)
        self._update_po_lines(cr,uid,ids,{'state':'done_except'},context)
        
    def picking_done(self, cr, uid, ids, context=None):
        ids_done = []
        for po in self.browse(cr, uid, ids, context):
            remain_qty = 0
            for line in po.order_line:
                if line.product_id.type not in ('consu','service'):
                    remain_qty += line.product_qty - (line.receive_qty - line.return_qty)
            if remain_qty == 0:
                ids_done.append(po.id)
        return super(purchase_order,self).picking_done(cr, uid, ids_done, context)
          
class purchase_order_line(osv.osv):  
    _name = "purchase.order.line"
    _inherit = 'purchase.order.line' 

    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('confirmed', 'Waiting Approval'),
        ('rejected', 'Rejected'),
        ('approved', 'Approved'),
        ('changing', 'In Changing'),
        ('changing_confirmed', 'Changing Waiting Approval'),
        ('changing_rejected', 'Changing Rejected'),
        ('done', 'Done'),
        ('done_except', 'Done with Exception'),
        ('cancel', 'Cancelled'),
        ('cancel_except', 'Cancelled with Exception')
    ]
        
    def _get_supp_prod(self, cr, uid, ids, fields, arg, context=None):
        result = {}
        for line in self.browse(cr,uid,ids,context=context):
            result[line.id] = {
                'supplier_prod_id': False,  
                'supplier_prod_name': '',
                'supplier_prod_code': '',
                'supplier_delay': 1,
            }
            if not line.product_id or not line.product_id.seller_ids:
                continue
            for seller_info in line.product_id.seller_ids:
                if seller_info.name == line.partner_id:
                    #found the product supplier info
                    result[line.id].update({
                        'supplier_prod_id': seller_info.id,                    
                        'supplier_prod_name': seller_info.product_name,
                        'supplier_prod_code': seller_info.product_code,
                        'supplier_delay': seller_info.delay,
                        
                    })
                    break
        return result

    def _get_rec_info(self, cr, uid, ids, fields, args, context=None):
        result = {}
        for id in ids:
            result[id] = {'receive_qty':0,'return_qty':0,'can_change_price':True,'can_change_product':True}
        uom_obj = self.pool.get("product.uom")
        for line in self.browse(cr,uid,ids,context=context):
            rec_qty = 0
            return_qty = 0
            invoice_qty = 0
            can_change_price = True
            can_change_product = True
            if line.move_ids:
                #once there are moving, then can not change product, 06/07/2014 by johnw
                can_change_product = False
                for move in line.move_ids:
                    if move.state == 'done':
                        if move.type == 'in':
                            rec_qty += move.product_qty
                        if move.type == 'out':
                            return_qty += move.product_qty
                #if there are products received then can not change product
#                if rec_qty - return_qty > 0:
#                    can_change_product = False
            if line.invoice_lines:
                #once there are invoice lines, then can not change product, 06/07/2014 by johnw
                can_change_product = False
                for inv_line in line.invoice_lines:
                    #if there are uncanceled invoices, then can not change product
                    if inv_line.invoice_id.state != 'cancel':
#                        can_change_product = False
                        invoice_qty += inv_line.quantity
                    #if there are done invoices, then can not change price
                    if can_change_price and (inv_line.invoice_id.state == 'paid' or len(inv_line.invoice_id.payment_ids) > 0):
                        can_change_price = False
            product_uom_base_qty = line.product_qty
            if line.product_uom.id != line.product_id.uom_id.id:
                product_uom_base_qty = uom_obj._compute_qty_obj(cr, uid, line.product_uom, line.product_qty, line.product_id.uom_id)
            result[line.id].update({'receive_qty':rec_qty,
                                    'return_qty':return_qty,
                                    'invoice_qty':invoice_qty,
                                    'can_change_price':can_change_price,
                                    'can_change_product':can_change_product,
                                    'product_uom_base_qty':product_uom_base_qty,})
        return result
    def _amount_line(self, cr, uid, ids, prop, arg, context=None):
        res = {}    
        for id in ids:
            res[id] = {'price_subtotal':0,'price_subtotal_withtax':0}         
        cur_obj=self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        for line in self.browse(cr, uid, ids, context=context):
            taxes = tax_obj.compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id]['price_subtotal'] = cur_obj.round(cr, uid, cur, taxes['total'])
            res[line.id]['price_subtotal_withtax'] = cur_obj.round(cr, uid, cur, line.price_unit*line.product_qty)
        return res
 
    _columns = {
        'po_notes': fields.related('order_id','notes',string='Terms and Conditions',readonly=True,type="text"),
        'payment_term_id': fields.related('order_id','payment_term_id',string='Payment Term',readonly=True,type="many2one", relation="account.payment.term"),
        'state': fields.selection(STATE_SELECTION, 'Status', readonly=True),
        'reject_msg': fields.text('Rejection Message', track_visibility='onchange'),
        'create_uid':  fields.many2one('res.users', 'Creator', select=True, readonly=True),
        'create_date': fields.datetime('Creation Date', readonly=True, select=True),
        'image_medium': fields.related('product_id','image_medium',type='binary',String="Medium-sized image"),
        'change_log': fields.one2many('change.log.po.line','po_line_id','Changing Log'),
        'inform_type': fields.char('Informer Type', size=10, readonly=True, select=True),
        'has_freight': fields.related('order_id','has_freight',string='Has Freight', type="boolean", readonly=True),
        'amount_freight': fields.related('order_id','amount_freight',string='Freight', type='float', readonly=True),
        'supplier_prod_id': fields.function(_get_supp_prod, type='integer', string='Supplier Product ID', multi="seller_info"),
        'supplier_prod_name': fields.function(_get_supp_prod, type='char', string='Supplier Product Name', required=True, multi="seller_info"),
        'supplier_prod_code': fields.function(_get_supp_prod, type='char', string='Supplier Product Code', multi="seller_info"),
        'supplier_delay' : fields.function(_get_supp_prod, type='integer', string='Supplier Lead Time', multi="seller_info"),
        'receive_qty' : fields.function(_get_rec_info, type='float', digits_compute=dp.get_precision('Product Unit of Measure'), string='Received Quantity', multi="rec_info"),
        'return_qty' : fields.function(_get_rec_info, type='float', digits_compute=dp.get_precision('Product Unit of Measure'), string='Returned Quantity', multi="rec_info"),
        'can_change_price' : fields.function(_get_rec_info, type='boolean', string='Can Change Price', multi="rec_info"),
        'can_change_product' : fields.function(_get_rec_info, type='boolean', string='Can Change Product', multi="rec_info"),
        'invoice_qty' : fields.function(_get_rec_info, type='float', digits_compute=dp.get_precision('Product Unit of Measure'), string='Invoice Quantity', multi="rec_info"),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account'),multi='amount_line',),
        'price_subtotal_withtax': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account'),multi='amount_line',),
        'product_uom_base': fields.related('product_id','uom_id',type='many2one',relation='product.uom', string='Base UOM',readonly=True),
        'product_uom_base_qty': fields.function(_get_rec_info, type='float', digits_compute=dp.get_precision('Product Unit of Measure'), string='Base Quantity', multi="rec_info"),
        'mfg_id': fields.many2one('sale.product', string='MFG ID'),     
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of sales order lines."),   
    }  
    _order = "order_id desc, sequence, id"
    _defaults = {
        'supplier_delay': lambda *a: 1,
        'receive_qty': 0,
        'return_qty': 0,
        'can_change_price': True,
        'can_change_product': True,
    }               
    def _is_po_update(self,cr,uid,po,state,context=None):
        po_update = True
        for line in po.order_line:
            if line.state!=state:
                po_update = False
                break
        return po_update

    def action_confirm(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'confirmed'}, context=context)
        self.write(cr, uid, ids, {'inform_type': '1'}, context=context)
        wf_service = netsvc.LocalService("workflow")
        #update po's state
        po_line_obj = self.browse(cr,uid,ids[0],context=context)
        po = po_line_obj.order_id
        is_po_update = self._is_po_update(cr,uid,po,'confirmed',context=context)
        if is_po_update:
            wf_service.trg_validate(uid, 'purchase.order', po.id, 'purchase_confirm', cr)            
            
        return True 
            
    def action_approve(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'approved'}, context=context)
        wf_service = netsvc.LocalService("workflow")
        #update po's state
        po_line_obj = self.browse(cr,uid,ids[0],context=context)
        po = po_line_obj.order_id
        is_po_update = self._is_po_update(cr,uid,po,'approved',context=context)
        if is_po_update:
            wf_service.trg_validate(uid, 'purchase.order', po.id, 'purchase_approve', cr)
        return True   
    
    def action_reject(self, cr, uid, ids, message, context=None):
        self.write(cr, uid, ids, {'state': 'rejected','reject_msg':message}, context=context)
        self.write(cr, uid, ids, {'inform_type': '2'}, context=context)
        wf_service = netsvc.LocalService("workflow")
        #update po's state
        po_line_obj = self.browse(cr,uid,ids[0],context=context)
        po = po_line_obj.order_id
        is_po_update = self._is_po_update(cr,uid,po,'rejected',context=context)
        if is_po_update:
            self.pool.get("purchase.order").action_reject(cr,uid,[po.id],"All lines are rejected",context=context)
        return True     
    #write the product supplier information
    def _update_prod_supplier(self,cr,uid,ids,vals,context=None):
        if vals.has_key('supplier_prod_name') or vals.has_key('supplier_prod_code') or vals.has_key('supplier_delay'):
            prod_supp_obj = self.pool.get('product.supplierinfo')
            new_vals = {'min_qty':0}
            if vals.has_key('supplier_prod_name'):
                new_vals.update({'product_name':vals['supplier_prod_name']})
            if vals.has_key('supplier_prod_code'):
                new_vals.update({'product_code':vals['supplier_prod_code']})
            if vals.has_key('supplier_delay'):
                new_vals.update({'delay':vals['supplier_delay']})
            #for the dmp_currency module, set the currency
            if ids:
                #from order line update
                for line in self.browse(cr,uid,ids,context=context):
                    new_vals.update({'name':line.partner_id.id,'product_id':line.product_id.product_tmpl_id.id,'currency':line.order_id.pricelist_id.currency_id.id})
                    if line.supplier_prod_id:
                        #update the prodcut supplier info
                        prod_supp_obj.write(cr,uid,line.supplier_prod_id,new_vals,context=context)
                    else:
                        supplier_prod_id = prod_supp_obj.create(cr,uid,new_vals,context=context)     
            else:
                # from order line create
                po = self.pool.get('purchase.order').browse(cr,uid,vals['order_id'])
                product = self.pool.get('product.product').browse(cr, uid, vals['product_id'], context=context)
                new_vals.update({'name':po.partner_id.id,'product_id':product.product_tmpl_id.id,'currency':po.pricelist_id.currency_id.id})
                prod_supp_ids = prod_supp_obj.search(cr,uid,[('product_id','=',new_vals['product_id']),('name','=',new_vals['name'])])
                if prod_supp_ids and len(prod_supp_ids) > 0:
                    #update the prodcut supplier info
                    prod_supp_obj.write(cr,uid,prod_supp_ids[0],new_vals,context=context)
                else:
                    supplier_prod_id = prod_supp_obj.create(cr,uid,new_vals,context=context)     
          
    def write(self, cr, uid, ids, vals, context=None):
        if not ids:
            return True
        id = ids[0]
        po_line = self.browse(cr,uid,id,context=context)
        #check under the 'changing' status
        if po_line.state == 'changing':
            #changed quantity can not less than the received quantity
            if vals.has_key('product_qty') and vals['product_qty'] <  po_line.receive_qty - po_line.return_qty:
                raise osv.except_osv(_('Error!'),
                                     _('The order quantity(%s) of %s can not be less than the received quantity(%s).')%(vals['product_qty'],po_line.product_id.name,po_line.receive_qty - po_line.return_qty))     
            #changed unir prie can not be do when there are uncanceled pickings or invoices
            if vals.has_key('price_unit') and not po_line.can_change_price:
                raise osv.except_osv(_('Error!'),
                                     _('The price of %s can not be change since there are related existing paid invoices.')%(po_line.product_id.name))     
        
        resu = super(purchase_order_line,self).write(cr, uid, ids, vals, context=context)
        #only when orders confirmed, then record the quantity&price changing log
        if po_line.order_id.state != 'draft':
            log_obj = self.pool.get('change.log.po.line')
            field_names = ['product_qty','price_unit','product_id'];
            for field_name in field_names:
                if vals.has_key(field_name):
                    value_old = getattr(po_line,field_name)
                    value_new = vals[field_name]
                    if field_name == 'product_id':
                        prod_obj = self.pool.get('product.product')
                        value_old = prod_obj.name_get(cr, uid, [value_old.id], context=context)[0][1]
                        value_new = prod_obj.name_get(cr, uid, [vals[field_name]], context=context)[0][1]
                    log_vals = {'po_id':po_line.order_id.id,'po_line_id':po_line.id,'product_id':po_line.product_id.id,
                                'field_name':field_name,'value_old':value_old,'value_new':value_new}
                    log_obj.create(cr,uid,log_vals,context=context)
        #update product supplier info
        self._update_prod_supplier(cr, uid, ids, vals, context)
        #if price_unit changed then update it to product_product.standard_price
        if vals.has_key('price_unit'):
            #standard_price = self.pool.get('product.uom')._compute_price(cr, uid, po_line.product_uom.id, vals["price_unit"],po_line.product_id.uom_id.id)
            #self.pool.get('product.product').write(cr,uid,[po_line.product_id.id],{'standard_price':standard_price,'uom_po_price':vals["price_unit"]},context=context)
            self.pool.get('product.product').write(cr,uid,[po_line.product_id.id],{'uom_po_price':vals["price_unit"]},context=context)
            
        return resu
    def create(self, cr, user, vals, context=None):
        #add the procut_uom set by product's purchase uom
        if 'product_uom' not in vals:
            prod = self.pool.get('product.product').browse(cr, user, vals['product_id'], context=context)
            product_uom = None
            if prod.uom_po_id:
                product_uom = prod.uom_po_id.id
            else:
                product_uom = prod.uom_id.id
            vals.update({'product_uom':product_uom})            
        resu = super(purchase_order_line,self).create(cr, user, vals, context=context)
        #update product supplier info
        self._update_prod_supplier(cr, user, [], vals, context)
        #if price_unit changed then update it to product_product.standard_price
        if vals.has_key('price_unit'):
            prod = self.pool.get('product.product').browse(cr, user, vals['product_id'], context=context)
            #standard_price = self.pool.get('product.uom')._compute_price(cr, user, vals["product_uom"], vals["price_unit"],prod.uom_id.id)            
            #self.pool.get('product.product').write(cr,user,[vals['product_id']],{'standard_price':standard_price,'uom_po_price':vals["price_unit"]},context=context)
            self.pool.get('product.product').write(cr,user,[vals['product_id']],{'uom_po_price':vals["price_unit"]},context=context)
            
        #only when orders confirmed, then record the po lines adding
        uid = user
        po_line = self.browse(cr, uid, resu, context=context)
        if po_line.order_id.state != 'draft':
            log_obj = self.pool.get('change.log.po.line')
            log_vals = {'po_id':po_line.order_id.id,'po_line_id':po_line.id,'product_id':po_line.product_id.id,
                                'field_name':'Add Product','value_old':'','value_new':'price:%s, quantity:%s'%(po_line.product_qty, po_line.price_unit)}
            log_obj.create(cr,uid,log_vals,context=context)                    
        return resu  
    def unlink(self, cr, uid, ids, context=None):
        #only the draft,canceled can be deleted
        lines = self.browse(cr,uid,ids,context=context)
        for line in lines:
            if line.state != 'draft' and line.state != 'cancel' and line.state != 'rejected' and line.state != 'changing' and line.state != 'changing_rejected':
                raise osv.except_osv(_('Error'), _('Only the lines with draft, canceled, rejected, changing, changing rejected can be deleted!\n%s'%line.product_id.name))
            if (line.move_ids and line.move_ids) or (line.invoice_lines and line.invoice_lines):
                raise osv.except_osv(_('Error'), _('Can not delete the lines with picking or invoice lines!\n%s'%line.product_id.name))
            #only when orders confirmed, then record the po lines deleting
            if line.order_id.state != 'draft':
                log_obj = self.pool.get('change.log.po.line')
                log_vals = {'po_id':line.order_id.id,'po_line_id':line.id,'product_id':line.product_id.id,
                                'field_name':'Delete Product','value_old':'price:%s, quantity:%s'%(line.product_qty, line.price_unit),'value_new':''}
                log_obj.create(cr,uid,log_vals,context=context)
        return super(purchase_order_line,self).unlink(cr,uid,ids,context=context)
    def copy_data(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({'change_log':None})
        return super(purchase_order_line, self).copy_data(cr, uid, id, default, context)
            
    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None):
        if not context:
            context = {}
        """
        onchange handler of product_id.
        """
        res = super(purchase_order_line,self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id,
                                partner_id, date_order, fiscal_position_id, date_planned,name, price_unit, context)
        if product_id and context is not None and not res['value'].get('taxes_id') and context.get('po_taxes_id')[0][2]: 
            # - determine taxes_id when purchase_header has taxes_id and produt has not own taxes setting
            account_fiscal_position = self.pool.get('account.fiscal.position')
            account_tax = self.pool.get('account.tax')
            taxes = account_tax.browse(cr, uid, context['po_taxes_id'][0][2])
            fpos = fiscal_position_id and account_fiscal_position.browse(cr, uid, fiscal_position_id, context=context) or False
            taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes)
            res['value'].update({'taxes_id': taxes_ids})

        # update the product supplier info
        if product_id and not context.get('supplier_prod_id'):
            prod_supp_obj = self.pool.get('product.supplierinfo')
            product = self.pool.get("product.product").browse(cr, uid, product_id, context=context)
            prod_supp_ids = prod_supp_obj.search(cr,uid,[('product_id','=',product.product_tmpl_id.id),('name','=',partner_id)])
            if prod_supp_ids and len(prod_supp_ids) > 0:
                prod_supp = prod_supp_obj.browse(cr,uid,prod_supp_ids[0],context=context)
                res['value'].update({'supplier_prod_id': prod_supp.id,
                                    'supplier_prod_name': context.get('supplier_prod_name') or prod_supp.product_name,
                                    'supplier_prod_code': context.get('supplier_prod_code') or prod_supp.product_code,
                                    'supplier_delay' :context.get('supplier_delay') or  prod_supp.delay})
            else:
                res['value'].update({'supplier_prod_id': False,
                                    'supplier_prod_name': context.get('supplier_prod_name') or '',
                                    'supplier_prod_code': context.get('supplier_prod_code') or '',
                                    'supplier_delay' : context.get('supplier_delay') or 1})
            
        return res

    def onchange_lead(self, cr, uid, ids, change_type, changes_value, date_order, context=None):
        res = {'value':{}}
        if change_type == 'date_planned':
            changes_value = changes_value[:10]
            supplier_delay = datetime.datetime.strptime(changes_value, DEFAULT_SERVER_DATE_FORMAT) - datetime.datetime.strptime(date_order, DEFAULT_SERVER_DATE_FORMAT)
            res['value']={'supplier_delay':supplier_delay.days}
        if change_type == 'supplier_delay':
            date_planned = datetime.datetime.strptime(date_order, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(days=changes_value)
            date_planned = datetime.datetime.strftime(date_planned,DEFAULT_SERVER_DATE_FORMAT)
            print res['value']
            res['value'].update({'date_planned':date_planned})
        return res
    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        #deal the 'date' datetime field query
        new_args = deal_args(self,args)
        return super(purchase_order_line,self).search(cr, user, new_args, offset, limit, order, context, count)

class stock_move(osv.osv):
    _inherit = "stock.move" 
    _columns = {    
        'supplier_prod_name': fields.related('purchase_line_id', 'supplier_prod_name',string='Supplier Product Name',type="char",readonly=True,store=True),
    }
import time
from openerp.report import report_sxw
from openerp.osv import osv
from openerp import pooler

#redefine the purchase PDF report to new rml
from openerp.addons.purchase.report.order import order
from openerp.report import report_sxw

class dmp_pur_order(order):
    def __init__(self, cr, uid, name, context):
        super(order, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'get_taxes_name':self._get_tax_name})
        self.localcontext.update({'get_boolean_name':self._get_boolean_name})
    #get the taxes name             
    def _get_tax_name(self,taxes_id):
        names = ''
        for tax in taxes_id:
            names += ", " + tax.name
        if names != '': 
            names = names[2:]
        return names      
    def _get_boolean_name(self,bool_val):
#        def _get_source(self, cr, uid, name, types, lang, source=None):
        bool_name = self.pool.get("ir.translation")._get_source(self.cr, self.uid, None, 'code', self.localcontext['lang'], 'bool_' + str(bool_val))
        return bool_name
          
report_sxw.report_sxw('report.purchase.order.dmp','purchase.order','addons/dmp_purchase/report/purchase_order.rml',parser=dmp_pur_order)
report_sxw.report_sxw('report.purchase.quotation.dmp','purchase.order','addons/dmp_purchase/report/purchase_quotation.rml',parser=dmp_pur_order)

from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
def deal_args(obj,args):  
    new_args = []
    for arg in args:
        fld_name = arg[0]
        if fld_name == 'create_date' or fld_name == 'write_date':
            fld_operator = arg[1]
            fld_val = arg[2]
            fld = obj._columns.get(fld_name)
            #['date','=','2013-12-12 16:00:00'] the '16' was generated for the timezone
            if fld._type == 'datetime' and fld_operator == "=" and fld_val.endswith('00:00'):
                time_start = [fld_name,'>=',fld_val]
                time_obj = datetime.datetime.strptime(fld_val,DEFAULT_SERVER_DATETIME_FORMAT)
                time_obj += relativedelta(days=1)
                time_end = [fld_name,'<=',time_obj.strftime(DEFAULT_SERVER_DATETIME_FORMAT)]
                new_args.append(time_start)
                new_args.append(time_end)
            else:
                new_args.append(arg)
        else:
            new_args.append(arg)    
    return new_args

from openerp.addons.purchase.purchase import purchase_order_line as oe_po_line
def dmp_po_line_onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
        partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
        name=False, price_unit=False, context=None):
    """
    onchange handler of product_id.
    """
    if context is None:
        context = {}

    res = {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'product_uom' : uom_id or False}}
    if not product_id:
        return res

    product_product = self.pool.get('product.product')
    product_uom = self.pool.get('product.uom')
    res_partner = self.pool.get('res.partner')
    product_supplierinfo = self.pool.get('product.supplierinfo')
    product_pricelist = self.pool.get('product.pricelist')
    account_fiscal_position = self.pool.get('account.fiscal.position')
    account_tax = self.pool.get('account.tax')

    # - check for the presence of partner_id and pricelist_id
    #if not partner_id:
    #    raise osv.except_osv(_('No Partner!'), _('Select a partner in purchase order to choose a product.'))
    #if not pricelist_id:
    #    raise osv.except_osv(_('No Pricelist !'), _('Select a price list in the purchase order form before choosing a product.'))

    # - determine name and notes based on product in partner lang.
    context_partner = context.copy()
    if partner_id:
        lang = res_partner.browse(cr, uid, partner_id).lang
        context_partner.update( {'lang': lang, 'partner_id': partner_id} )
    product = product_product.browse(cr, uid, product_id, context=context_partner)
    name = product.name
    if product.description_purchase:
        name += '\n' + product.description_purchase
    res['value'].update({'name': name})

    # - set a domain on product_uom
    res['domain'] = {'product_uom': [('category_id','=',product.uom_id.category_id.id)]}

    # - check that uom and product uom belong to the same category
    product_uom_po_id = product.uom_po_id.id
    if not uom_id:
        uom_id = product_uom_po_id

    if product.uom_id.category_id.id != product_uom.browse(cr, uid, uom_id, context=context).category_id.id:
        if self._check_product_uom_group(cr, uid, context=context):
            res['warning'] = {'title': _('Warning!'), 'message': _('Selected Unit of Measure does not belong to the same category as the product Unit of Measure.')}
        uom_id = product_uom_po_id

    res['value'].update({'product_uom': uom_id})

    # - determine product_qty and date_planned based on seller info
    if not date_order:
        date_order = fields.date.context_today(self,cr,uid,context=context)


    supplierinfo = False
    for supplier in product.seller_ids:
        if partner_id and (supplier.name.id == partner_id):
            supplierinfo = supplier
            if supplierinfo.product_uom.id != uom_id:
                res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier only sells this product by %s') % supplierinfo.product_uom.name }
            min_qty = product_uom._compute_qty(cr, uid, supplierinfo.product_uom.id, supplierinfo.min_qty, to_uom_id=uom_id)
            if (qty or 0.0) < min_qty: # If the supplier quantity is greater than entered from user, set minimal.
                if qty:
                    res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier has a minimal quantity set to %s %s, you should not purchase less.') % (supplierinfo.min_qty, supplierinfo.product_uom.name)}
                qty = min_qty
    dt = self._get_date_planned(cr, uid, supplierinfo, date_order, context=context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    qty = qty or 1.0
    res['value'].update({'date_planned': date_planned or dt})
    if qty:
        res['value'].update({'product_qty': qty})

    # - determine price_unit and taxes_id
    #only change the price when the price_unir parameter has not value, by john wang, 2014/02/25
    if not price_unit or price_unit == 0:
        if pricelist_id:
            price = product_pricelist.price_get(cr, uid, [pricelist_id],
                    product.id, qty or 1.0, partner_id or False, {'uom': uom_id, 'date': date_order})[pricelist_id]
        else:
            price = product.uom_po_price
    else:
        price = price_unit
        
    taxes = account_tax.browse(cr, uid, map(lambda x: x.id, product.supplier_taxes_id))
    fpos = fiscal_position_id and account_fiscal_position.browse(cr, uid, fiscal_position_id, context=context) or False
    taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes)
    res['value'].update({'price_unit': price, 'taxes_id': taxes_ids})

    return res
oe_po_line.onchange_product_id = dmp_po_line_onchange_product_id    