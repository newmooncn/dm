# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import time
from openerp.osv import fields, osv
from openerp.osv.orm import browse_record, browse_null
from openerp.tools.translate import _
import datetime
import openerp.tools as tools

class task_group(osv.osv_memory):
    _inherit = "task.group"
    _columns = {
        'team_leader': fields.char('Team Leader', size=64, required=False),
        'team_members': fields.char('Team Members', size=1024, required=False),
    }
class task_print(osv.osv_memory):
    _inherit = "task.print"
    _columns = {
        #add 'by_team' type
        'print_type': fields.selection([('by_assignee','Task List By Assignee'),
                                        ('by_employee','Task List By Employee'),
                                        ('by_team','Task List By Team')],
                                       'Type', required=True, select=False),        
    }
    
    def default_get(self, cr, uid, fields_list, context=None):
        values = super(task_print,self).default_get(cr, uid, fields_list, context)
        if context.get('mfg_daily'):
            today = datetime.datetime.utcnow().strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
            values.update({'print_type':'by_team','task_day':today,'task_type':'mfg'})
        return values
            
    def _get_team_name(self, cr, uid, task, context=None):
        dept_name = 'No Team'
        if task.dept_id:
            dept_name = task.dept_id.name    
        return dept_name
    #call by do_print()
    def _group_name_func(self, print_type):
        group_name_func = super(task_print, self)._group_name_func(print_type)
        if print_type == 'by_team':
            group_name_func = self._get_team_name
        return group_name_func
    #call by do_print(), to put the special values of group
    def _update_group_vals(self, group_vals, task_print, task):
        group_vals = super(task_print,self)._update_group_vals(group_vals, task_print, task)
        #Add the team fields for the by_team report
        if task_print.print_type == 'by_team' and task.dept_id:
            team_leader = task.dept_mgr_id and task.dept_mgr_id.name
            team_leader_id = task.dept_mgr_id and task.dept_mgr_id.id or 0
            team_members = ''
            if task.emp_ids:
                team_members = [emp.name for emp in task.emp_ids if emp.id != team_leader_id]
                team_members = ', '.join(team_members)
            group_vals.update({'team_leader':team_leader,'team_members':team_members})
        return group_vals
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
