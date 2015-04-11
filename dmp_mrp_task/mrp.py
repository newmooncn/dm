# -*- encoding: utf-8 -*-
from openerp.osv import fields,osv
from openerp.addons.base_status.base_stage import base_stage

class mrp_production(osv.osv):
    _inherit = 'mrp.production'
    _columns = {
        'task_mgr_id': fields.many2one('res.users', 'Task Manager'),                
    }
    _defaults={'task_mgr_id': lambda obj, cr, uid, context: uid,}
    
class mrp_routing_workcenter(osv.osv):
    _inherit = 'mrp.routing.workcenter'
    _columns = {
        'wc_task_ids': fields.one2many('mrp.routing.workcenter.task','routing_wc_id',string='Work center tasks')
    }
    
class mrp_routing_workcenter_task(osv.osv):        
    _name = 'mrp.routing.workcenter.task'
    _description = "Routing work center's task"
    _columns = {
                'routing_wc_id': fields.many2one('mrp.routing.workcenter', 'Parent Work Center', select=True, ondelete='cascade',),
                'name': fields.char('Task Summary', size=128, required=True, select=True),
                'sequence': fields.integer('Sequence', select=True, help="Gives the sequence order when displaying a list of tasks."),
                'dept_id':fields.many2one('hr.department',string='Team',),
                'planned_hours': fields.float('Planned Hours'),
                }

class mrp_bom(osv.osv):
    _inherit = 'mrp.bom'
    def _hook_bom_wo_line(self, cr, uid, bom, wc_use):
        '''
        @param bom: mrp.bom object
        @param wc_use: mrp.routing.workcenter_lines: mrp.routing.workcenter
        @return: dict to fill the mo's workorder: mrp_production_workcenter_line
        '''
        data = super(mrp_bom,self)._hook_bom_wo_line(cr, uid, bom, wc_use)
        #+++John Wang, 09/12/2014+++# get the routing work center tasks: mrp_production_workcenter_line
        wc_tasks = []
        project_mfg_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'dmp_mrp', 'project_mfg')[1]
        for wc_task in wc_use.wc_task_ids:
            emp_ids = self.pool.get('hr.employee').search(cr, uid, [('department_id','=',wc_task.dept_id.id)])
            emp_ids = [(4,emp_id) for emp_id in emp_ids]
            wc_task = {'project_id':project_mfg_id,
                       'sequence':wc_task.sequence,
                       'dept_id':wc_task.dept_id.id,
                       'dept_mgr_id':wc_task.dept_id.manager_id.id,
                       'emp_ids':emp_ids,
                       'name':wc_task.name,
                       'planned_hours':wc_task.planned_hours,}
            wc_tasks.append((0,0,wc_task))        
        data.update({'task_ids': wc_tasks})
        return data
        
class mrp_production_workcenter_line(osv.osv):
    _inherit = 'mrp.production.workcenter.line'
    _columns = {
        'task_ids': fields.one2many('project.task', 'workorder_id',string='Working Tasks'),
    }

    def action_close(self, cr, uid, ids, context=None):
        #TODO generate the working hours time sheet 
        return super(mrp_production_workcenter_line,self).action_close(cr, uid, ids, context=context)  
    
class project_task(base_stage, osv.osv):
    _inherit = "project.task"
    _columns = {
        'workorder_id': fields.many2one('mrp.production.workcenter.line', string='Work Order', ondelete='cascade'),
        'workcenter_id': fields.related('workorder_id','workcenter_id', type='many2one', relation="mrp.workcenter", string='Work Center', readonly=True),
        'production_id': fields.related('workorder_id','production_id', type='many2one', relation="mrp.production", string='Manufacture Order', readonly=True, store=True),
        'product':fields.related('production_id','product_id',type='many2one',relation='product.product',string='Product', readonly=True),
        'dept_id':fields.many2one('hr.department',string='Team',),
        'dept_mgr_id':fields.many2one('hr.employee',string='Team Leader'),
    }
    def onchange_dept_id(self,cr,uid,ids,dept_id,context=None):
        resu = {}
        if dept_id:
            dept = self.pool.get('hr.department').read(cr, uid, dept_id, ['manager_id'],context=context)
            manager_id = dept['manager_id']
            emp_ids = self.pool.get('hr.employee').search(cr, uid, [('department_id','=',dept_id)],context=context)
            value={'dept_mgr_id':manager_id, 'emp_ids':emp_ids}
            resu['value'] = value
        return resu
    def default_get(self, cr, uid, fields_list, context=None):
        resu = super(project_task,self).default_get(cr, uid, fields_list, context=context)
        if not resu.get('project_id') and context.get('default_project_type',False) == 'mfg':
            result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'dmp_mrp', 'project_mfg')
            resu.update({'project_id':result[1]})
        if context.get('force_workorder'):
            wo_id = context.get('force_workorder')
            priority = self.pool.get('mrp.production.workcenter.line').read(cr, uid, wo_id, ['priority'],context=context)['priority']
            resu.update({'workorder_id': wo_id, 'priority':priority})
        return resu
    def on_change_wo(self,cr,uid,ids,wo_id,context=None):
        resu = {}
        if wo_id:
            wo = self.pool.get('mrp.production.workcenter.line').read(cr, uid, wo_id, ['priority'],context=context)
            value={'priority':wo['priority']}
            resu['value'] = value
        return resu