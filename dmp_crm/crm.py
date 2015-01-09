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

import time

class res_users(osv.osv):
    _name = 'res.users'
    _inherit = 'res.users'
    _columns = {
			'own_crm_sections': fields.one2many('crm.case.section','user_id','My Own Teams'),
			'parent_crm_sections': fields.many2many('crm.case.section', 'sale_member_rel', 'member_id', 'section_id', 'My Parent Teams'),		
		}
    
class crm_lead(osv.osv):
    _inherit="crm.lead"    
    _columns={
        'phonecall_ids': fields.one2many('crm.phonecall', 'opportunity_id',string='Callings', ),
        'contact_log_ids': fields.many2many('contact.log', 'oppor_contact_log_rel','oppor_id','log_id',string='Contact Logs', )                      
    }
class contact_log(osv.osv):
    _name = 'contact.log'
    _description="Contact Log"
    _order = "date desc"
    _columns = {
        'type_id': fields.many2one('contact.log.type','Type',required=True),
        'name': fields.char('Summary', size=64,required=True),
        'date': fields.datetime('Contact Date',required=True),
        'person': fields.char('Person',size=32,required=False),
        'duration': fields.float('Hours'),
        'description': fields.text('Description',required=True),   
    }
    '''
    the 'op_name','op_contact_name' comes from the view xml field like below:
    field name="contact_log_ids" widget="one2many_list" context="{'op_name':name,'op_contact_name':contact_name}"/>
    ''' 
    _defaults={'name':lambda s, cr, uid, c: c.get('op_name'),
               'person':lambda s, cr, uid, c: c.get('op_contact_name'),
               'date': lambda *args: time.strftime('%Y-%m-%d %H:%M:%S'),}   
        
class contact_log_type(osv.osv):
    _name = "contact.log.type"
    _description = "Types"
    _columns = {
        'name': fields.char('Type Name', size=64, required=True),
        'active': fields.boolean('Active'),
    }
    _defaults = {
        'active': lambda *a: 1,
    }        