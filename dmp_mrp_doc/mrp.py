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

class mrp_bom(osv.osv):
    _inherit = 'mrp.bom'
  
    def attachment_tree_view(self, cr, uid, ids, context):
        project_ids = self.pool.get('project.project').search(cr, uid, [('bom_id', 'in', ids)])
        task_ids = self.pool.get('project.task').search(cr, uid, ['|',('bom_id', 'in', ids),('project_id','in',project_ids)])
        domain = [
             '|','|', 
             '&', ('res_model', '=', 'mrp.bom'), ('res_id', 'in', ids),
             '&', ('res_model', '=', 'project.project'), ('res_id', 'in', project_ids),
             '&', ('res_model', '=', 'project.task'), ('res_id', 'in', task_ids)
        ]
        res_id = ids and ids[0] or False
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'view_id': False,
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, res_id)
        }   
        
class mrp_production_workcenter_line(osv.osv):
    
    def wo_docs(self, cr, uid, ids, context):
        bom_ids = [wo.bom_id.id for wo in self.browse(cr, uid, ids, context=context) if wo.bom_id]
        return self.pool.get('mrp.bom').attachment_tree_view(cr, uid, bom_ids, context=context) 
    _inherit = 'mrp.production.workcenter.line'