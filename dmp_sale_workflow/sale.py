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
from openerp import netsvc
from openerp.addons.dm_base import utils
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.addons.sale.sale import sale_order as so

class sale_order(osv.osv):
    _inherit="sale.order"
    
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()
        
    _columns={              
        'state': fields.selection([
            ('draft', 'Draft Quotation'),
            ('sent', 'Quotation Sent'),
            ('review', 'Review'),
            ('engineer', 'Engineering'),
            ('account', 'Accounting'),
            ('super', 'Super Approving'),
            ('progress', 'Sales Order'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('manual', 'Sale to Invoice'),
            ('shipping_except', 'Shipping Exception'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ], 'Status', readonly=True, track_visibility='onchange',
                help="Gives the status of the quotation or sales order.\
              \nThe exception status is automatically set when a cancel operation occurs \
              in the invoice validation (Invoice Exception) or in the picking list process (Shipping Exception).\nThe 'Waiting Schedule' status is set when the invoice is confirmed\
               but waiting for the scheduler to run on the order date.", select=True),
        'reject_message': fields.text('Rejection Message', track_visibility='onchange'),
        #change track_visibility from 'always' to 'onchange'
        'partner_id': fields.many2one('res.partner', 'Customer', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, 
                                      required=True, change_default=True, select=True, track_visibility='onchange'),
        'amount_untaxed': fields.function(so._amount_all, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The amount without tax.", track_visibility='onchange'),              
    }
    
    #call by workflow                      
    def to_state(self,cr,uid,ids,new_state,context=None):
        '''
        Why put this variable here, because if we put thie variable as one class level,
        then the translation can not be translate to current user languange, 
        since one class instance will be init only one time and the "_()" function will run one time
        but system may be used by different languange's users         
        ''' 
        EMAIL_ACTIONS = {'review':{'msg':_('sales order submitted, need your review'),'groups':['dmp_sale_workflow.group_sale_reviewer']},
                         'engineer':{'msg':_('sales confirmed, need engineering approval'),'groups':['dmp_engineer.group_engineer_user']},
                         'account':{'msg':_('engineering approved, need accounting approval'),'groups':['account.group_account_manager']},
                         'super':{'msg':_('accounting approved, need super approval'),'groups':['dmp_sale_workflow.group_super_manager']},
                         'review2draft':{'msg':_('reviewer rejected, please do re-checking'),'groups':['base.group_sale_salesman']},
                         'super2engineer':{'msg':_('Super rejected, please do engineering re-checking'),'groups':['dmp_engineer.group_engineer_user']},
                         'super2account':{'msg':_('Super rejected, please do accounting re-checking'),'groups':['account.group_account_manager']},}
                
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        vals = {'state':new_state, 'reject_message':None}
        action = new_state
        #handle the super rejection
        old_state = self.read(cr, uid, ids[0], ['state'], context=context)['state']
        if old_state == 'review' and new_state == 'draft':
            action = 'review2draft'
        if old_state == 'super' and new_state == 'engineer':
            action = 'super2engineer'
        if old_state == 'super' and new_state == 'account':
            action = 'super2account'
        self.write(cr, uid, ids, vals, context=context)
        #send email to the user group that need do next action
        utils.email_notify(cr, uid, self._name, ids, EMAIL_ACTIONS, action, subject_fields = ['name'], email_to = [], 
                           context=context, object_desc=_(self._description))
          
    REJECT_SIGNALS = {'review-draft':'review_reject_draft',
                      'super-engineer':'super_reject_engineer',
                      'super-account':'super_reject_account',}
                                          
    def action_reject(self, cr, uid, ids, context=None):   
        if not context:
            context = {}  
        ctx = dict(context)
        ctx.update({'confirm_title':_('Reason for rejection'),
                    'src_model':'sale.order',
                    'model_callback':'action_reject_callback'})
        return self.pool.get('confirm.message').open(cr, uid, ids, ctx)

    def action_reject_callback(self, cr, uid, ids, message, context=None):
        #return self.to_state(cr, uid, ids, context.get('state_to'), context=context, reject_message=message)
        #call workflow process
        signal = '%s-%s'%(context.get('state_from'), context.get('state_to'))
        signal = self.REJECT_SIGNALS.get(signal)
        wkf_service = netsvc.LocalService("workflow")
        state_to = context.get('state_to')
        for so_id in ids:
            if state_to == 'draft':
                wkf_service.trg_delete(uid, 'sale.order', so_id, cr)
                wkf_service.trg_create(uid, 'sale.order', so_id, cr)
                self.to_state(cr, uid, ids, 'draft', context=context)
            else:
                wkf_service.trg_validate(uid, 'sale.order', so_id, signal, cr)
        #update message
        return self.write(cr, uid, ids, {'reject_message':message}, context=context)