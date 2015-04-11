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

class mrp_routing(osv.osv):
    _inherit = 'mrp.routing'
    _sql_constraints = [
        ('name', 'unique(name)', 'Routing name must be unique!'),
        ('code', 'unique(code)', 'Routing code must be unique!'),
    ]
    
class mrp_routing_workcenter(osv.osv):
    _inherit = 'mrp.routing.workcenter'
    _columns = {
        'oper_pre_ids': fields.many2many('mrp.routing.workcenter', 'route_oper_flow','oper_next_id','oper_pre_id', string='Previous Workcenters', domain="[('routing_id','=',routing_id)]"),
        'oper_next_ids': fields.many2many('mrp.routing.workcenter', 'route_oper_flow','oper_pre_id','oper_next_id', string='Next Workcenters', domain="[('routing_id','=',routing_id)]"),
    }
    _sql_constraints = [
        ('name', 'unique(routing_id,name)', 'Routing work center name must be unique under one routing!'),
    ]
    
class mrp_production(osv.osv):
    _inherit = 'mrp.production'
    def _action_compute_lines(self, cr, uid, ids, properties=None, context=None):
        resu = super(mrp_production, self)._action_compute_lines(cr, uid, ids, properties=properties, context=context) 
        #add by johnw@07/11/2014, update the wo_pre_ids and wo_next_ids
        #========begin=========
        workcenter_line_obj = self.pool.get('mrp.production.workcenter.line')
        wo_ids = workcenter_line_obj.search(cr, uid, [('production_id','in',ids)],context=context)
        sql = '''
        select a.id as pre_id, e.id as next_id
        from mrp_production_workcenter_line a
        join mrp_routing_workcenter b on a.routing_operation_id  = b.id 
        join route_oper_flow c on b.id = c.oper_pre_id 
        join mrp_routing_workcenter d on c.oper_next_id = d.id  
        join mrp_production_workcenter_line e 
            on e.routing_operation_id = d.id
            and a.production_id = e.production_id
            and a.bom_id = e.bom_id
            and a.routing_id = e.routing_id
        where a.id = ANY(%s)
        order by a.id,e.id
        '''
        cr.execute(sql, (wo_ids,))
        wo_ids_flow = dict.fromkeys(wo_ids,False)
        #retrieve data, store to the dict
        for data in cr.fetchall():
            wo_pre_id = data[0]
            wo_next_id = data[1]
            if not wo_ids_flow[wo_pre_id]:
                wo_ids_flow[wo_pre_id] = []
            wo_ids_flow[wo_pre_id].append((4,wo_next_id))
            
        #loop to update wo_next_ids, since the many2many is two-way, so the wo_pre_ids will be updated automatically.
        for wo_id, wo_next_ids in wo_ids_flow.items():
            workcenter_line_obj.write(cr, uid, [wo_id], {'wo_next_ids':wo_next_ids}, context=context)
        #========end=========
        return resu

class mrp_bom(osv.osv):
    _inherit = 'mrp.bom'
    
    def _hook_bom_wo_line(self, cr, uid, bom, wc_use):
        '''
        @param bom: mrp.bom object
        @param wc_use: mrp.routing.workcenter_lines: mrp.routing.workcenter
        @return: dict to fill the mo's workorder: mrp_production_workcenter_line
        '''
        data = super(mrp_bom,self)._hook_bom_wo_line(cr, uid, bom, wc_use)
        #johnw, set the wo's bom, routing data
        data.update({
            'bom_id': bom.id,
            'routing_id': wc_use.routing_id.id,
            'routing_operation_id': wc_use.id,
            'name': tools.ustr(wc_use.name) + ' - '  + tools.ustr(bom.name)                        
            })
        return data
    
from openerp.addons.mrp_operations.mrp_operations import mrp_production_workcenter_line as mrp_prod_wc
mrp_prod_wc._order = 'id desc, priority, production_id desc, sequence asc'

class mrp_production_workcenter_line(osv.osv):
    _inherit = 'mrp.production.workcenter.line'
    
    def _has_pre_wo(self, cr, uid, ids, field_name, arg, context=None):
        res = dict.fromkeys(ids,False)
        for wo in self.browse(cr, uid, ids, context=context):
            if wo.wo_pre_ids:
                res[wo.id] = True
        return res    
            
    _columns = {
        'bom_id': fields.many2one('mrp.bom', string='BOM', readonly=True),
        'routing_id': fields.many2one('mrp.routing', string='Routing', readonly=True),
        'routing_operation_id': fields.many2one('mrp.routing.workcenter', string='Routing Operation', readonly=True ),
        #relationship among work orders
        'has_pre_ids': fields.function(_has_pre_wo, type='boolean', string='Has Pre WO'),
        'wo_pre_ids': fields.many2many('mrp.production.workcenter.line', 'mrp_wo_flow','wo_next_id','wo_pre_id', string='Previous WOs', domain="[('production_id','=',production_id),('bom_id','=',bom_id),]"),
        'wo_next_ids': fields.many2many('mrp.production.workcenter.line', 'mrp_wo_flow','wo_pre_id','wo_next_id', string='Next WOs', domain="[('production_id','=',production_id),('bom_id','=',bom_id),]"),
        #add 'ready' state
        'state': fields.selection([('draft','Draft'),('ready','Ready'),('cancel','Cancelled'),('pause','Pending'),('startworking', 'In Progress'),('done','Finished')],'Status', readonly=True,
                                 help="* When a work order is created it is set in 'Draft' status.\n" \
                                       "* When user sets work order in start mode that time it will be set in 'In Progress' status.\n" \
                                       "* When work order is in running mode, during that time if user wants to stop or to make changes in order then can set in 'Pending' status.\n" \
                                       "* When the user cancels the work order it will be set in 'Canceled' status.\n" \
                                       "* When order is completely processed that time it is set in 'Finished' status."),
    }
        
    #improve the action_done() in mrp_operations
    def action_done(self, cr, uid, ids, context=None):
        resu = super(mrp_production_workcenter_line,self).action_done(cr, uid, ids, context)
        '''
        Trigger all of the next workorder to go to the 'ready' state, this will call the wo.is_ready() by the workflow definition 
        '''
        wf_service = netsvc.LocalService("workflow")
        for wo in self.browse(cr, uid, ids, context=context):
            if wo.wo_next_ids:
                for wo_next in wo.wo_next_ids:
                    wf_service.trg_validate(uid, 'mrp.production.workcenter.line', wo_next.id, 'ready_to_start', cr)
        return resu    
    
    def is_ready(self, cr, uid, ids):
        """
        @return: True or False
        """
        res = True
        for wo in self.browse(cr, uid, ids):
            #if there are previous WO, only when all of them are done, then this WO is ready to start
            if wo.wo_pre_ids:
                for wo_pre in wo.wo_pre_ids:
                    if wo_pre.state != 'done':
                        res = False
                        break
        return res   

class mrp_workcenter(osv.osv):
    _inherit = 'mrp.workcenter'
    _columns = {
        'manager_id': fields.many2one('res.users', 'Manager'),
        'members': fields.many2many('hr.employee', 'wc_emp_rel', 'wc_id', 'emp_id', 'Work Center Members',
            help="Work Center's members are employees who can have an access to the work orders related to this work center.", ),
        } 