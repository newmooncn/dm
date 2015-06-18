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

class mrp_production(osv.osv):
    _inherit= 'mrp.production'
    
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()
        
    _columns={      
        'state': fields.selection(
            [('draft', 'New'), ('cancel', 'Cancelled'), ('picking_except', 'Picking Exception'), ('approve', 'Approving'), ('confirmed', 'Awaiting Raw Materials'),
                ('ready', 'Ready to Produce'), ('in_production', 'Production Started'), ('done', 'Done')],
            string='Status', readonly=True,
            track_visibility='onchange',
            help="When the production order is created the status is set to 'Draft'.\n\
                If the order is confirmed the status is set to 'Waiting Goods'.\n\
                If any exceptions are there, the status is set to 'Picking Exception'.\n\
                If the stock is available then the status is set to 'Ready to Produce'.\n\
                When the production gets started then the status is set to 'In Production'.\n\
                When the production is over, the status is set to 'Done'."),
        'reject_message': fields.text('Rejection Message', track_visibility='onchange'),          
    }
    
    #call by workflow                      
    def to_state(self,cr,uid,ids,new_state,context=None):
        '''
        Why put this variable here, because if we put the variable as one class level,
        then the translation can not be translate to current user languange, 
        since one class instance will be init only one time and the "_()" function will run one time
        but system may be used by different languange's users         
        ''' 
        EMAIL_ACTIONS = {'approve':{'msg':_('confirmed, need your approval'),'groups':['dmp_base.group_super_manager']},
                         'confirmed':{'msg':_('manager approved'),'groups':['creator']},
                         'ready':{'msg':_('ready'),'groups':['creator']},
                         'approve2draft':{'msg':_('rejected by manager, please do re-checking'),'groups':['creator']}}
                
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        vals = {'state':new_state, 'reject_message':None}
        action = new_state
        #handle the super rejection
        old_state = self.read(cr, uid, ids[0], ['state'], context=context)['state']
        if old_state == 'approve' and new_state == 'draft':
            action = 'approve2draft'
        self.write(cr, uid, ids, vals, context=context)
        #send email to the user group that need do next action
        utils.email_notify(cr, uid, self._name, ids, EMAIL_ACTIONS, action, subject_fields = ['name'], email_to = [], 
                           context=context, object_desc=_('Manufacturing Order'))
          
    REJECT_SIGNALS = {'approve-draft':'approve_reject_draft',}
                                          
    def action_reject(self, cr, uid, ids, context=None):   
        if not context:
            context = {}  
        ctx = dict(context)
        ctx.update({'confirm_title':_('Reason for rejection'),
                    'src_model':self._name,
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
                wkf_service.trg_delete(uid, self._name, so_id, cr)
                wkf_service.trg_create(uid, self._name, so_id, cr)
                self.to_state(cr, uid, ids, 'draft', context=context)
            else:
                wkf_service.trg_validate(uid, 'sale.order', so_id, signal, cr)
        #update message
        return self.write(cr, uid, ids, {'reject_message':message}, context=context)
    
    def action_ready(self, cr, uid, ids, context=None):
        resu = super(mrp_production,self).action_ready(cr, uid, ids, context=context)
        self.to_state(cr,uid,ids,'ready',context=context)
        return resu
        
    def action_confirm(self, cr, uid, ids, context=None):
        resu = super(mrp_production,self).action_confirm(cr, uid, ids, context=context)
        self.to_state(cr,uid,ids,'confirmed',context=context)
        return resu