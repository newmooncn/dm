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
from osv import fields,osv,orm
from openerp import netsvc

class sale_order(osv.osv):
    _inherit="sale.order"
    
    def _check_groups(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        fld_groups = {
            'is_sale': 'base.group_sale_salesman',
            'is_eng_mgr': 'dmp_sale_workflow.group_engineer_manager',
            'is_plan_mgr': 'dmp_sale_workflow.group_mrp_plan_manager',
            'is_pur_mgr': 'purchase.group_purchase_manager',
            'is_top_mgr': 'dmp_sale_workflow.group_top_manager',
            'is_sale_mgr': 'base.group_sale_manager',
        }
        #check group
        user_obj = self.pool.get('res.users')
        for field_name, group_ext_id in fld_groups.items():
            fld_groups[field_name] = user_obj.has_group(cr, uid, group_ext_id)
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = fld_groups
        return res    
    _STATES_EDITABLE = {'sale_confirmed': [('readonly', False)], 
                        'engineer_confirmed': [('readonly', False)], 
                        'plan_confirmed': [('readonly', False)], 
                        'purchase_confirmed': [('readonly', False)], 
                        'top_confirmed': [('readonly', False)]}
    _columns={
            'client_order_ref': fields.char('Customer Reference', size=64, 
                                            readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
              
          'state': fields.selection([
            ('draft', 'Draft Quotation'),
            ('sent', 'Quotation Sent'),
            ('sale_confirmed', 'Sale Confirmed'),
            ('engineer_confirmed', 'Engineering Confirmed'),
            ('plan_confirmed', 'Planner Confirmed'),
            ('purchase_confirmed', 'Purchase Confirmed'),
            ('top_confirmed', 'Top Confirmed'),
            ('progress', 'Customer Confirmed'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
#            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('shipping_except', 'Shipping Exception'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ], 'Status', readonly=True,help="Gives the status of the quotation or sales order.\
              \nThe exception status is automatically set when a cancel operation occurs \
              in the invoice validation (Invoice Exception) or in the picking list process (Shipping Exception).\nThe 'Waiting Schedule' status is set when the invoice is confirmed\
               but waiting for the scheduler to run on the order date.", select=True),
            #for sale confirm
            'is_sale': fields.function(_check_groups, type='boolean', string='Is Sale', multi='_check_groups'),
            'date_expect': fields.date('Expect Date', readonly=True, states=_STATES_EDITABLE),
            'date_promise': fields.date('Promise Date', readonly=True, states=_STATES_EDITABLE),
            'date_effected': fields.date('Effected Date', readonly=True, states=_STATES_EDITABLE),
            'sale_req_user_id': fields.many2one('res.users','Sales Requester', readonly=True),
            'sale_req_date': fields.date('Sales Request Date', readonly=True),     
            'sale_req_note': fields.char('Review Notes', size=218, readonly=True, states=_STATES_EDITABLE),                 
            #for engineer confirm
            'is_eng_mgr': fields.function(_check_groups, type='boolean', string='Is Engineer Manager', multi='_check_groups'),
            'bom_confirmed': fields.boolean('BOM Confirmed', readonly=True, states=_STATES_EDITABLE),
            'pcb_model': fields.boolean('PCB Model', readonly=True, states=_STATES_EDITABLE),
            'need_trial_mfg': fields.boolean('Trial Manufacture', readonly=True, states=_STATES_EDITABLE),
            'have_spec': fields.boolean('Have Specification', readonly=True, states=_STATES_EDITABLE),
            'user_ref_sample': fields.boolean('User Reference Sample', readonly=True, states=_STATES_EDITABLE),
            'eng_user_id': fields.many2one('res.users','Approve User', readonly=True),
            'eng_date': fields.date('Approve Date', readonly=True),     
            'eng_note': fields.char('Review Notes', size=218, readonly=True, states=_STATES_EDITABLE),
            #for plan confirm
            'is_plan_mgr': fields.function(_check_groups, type='boolean', string='Is Plan Manager', multi='_check_groups'),
            'mfg_order_no': fields.char('MFG Order#', size=128, readonly=True, states=_STATES_EDITABLE),
            'date_mfg_exp_start': fields.date('Plan Start Date', readonly=True, states=_STATES_EDITABLE),
            'date_mfg_exp_finish': fields.date('Plan Finish Date', readonly=True, states=_STATES_EDITABLE),
            'plan_user_id': fields.many2one('res.users','Approve User', readonly=True),
            'plan_date': fields.date('Approve Date', readonly=True),     
            'plan_note': fields.char('Review Notes', size=218, readonly=True, states=_STATES_EDITABLE),          
            #for purchase confirm
            'is_pur_mgr': fields.function(_check_groups, type='boolean', string='Is Purchase Manager', multi='_check_groups'),
            'date_pur_order': fields.date('Plan Purchase Order Date', readonly=True, states=_STATES_EDITABLE),
            'date_pur_receive': fields.date('Plan Receiving Date', readonly=True, states=_STATES_EDITABLE),
            'pur_user_id': fields.many2one('res.users','Approve User', readonly=True),
            'pur_date': fields.date('Approve Date', readonly=True),     
            'pur_note': fields.char('Review Notes', size=218, readonly=True, states=_STATES_EDITABLE),
            #for top confirm
            'is_top_mgr': fields.function(_check_groups, type='boolean', string='Is Top Manager', multi='_check_groups'),
            'date_top_receive': fields.date('Plan Purchase Order Date', readonly=True, states=_STATES_EDITABLE),
            'date_top_finish': fields.date('Plan Receiving Date', readonly=True, states=_STATES_EDITABLE),
            'date_top_deliver': fields.date('Plan Deliver Date', readonly=True, states=_STATES_EDITABLE),
            'top_user_id': fields.many2one('res.users','Approve User', readonly=True),
            'top_date': fields.date('Approve Date', readonly=True),
            'top_advice': fields.selection([('to_plan','Plan Recheck'),
                                            ('to_pur','Purchase Recheck'),
                                            ('final','Final Check')],'Top Advice', 
                                           readonly=True, states=_STATES_EDITABLE),
            'top_note': fields.char('Review Notes', size=218, readonly=True, states=_STATES_EDITABLE),
            
            'is_sale_mgr': fields.function(_check_groups, type='boolean', string='Is Sale Manager', multi='_check_groups'),
              
            #for customer confirm
    }
    
    def copy(self, cr, uid, id, default=None, context=None):
        default.update({
            'sale_req_user_id': None,
            'sale_req_date': None,            
            #for engineer confirm
            'eng_user_id': None,
            'eng_date': None,
            #for plan confirm
            'mfg_order_no': None,
            'plan_user_id': None,
            'plan_date': None,    
            #for purchase confirm
            'pur_user_id': None,
            'pur_date': None,
            #for top confirm
            'top_user_id': None,
            'top_date': None,
            'top_advice': None,
            })
        return super(sale_order,self).copy(cr, uid, id, default, context)
    STATE_APPROVE_FLDS = {'sale_confirmed':{'fld_user':'sale_req_user_id','fld_date':'sale_req_date',
                                            'mail_group':'dmp_sale_workflow.group_engineer_manager','mail_action':u'研发审核确认'},
                          'engineer_confirmed':{'fld_user':'eng_user_id','fld_date':'eng_date',
                                            'mail_group':'dmp_sale_workflow.group_mrp_plan_manager','mail_action':u'计划审核确认'},
                          'plan_confirmed':{'fld_user':'plan_user_id','fld_date':'plan_date',
                                            'mail_group':'purchase.group_purchase_manager','mail_action':u'采购审核确认'},
                          'purchase_confirmed':{'fld_user':'pur_user_id','fld_date':'pur_date',
                                            'mail_group':'dmp_sale_workflow.group_top_manager','mail_action':u'厂部审核确认'},
                          'top_confirmed':{'fld_user':'top_user_id','fld_date':'top_date',
                                            'mail_group':'base.group_sale_manager','mail_action':u'客户确认'},
                          }

    def to_state(self,cr,uid,ids,new_state,context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        vals = {'state':new_state}
        old_state = self.read(cr, uid, ids[0], ['state'], context=context)['state']
        if self.STATE_APPROVE_FLDS.get(new_state,False):
            flds = self.STATE_APPROVE_FLDS.get(new_state)
            vals.update({flds['fld_user']:uid, flds['fld_date']:fields.date.today()})
        self.write(cr, uid, ids, vals, context=context)
        #send email to the user group that need do next action
        if self.STATE_APPROVE_FLDS.get(new_state,False):
            flds = self.STATE_APPROVE_FLDS.get(new_state)
            self._msg_notify(cr, uid, ids, flds['mail_action'], [flds['mail_group']],context) 
        #update mfg_order_no
        if new_state == 'engineer_confirmed':
            added_mo_ids = []
            for so in self.browse(cr, uid, ids, context=context):
                mfg_order_no = ''
                date_mfg_exp_start = None
                for soln in so.order_line:
                    if soln.procurement_id \
                            and soln.procurement_id.production_id \
                            and soln.procurement_id.production_id.id not in added_mo_ids:
                        mo = soln.procurement_id.production_id
                        mfg_order_no += (mfg_order_no != '' and ',' or '') + mo.name
                        if not date_mfg_exp_start or date_mfg_exp_start > mo.date_planned:
                            date_mfg_exp_start = mo.date_planned
                        added_mo_ids.append(mo.id)
                if mfg_order_no:
                    self.write(cr, uid, so.id, \
                           {'mfg_order_no':mfg_order_no, 'date_mfg_exp_start':date_mfg_exp_start}, \
                           context=context)
        #top confirm selecting
        if old_state == 'purchase_confirmed':
            #top2plan
            if new_state == 'engineer_confirmed':
                self.write(cr, uid, ids, {'top_advice':'to_plan'}, context=context)
            #top2purchase
            if new_state == 'plan_confirmed':
                self.write(cr, uid, ids, {'top_advice':'to_pur'}, context=context)
            #top_confirmed
            if new_state == 'top_confirmed':
                self.write(cr, uid, ids, {'top_advice':'final'}, context=context)
        
    def _msg_notify(self, cr, uid, ids, action_name, group_params, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            email_group_ids = []
            for group_param in group_params:
                module,group_ext_id = group_param.split('.')
                email_group_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, module, group_ext_id)[1]
                email_group_ids.append(email_group_id)
            if email_group_ids:                    
                email_subject = u'销售单%s提醒'%(action_name) 
                email_body = u'销售单:%s 需要你进行%s'%(order.name,action_name)
                msg_vals = {'subject':email_subject,'body':email_body,'model':'sale.order','res_id':order.id}
                msg_tool = self.pool.get('msg.tool')
                msg_tool.send_msg(cr, uid, None ,msg_vals,unread=True,starred=True,group_ids=email_group_ids,context=context)        

class mrp_production(osv.osv):
    _inherit="mrp.production"
    def _compute_planned_workcenter(self, cr, uid, ids, context=None, mini=False):
        resu = super(mrp_production, self)._compute_planned_workcenter(cr, uid, ids, context, mini) 
        super(mrp_production, self).write(cr, uid, ids, {'date_finished': False})
        return resu