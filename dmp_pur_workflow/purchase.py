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
            'dmp_pur_workflow.mt_rfq_rejected': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'rejected',
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
            
    _columns = {
        'state': fields.selection(STATE_SELECTION, 'Status', readonly=True, help="The status of the purchase order or the quotation request. A quotation is a purchase order in a 'Draft' status. Then the order has to be confirmed by the user, the status switch to 'Confirmed'. Then the supplier must confirm the order to change the status to 'Approved'. When the purchase order is paid and received, the status becomes 'Done'. If a cancel action occurs in the invoice or in the reception of goods, the status becomes in exception.", select=True),
        'reject_msg': fields.text('Rejection Message', track_visibility='onchange'),
        'inform_type': fields.char('Informer Type', size=10, readonly=True, select=True),
        'approver': fields.many2one('res.users','Approver', readonly=True),
    }

    def _get_lines(self,cr,uid,ids,states=None,context=None):
        todo = []
        for po in self.browse(cr, uid, ids, context=context):
            if not po.order_line:
                continue
            for line in po.order_line:
                if states == None or line.state in states:
                    todo.append(line.id)
        return todo
    
    def wkf_confirm_order(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        todo = []
        for po in self.browse(cr, uid, ids, context=context):
            if not po.order_line:
                raise osv.except_osv(_('Error!'),_('You cannot confirm a purchase order without any purchase order line.'))
            for line in po.order_line:
                if line.state=='draft' or line.state=='rejected':
                    todo.append(line.id)       
        self.pool.get('purchase.order.line').write(cr, uid, todo, {'state':'confirmed'},context)
        for id in ids:
            self.write(cr, uid, [id], {'state' : 'confirmed', 'validator' : uid, 'inform_type':'1'})
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
        self.write(cr, uid, ids, {'state': 'approved', 'approver': uid,\
                                  'date_approve': fields.date.context_today(self,cr,uid,context=context), 'inform_type':'3'})
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
        return super(purchase_order,self).write(cr,user,ids,vals,context=context)   
       
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

 
    _columns = {
        'state': fields.selection(STATE_SELECTION, 'Status', readonly=True),
        'reject_msg': fields.text('Rejection Message', track_visibility='onchange'),
        'inform_type': fields.char('Informer Type', size=10, readonly=True, select=True),         
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
        return resu

    def unlink(self, cr, uid, ids, context=None):
        #only the draft,canceled can be deleted
        lines = self.browse(cr,uid,ids,context=context)
        for line in lines:
            if line.state != 'draft' and line.state != 'cancel' and line.state != 'rejected' and line.state != 'changing' and line.state != 'changing_rejected':
                raise osv.except_osv(_('Error'), _('Only the lines with draft, canceled, rejected, changing, changing rejected can be deleted!\n%s'%line.product_id.name))
            if (line.move_ids and line.move_ids) or (line.invoice_lines and line.invoice_lines):
                raise osv.except_osv(_('Error'), _('Can not delete the lines with picking or invoice lines!\n%s'%line.product_id.name))
        return super(purchase_order_line,self).unlink(cr,uid,ids,context=context)