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
from openerp.osv import fields,osv
from openerp.addons.base_status.base_stage import base_stage
from openerp.tools.translate import _
from openerp.addons.project import project as project_super
from openerp.addons.dm_base import utils
   
'''
Sending email to the assignee when creating and writing
'''    
class project_task(base_stage, osv.osv):
    _inherit = "project.task" 
    
    def create(self, cr, uid, vals, context=None):
        new_id = super(project_task,self).create(cr, uid, vals ,context)
        if self.browse(cr,uid,new_id,context=context).project_type != 'mfg':
            if 'user_id' in vals:
                email_vals = {'email_user_id':vals['user_id'],'email_template_name':'project_task_assignee'}
                utils.email_send_template(cr, uid, [new_id], email_vals, context)
        return new_id
            
    def write(self, cr, uid, ids, vals, context=None):
        resu = super(project_task,self).write(cr, uid, ids, vals ,context)
        if 'user_id' in vals:
            email_vals = {'email_user_id':vals['user_id'],'email_template_name':'project_task_assignee'}
            utils.email_send_template(cr, uid, ids, email_vals, context)
        return resu     