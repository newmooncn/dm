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
1.Project can not be closed if there are opening tasks
2.When do creation, set the state list by project_type
'''
class project_project(osv.osv):
    _inherit = 'project.project'
    _order = 'id desc'
    
    #add the ID return in the name
    def name_get(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not len(ids):
            return []
        result = []
        for data in self.browse(cr, user, ids, context=context):
            if data.id <= 0:
                result.append((data.id,''))
                continue
            result.append((data.id,'[%s]%s'%(data.id,data.name)))
                          
        return result    
            
    def set_done(self, cr, uid, ids, context=None):        
        if isinstance(ids, (int,long)):
            ids = [ids]
        if context == None:
            context = {}
        #the BOM is required when do project done
        for proj in self.browse(cr, uid, ids, context=context):
            for task in proj.tasks:
                if task.state != 'done':
                    raise osv.except_osv(_('Error!'), _('Project "%s" can not be close, the task "%s" is opening.'%(proj.name,task.name)))
        resu = super(project_project,self).set_done(cr, uid, ids, context) 
        return resu
   

class project_task(base_stage, osv.osv):
    _inherit = "project.task"        
    _order = "sequence, date_start, name, id"
    _columns = {
        'private': fields.boolean("Private"),     
        'daily_date':fields.function(lambda *a,**k:{}, type='date',string="Daily Task Date",),
    }
    #add the ID return in the name
    def name_get(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not len(ids):
            return []
        result = []
        for data in self.browse(cr, user, ids, context=context):
            if data.id <= 0:
                result.append((data.id,''))
                continue
            result.append((data.id,'[%s]%s'%(data.id,data.name)))
                          
        return result
    '''     
    Replaced below code with code in project_simple_view.xml:
    ===========
                    <field name="daily_date" widget="calendar"
                        filter_domain="['|',('date_start','=',False),('date_start','&lt;=', self + ' 23:59:59'),'|',('date_end','=',False),('date_end','&gt;=', self + ' 00:00:00')]"/>
    ===========                       
    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        #deal the 'date' datetime field query
        new_args = deal_args(self,args)
        idx_daily = 0
        args_daily = []
        for arg in new_args:
            #add the category improving
            if arg[0] == 'daily_date':
                args_daily = ['|',['date_start','=',False],['date_start','<=','%s %s'%(arg[2],'23:59:59')],'|',['date_end','=',False],['date_end','>=','%s %s'%(arg[2],'00:00:00')]]
                new_args.pop(idx_daily)
                new_args += args_daily
                break
            idx_daily += 1                           
        #get the search result        
        ids = super(project_task,self).search(cr, user, new_args, offset, limit, order, context, count)
        return ids 
    ''' 
    def unlink(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        for task_state in self.read(cr, uid, ids, ['name','state']):
            if task_state['state'] not in ('cancelled','draft'):
                raise osv.except_osv(_('Error!'), _('Task "%s" can not be delete, only task with Draft&Cancel states can be delete.'%(task_state['name'],)))
        res = super(project_task, self).unlink(cr, uid, ids, context)
        return res     
    
    _group_by_full = {
        'user_id': project_super.task._read_group_user_id,
    }     