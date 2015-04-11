# -*- encoding: utf-8 -*-
from openerp.osv import fields,osv
from openerp.tools.translate import _
from openerp import netsvc
import time
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from lxml import etree
from openerp.addons.mrp.mrp import rounding as mrp_rounding
from openerp import tools
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp

class mrp_production(osv.osv):
    _inherit = 'mrp.production'
    _columns = {
        'priority': fields.selection([('4','Very Low'), ('3','Low'), ('2','Medium'), ('1','Important'), ('0','Very important')], 'Priority', 
                                     select=True,  readonly=False, states=dict.fromkeys(['cancel', 'done'], [('readonly', True)])),
    }
    _defaults={'priority': '2'}
    
    #add the priority auto setting logic
    def write(self, cr, uid, ids, vals, context=None, update=True, mini=True):
        resu = super(mrp_production, self).write(cr, uid, ids, vals, context=context,update=update,mini=mini)        
        if 'priority' in vals.keys():
            self.set_priority(cr,uid,ids,vals['priority'],context)
        return resu
    
    def set_priority(self,cr,uid,ids,priority,context=None):
        if context is None:
            context = {}
        #set all of the sub manufacture orders, work orders, MFG tasks priority
        set_ids = []
        wo_ids = []
        for mo in self.browse(cr,uid,ids,context=context):
            if mo.state in ('cancel','done'):
                continue
            set_ids.append(mo.id)
            wo_ids += [wo.id for wo in mo.workcenter_lines]
        if set_ids:
            #update manufacture order
            cr.execute("update mrp_production set priority=%s where id  = ANY(%s)", (priority, (set_ids,)))
            #update manufacture order
            self.pool.get('mrp.production.workcenter.line').set_priority(cr, uid, wo_ids, priority, context=context)  
            
    def _action_compute_lines(self, cr, uid, ids, properties=None, context=None):
        resu = super(mrp_production, self)._action_compute_lines(cr, uid, ids, properties=properties, context=context) 
        #update the priority of work order&tasks
        workcenter_line_obj = self.pool.get('mrp.production.workcenter.line')
        wo_task_obj = self.pool.get('project.task')
        for production in self.browse(cr, uid, ids, context=context):
            wo_ids = workcenter_line_obj.search(cr, uid, [('production_id','=',production.id)],context=context)
            if wo_ids:
                workcenter_line_obj.write(cr, uid, wo_ids, {'priority':production.priority}, context=context)
                wo_task_ids = wo_task_obj.search(cr, uid, [('workorder_id','in',wo_ids)], context=context)
                if wo_task_ids:
                    wo_task_obj.write(cr, uid, wo_task_ids, {'priority':production.priority, 'user_id':production.task_mgr_id.id}, context=context)
        return resu
    
class mrp_production_workcenter_line(osv.osv):
    _inherit = 'mrp.production.workcenter.line'
    _columns = {
        'priority': fields.selection([('4','Very Low'), ('3','Low'), ('2','Medium'), ('1','Important'), ('0','Very important')], 'Priority', select=True),
    }
    _defaults = {'priority': '2'}
    
    #add the 'update=True, mini=True' inhreited from mrp_operations.mrp_production_workcenter_line
    def write(self, cr, uid, ids, vals, context=None, update=True):
        resu = super(mrp_production_workcenter_line, self).write(cr, uid, ids, vals, context=context,update=update)        
        if 'priority' in vals.keys():
            self.set_priority(cr,uid,ids,vals['priority'],context)
        return resu
    
    def set_priority(self,cr,uid,ids,priority,context=None):
        if context is None:
            context = {}
        #set all of the sub manufacture orders, work orders, MFG tasks priority
        set_ids = []
        task_ids = []
        for wo in self.browse(cr,uid,ids,context=context):
            if wo.state in ('cancel','done'):
                continue
            set_ids.append(wo.id)
            task_ids += [task.id for task in wo.task_ids if task.state not in ('cancelled','done')]
        if set_ids:
            #update work order
            cr.execute("update mrp_production_workcenter_line set priority=%s where id  = ANY(%s)", (priority, (set_ids,)))
            #update manufacture order
            self.pool.get('project.task').write(cr, uid, task_ids, {'priority':priority}, context=context)