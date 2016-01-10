# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2012 OpenERP S.A. (<http://openerp.com>).
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

import threading
from openerp import pooler
from openerp.tools import mail
from openerp import SUPERUSER_ID
from openerp.osv import osv
from openerp.modules.registry import RegistryManager
from datetime import datetime
import time
import pytz
import logging
from openerp.tools import resolve_attr 
from openerp.osv import fields
from pynum2word import num2word_EN

_logger = logging.getLogger(__name__)

def dtstr_utc2local(cr, uid, dt_str, context=None):
    '''
    @param dt_str: UTC datetime string  of DEFAULT_SERVER_DATETIME_FORMAT format
    @return: Local(context['tz']) datetime string of DEFAULT_SERVER_DATETIME_FORMAT format
    '''
    dt_obj = datetime.strptime(dt_str, DEFAULT_SERVER_DATETIME_FORMAT)
    dt_obj = context_timestamp(cr, uid, dt_obj, context) 
    return datetime.strftime(dt_obj, DEFAULT_SERVER_DATETIME_FORMAT)

def dtstr_local2utc(cr, uid, dt_str, context=None):
    '''
    @param dt_str: Local(context['tz']) datetime string  of DEFAULT_SERVER_DATETIME_FORMAT format
    @return: UTC datetime string of DEFAULT_SERVER_DATETIME_FORMAT format
    '''
    dt_obj = datetime.strptime(dt_str, DEFAULT_SERVER_DATETIME_FORMAT)
    dt_obj = utc_timestamp(cr, uid, dt_obj, context) 
    return datetime.strftime(dt_obj, DEFAULT_SERVER_DATETIME_FORMAT)

def context_timestamp(cr, uid, timestamp, context=None):
    '''
    Convert utc timestamp to timestamp at TZ
    @param timestamp: UTC time
    @return: local time at TZ 
    '''
    return fields.datetime.context_timestamp(cr, uid, timestamp, context=context)    
                            
def utc_timestamp(cr, uid, timestamp, context=None):
    """Returns the given client's timestamp converted to utc.

       :param datetime timestamp: local datetime value (expressed in LOCAL)
                                  to be converted to the utc
       :param dict context: the 'tz' key in the context should give the
                            name of the User/Client timezone (otherwise
                            uid's tz will be used)
       :rtype: datetime
       :return: timestamp converted to timezone-aware datetime in UTC
    """
    assert isinstance(timestamp, datetime), 'Datetime instance expected'
    if context and context.get('tz'):
        tz_name = context['tz']  
    else:
        registry = RegistryManager.get(cr.dbname)
        tz_name = registry.get('res.users').read(cr, SUPERUSER_ID, uid, ['tz'])['tz']
    if tz_name:
        try:
            utc = pytz.timezone('UTC')
            context_tz = pytz.timezone(tz_name)
            context_timestamp = context_tz.localize(timestamp, is_dst=False) # UTC = no DST
            return context_timestamp.astimezone(utc)
        except Exception:
            _logger.debug("failed to compute context/client-specific timestamp, "
                          "using the UTC value",
                          exc_info=True)
    return timestamp
    
def email_send_template(cr, uid, ids, email_vals, context=None):
    if 'email_template_name' in email_vals:
        threaded_email = threading.Thread(target=_email_send_template, args=(cr, uid, ids, email_vals, context))
        threaded_email.start()
    return True
def _email_send_template(cr, uid, ids, email_vals, context=None):       
    pool =  pooler.get_pool(cr.dbname)
    #As this function is in a new thread, i need to open a new cursor, because the old one may be closed
    new_cr = pooler.get_db(cr.dbname).cursor()
    #send email by template
    if 'email_template_name' in email_vals:
        email_tmpl_obj = pool.get('email.template')
        #check email user 
        if 'email_user_id' in email_vals:
            assignee = pool.get('res.users').browse(new_cr, uid, email_vals['email_user_id'], context=context)
            #only send email when user have email setup
            if not assignee.email:
                return False
        tmpl_ids = email_tmpl_obj.search(new_cr, uid, [('name','=',email_vals['email_template_name'])])
        if tmpl_ids:
            for id in ids:
                email_tmpl_obj.send_mail(new_cr, uid, tmpl_ids[0], id, force_send=True, context=context)
    #close the new cursor
    new_cr.close()
    return True
'''
            #generate the attachments by PDF report
            attachments = []
            report_name = 'Employee Welcome Checklist'
            report_service = netsvc.LocalService('report.hr.welcome.checklist')
            rpt_emp_ids = [emp.id for emp in emp_ids]            
            (result, format) = report_service.create(cr, uid, rpt_emp_ids, {'model': 'hr.employee'}, context)
            ext = "." + format
            if not report_name.endswith(ext):
                report_name += ext
            attachments.append((report_name, result))
'''
def email_send_group(cr, uid, email_from, email_to, subject, body, email_to_group_id=False, email_cc=None, attachments=None, context=None):
    if email_from and (email_to or email_to_group_id):
        threaded_email = threading.Thread(target=_email_send_group, args=(cr, uid, email_from, email_to, subject, body, email_to_group_id, email_cc, attachments, context))
        threaded_email.start()
    return True

def _email_send_group(cr, uid, email_from, email_to, subject, body, email_to_group_ids=False, email_cc=None, attachments=None, context=None):
    pool =  pooler.get_pool(cr.dbname)
    new_cr = pooler.get_db(cr.dbname).cursor()
    emails = []
    if email_to: 
        if isinstance(email_to, type(u' ')):
            emails.append(email_to)
        else:
            emails += email_to
    if email_to_group_ids: 
        #get the group user's addresses by group id
        group_obj = pool.get("res.groups")
        if not isinstance(email_to_group_ids, (list, int, long)):
            email_to_group_ids = long(email_to_group_ids)
        #we can use SUPERUSER_ID to ignore the record rule for res_users and res_partner,  the email should send to all users in the group.
#        group = group_obj.browse(new_cr,SUPERUSER_ID,email_to_group_id,context=context)
        if isinstance(email_to_group_ids, (int, long)):
            email_to_group_ids = [email_to_group_ids]
        groups = group_obj.browse(new_cr,uid,email_to_group_ids,context=context)
        emails = []
        for group in groups:
            emails += [user.email for user in group.users if user.email]
    if emails:
        #remove duplicated email address
        emails = list(set(emails))
        email_ccs = []
        if email_cc: 
            if isinstance(email_cc, type(u' ')):
                email_ccs.append(email_cc)
            else:
                email_ccs += email_cc
        mail.email_send(email_from, emails, subject, body, email_cc=email_ccs, attachments=attachments)
        
    #close the new cursor
    new_cr.close()        
    return True    

def email_notify(cr, uid, obj_name, obj_ids, actions, action, subject_fields = None, email_to = None, context=None, **kwargs):
    '''
    @param param:obj_name the model name that related to email, 'hr.holiday'
    @param param:object ids list, [1,2,3...]
    @param param:actions, one dict that define the action name and related message and groups
    actions = {'confirmed':{'msg':'need your approval','groups':['metro_purchase.group_pur_req_checker']},
                  'approved':{'msg':'approved, please issue PO','groups':['metro_purchase.group_pur_req_buyer']},
                  'rejected':{'msg':'was rejected, please check','groups':[]},
                  'in_purchase':{'msg':'is in purchasing','groups':[],},
                  'done':{'msg':'was done','groups':[]},
                  'cancel':{'msg':'was cancelled','groups':[]},
                  }  
    @param param: optional, subject_fields, one list that will generated the subject, if missing then user object.name
    @param email_to:optional, email to addresss
    '''
    pool =  pooler.get_pool(cr.dbname)
    model_obj = pool.get('ir.model.data')
    obj_obj = pool.get(obj_name)
    if actions.get(action,False):
        msg = actions[action].get('msg')
        group_params = actions[action].get('groups')
        send_to_creator = False
        #email to groups
        email_group_ids = []
        for group_param in group_params:
            grp_data = group_param.split('.')
            #if there is a group named 'creator', then it means send the email to order creator
            if grp_data[0] == 'creator':
                send_to_creator = True
                continue                
            email_group_ids.append(model_obj.get_object_reference(cr, uid, grp_data[0], grp_data[1])[1])
        for order in obj_obj.browse(cr, uid, obj_ids, context=context):
            #email messages      
            subject_sub = ""       
            if not subject_fields:
                subject_sub = order._description
            else:
                for field in subject_fields:
                    subject_sub +=  '%s,'%(resolve_attr(order, field),)
            object_desc = obj_obj._description
            if kwargs and kwargs.get('object_desc'):
                object_desc = kwargs.get('object_desc')
            email_subject = '%s: %s %s'%(object_desc, subject_sub, msg)
            email_body = email_subject
            #the current user is the from user
            email_from = pool.get("res.users").read(cr, uid, uid, ['email'],context=context)['email']
            #the special 'creator' on email_to
            if send_to_creator and order.create_uid.email:
                email_to = order.create_uid.email
            #send emails
            email_send_group(cr, uid, email_from, email_to, email_subject,email_body, email_group_ids, context) 

class msg_tool(osv.TransientModel):
    _name = 'msg.tool'
    #msg_vals = {'subject':'111','body':'111222333444555','model':'purchase.order','res_id':1719}
    def send_msg(self, cr, uid, user_ids, msg_vals, unread = False, starred = False, group_ids = None, context=None):
        """ Process the wizard content and proceed with sending the related
            email(s), rendering any template patterns on the fly if needed. """
        if not user_ids and not group_ids:
            return None
        if context is None:
            context = {}        
        if user_ids is None:
            user_ids = []
        #fetch users from group
        if group_ids:
            groups = self.pool.get('res.groups').browse(cr, uid, group_ids, context=context)
            add_user_ids = []
            for group in groups:
                add_user_ids = [u.id for u in group.users]
            user_ids += add_user_ids
        #get partners
        users = self.pool.get('res.users').browse(cr, uid, user_ids, context=context)
        partner_ids = [u.partner_id.id for u in users]
        
        msg_vals['partner_ids'] = partner_ids
        # post the message
        subtype = 'mail.mt_comment'
        msg_id = self.pool.get('mail.thread').message_post(cr, uid, [0], type='comment', subtype=subtype, context=context, **msg_vals)
        upt_vals = {}
        if 'model' in msg_vals:
            upt_vals['model'] = msg_vals['model']
        if 'res_id' in msg_vals:
            upt_vals['res_id'] = msg_vals['res_id']
        if upt_vals:
            self.pool.get('mail.message').write(cr, uid, [msg_id], upt_vals, context=context)
        #set unread and star flag
        if unread:
            for user_id in user_ids:
                self.pool.get("mail.message").set_message_read(cr, user_id, [msg_id], False, context=context)
        if starred:
            for user_id in user_ids:
                self.pool.get("mail.message").set_message_starred(cr, user_id, [msg_id], True, context=context)

        return msg_id
    
    def test_msg(self,cr,uid,ids,context=None):
        (model, mail_group_id) = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'metro_purchase', 'group_pur_req_manager')
        user_ids = [uid,37]
        group_ids=[mail_group_id]      
        msg_vals = {'subject':'Order approve','body':'Please help approve the purchase order','model':'purchase.order','res_id':1719}
        
        msg_tool = self.pool.get('msg.tool')
        msg_id = msg_tool.send_msg(cr, uid, [uid,37],msg_vals,unread=True,starred=True,group_ids=[mail_group_id],context=context)        

        '''
        #fetch users from group
        if group_ids:
            groups = self.pool.get('res.groups').browse(cr, uid, group_ids, context=context)
            add_user_ids = []
            for group in groups:
                add_user_ids = [u.id for u in group.users]
            user_ids += add_user_ids
        #get partners
        users = self.pool.get('res.users').browse(cr, uid, user_ids, context=context)
        partner_ids = [u.partner_id.id for u in users]
        msg_vals['partner_ids'] = partner_ids
               
        msg_id = self.pool.get('purchase.order').message_post(cr, uid, 1719, **msg_vals)
                        
        #set unread and star flag
        for user_id in user_ids:
            self.pool.get("mail.message").set_message_read(cr, user_id, [msg_id], False, context=context)
        for user_id in user_ids:
            self.pool.get("mail.message").set_message_starred(cr, user_id, [msg_id], True, context=context)
        '''
                                        
        print msg_id    
        

def field_get_file(self, cr, uid, ids, field_names, args, context=None):
    result = dict.fromkeys(ids, {})
    attachment_obj = self.pool.get('ir.attachment')
    for obj in self.browse(cr, uid, ids):
        for field_name in field_names:
            result[obj.id][field_name] = None
            file_ids = attachment_obj.search(
                cr, uid, [('name', '=', field_name),
                          ('res_id', '=', obj.id),
                          ('res_model', '=', self._name)],context=context)
            if file_ids:
                result[obj.id][field_name] = attachment_obj.browse(cr, uid, file_ids[0]).datas
    return result

def field_set_file(self, cr, uid, id, field_name, value, args, context=None):
    attachment_obj = self.pool.get('ir.attachment')
    file_ids = attachment_obj.search(
        cr, uid, [('name', '=', field_name),
                  ('res_id', '=', id),
                  ('res_model', '=', self._name)])
    file_id = None
    if file_ids:
        file_id = file_ids[0]
        attachment_obj.write(cr, uid, file_id, {'datas': value})
    else:
        file_id = attachment_obj.create(
            cr, uid, {'name':  field_name,
                      'res_id': id,
                      'type': 'binary',
                      'res_model':self._name,
                      'datas': value})    
    return file_id        

from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

def deal_args_dt(cr, uid, obj,args,dt_fields,context=None):  
    new_args = []
    for arg in args:
        fld_name = arg[0]
        if fld_name in dt_fields:
            fld_operator = arg[1]
            fld_val = arg[2]
            fld = obj._columns.get(fld_name)
            if fld._type == 'datetime':
                if len(fld_val) == 10:
                    '''
                    ['date','=','2013-12-12] only supply the date part without time
                    ''' 
                    dt_val = datetime.strptime(fld_val + ' 00:00:00', DEFAULT_SERVER_DATETIME_FORMAT)
                    dt_val = utc_timestamp(cr, uid, dt_val, context=context)
                    fld_val = dt_val.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                if fld_val.endswith('00:00'):
                    if fld_operator == "=":
                        '''
                        ['date','=','2013-12-12 16:00:00'] the '16' was generated for the timezone
                        the user inputed is '2013-12-13 00:00:00', subtract 8 hours, then get this value
                        ''' 
                        time_start = [fld_name,'>=',fld_val]
                        time_obj = datetime.strptime(fld_val,DEFAULT_SERVER_DATETIME_FORMAT)
                        time_obj += relativedelta(days=1)
                        time_end = [fld_name,'<=',time_obj.strftime(DEFAULT_SERVER_DATETIME_FORMAT)]
                        new_args.append(time_start)
                        new_args.append(time_end)
                    elif fld_operator == "!=":
                        time_start = [fld_name,'<',fld_val]
                        time_obj = datetime.strptime(fld_val,DEFAULT_SERVER_DATETIME_FORMAT)
                        time_obj += relativedelta(days=1)
                        time_end = [fld_name,'>',time_obj.strftime(DEFAULT_SERVER_DATETIME_FORMAT)]
                        new_args.extend(['|', '|', [fld_name,'=',False], time_start, time_end])                    
                    else:
                        new_args.append(arg)
                else:
                    new_args.append(arg)
        else:
            new_args.append(arg) 
    #TODO: refer fields.datetime.context_timestamp() to deal with the timezone
    #TODO: Improve the code in line#1014@osv/expression.py to handel the timezone for the datatime field:
    '''
                if field._type == 'datetime' and right and len(right) == 10:
                    if operator in ('>', '>='):
                        right += ' 00:00:00'
                    elif operator in ('<', '<='):
                        right += ' 23:59:59'
                    push(create_substitution_leaf(leaf, (left, operator, right), working_model))    
    '''
    return new_args

def set_seq(cr, uid, data, table_name=None, context=None):
    '''
    Set the new data sequence in the related model's create() or write method.
    @param data: the dict data will be create 
    @param table_name: table name
    '''
    if not data or data.get('sequence') and data['sequence'] > 0: 
        return
    #get max seq in db
    cr.execute('select max(sequence) as seq from %s'%(table_name))
    seq_max = cr.fetchone()[0]
    if seq_max is None:
        seq_max = 0
    seq_max += 1
    data['sequence'] = seq_max
        
def set_seq_o2m(cr, uid, lines, m_table_name=None, o_id_name=None, o_id=None, context=None):
    '''
    Set the one2many list sequence in the 'one' in 'one2many' model's create() or write method.
    @param lines: one list that contains list of line of one2many lines  
    @param m_table_name: 'many' table name
    @param o_id_name: field name of 'many' table related to 'one' table
    @param o_id:'one' id value of field 'o_id_name'   
    '''
    '''
    line's format in lines:
    **create**:[0,False,{values...}]
    **write**:[1,%so_line_id%,{values...}]
    **delete**:[2, %so_line_id%, False]
    **no change**:[4, %so_line_id%, False]
    '''
    if not lines: 
        return
    #get max seq in db
    seq_max = 0
    if m_table_name and o_id_name and o_id:
        cr.execute('select max(sequence) as seq from %s where %s=%s'%(m_table_name, o_id_name, o_id))
        seq_max = cr.fetchone()[0]
        if seq_max is None:
            seq_max = 0
    #get max seq from saving data
    lines_deal = []
    for line in lines:
        data = line[2]
        if data and data.get('sequence') and data['sequence'] and seq_max < data['sequence']:
            seq_max = data['sequence']
        elif line[0] == 0:
            lines_deal.append(line)
    #generate the new seq
    for line in lines_deal:
        seq_max += 1
        line[2]['sequence'] = seq_max
        
def set_resu_warn(res, message, title=None):
    if not message: return
    #set the return warning messages
    warning = res.get('warning',{})
    if warning and warning.get('message'):
        warning['message'] = '%s\n%s'%(warning['message'], message)
    else:
        warning = {
                   'title': title or 'Warning',
                   'message' : message
                }
    res.update({'warning':warning})        
    
def number2words_en_upper(num):
    return num2word_EN.to_card(num).upper()

def number2words_en_upper2(num):
    #remove the ','
    return number2words_en_upper(num).replace(',', '')