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
    
_PROJ_TYPES = [('simple','Simple'),('software','Software'),('engineer','Engineering'),('gtd','GTD'),('mfg','Manufacture')]
'''
1.Add 'type' field to extend the project's usage
'''
class project_project(osv.osv):
    _inherit = 'project.project'
    _columns = {
        'project_type': fields.selection(_PROJ_TYPES,string='Type',),
    }
    
    def _get_default_states(self, cr, uid, context):
        domain = []
        if context and context.get('default_project_type'):
            domain += ['|',('project_type','=',context['default_project_type'])]
        domain +=  ['|',('project_type','=','all'),('case_default','=',1)]
        ids = self.pool.get('project.task.type').search(cr, uid, domain, context=context)
        return ids
    
    _defaults = {'project_type':'simple',
                 'type_ids': _get_default_states,
                 }
    
    def onchange_project_type(self,cr, uid, ids, project_type, context=None):
        if not project_type:
            return {}
        domain =  ['|','|',('project_type','=',project_type),('project_type','=','all'), ('case_default','=',1)]
        ids = self.pool.get('project.task.type').search(cr, uid, domain, context=context)
        return {'value':{'type_ids': ids}}
   
'''
Imrpove the group by state, to add the 'project_type' domain to return all the states related to the project type
'''    
class project_task(base_stage, osv.osv):
    _inherit = "project.task"     
    _columns = {
        'project_type': fields.related('project_id', 'project_type', type='selection', 
                                       selection=_PROJ_TYPES, 
                                       string='Project Type', select=1),
    }
            
    def default_get(self, cr, uid, fields_list, context=None):
        resu = super(project_task,self).default_get(cr, uid, fields_list, context=context)
        if not resu.get('project_id') and context.get('default_project_type',False) == 'simple':
            result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'dmp_project', 'project_simple')
            resu.update({'project_id':result[1]})
        return resu
    
    def fields_get(self, cr, uid, allfields=None, context=None, write_access=True):
        resu = super(project_task,self).fields_get(cr, uid, allfields,context,write_access)
        #set  the 'project_id' domain dynamically by the default_project_type
        default_project_type = context and context.get('default_project_type', False) or False
        if resu.has_key('project_id') and default_project_type:            
            project_ids = self.pool.get('project.project').search(cr, uid, [('project_type','=',default_project_type)], context=context)
            resu['project_id']['domain'] = [('id','in',project_ids)]
        return resu 
         
    def _resolve_project_type_from_context(self, cr, uid, context=None):
        """ Returns the project_type from the type context
            key. Returns None if it cannot be resolved.
        """
        if context is None:
            context = {}
        return context.get('default_project_type')   
     
    def _read_group_stage_ids(self, cr, uid, ids, domain, read_group_order=None, access_rights_uid=None, context=None):
        stage_obj = self.pool.get('project.task.type')
        order = stage_obj._order
        access_rights_uid = access_rights_uid or uid
        if read_group_order == 'stage_id desc':
            order = '%s desc' % order
        search_domain = []
        project_id = self._resolve_project_id_from_context(cr, uid, context=context)
        if project_id:
            search_domain += ['|', ('project_ids', '=', project_id)]
        search_domain += [('id', 'in', ids)]
        # johnw, 07/22/2014, retrieve type from the context (if set: choose 'type' or 'both')
        #begin                
        project_type = self._resolve_project_type_from_context(cr, uid, context=context)
        if type:
            type_domain = ['|', ('project_type', '=', project_type), ('project_type', '=', 'all')]
            search_domain.insert(0, '|')
            search_domain += type_domain
        #end
        stage_ids = stage_obj._search(cr, uid, search_domain, order=order, access_rights_uid=access_rights_uid, context=context)
        result = stage_obj.name_get(cr, access_rights_uid, stage_ids, context=context)
        # restore order of the search
        result.sort(lambda x,y: cmp(stage_ids.index(x[0]), stage_ids.index(y[0])))
    
        fold = {}
        for stage in stage_obj.browse(cr, access_rights_uid, stage_ids, context=context):
            fold[stage.id] = stage.fold or False
        return result, fold 
    
    _group_by_full = {
        'stage_id': _read_group_stage_ids,
    }     
    
class project_task_type(osv.osv):
    _inherit = 'project.task.type'
    _columns = {
        'project_type': fields.selection(_PROJ_TYPES+[('all','All')],string='Type',),
    }      
    _defaults={'project_type':'simple'}