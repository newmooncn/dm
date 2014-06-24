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
from openerp.osv import fields, osv
from openerp.tools.translate import _

class procurement_order(osv.osv):
    _inherit = "procurement.order"

    def action_produce_assign_service(self, cr, uid, ids, context=None):
        project_task = self.pool.get('project.task')
        for procurement in self.browse(cr, uid, ids, context=context):
            project = self._get_project(cr, uid, procurement, context=context)
            planned_hours = self._convert_qty_company_hours(cr, uid, procurement, context=context)
            task_id = project_task.create(cr, uid, {
                'name': '%s:%s' % (procurement.origin or '', procurement.product_id.name),
                'date_deadline': procurement.date_planned,
                'planned_hours': planned_hours,
                'remaining_hours': planned_hours,
                'partner_id': procurement.sale_line_id and procurement.sale_line_id.order_id.partner_id.id or False,
                'user_id': procurement.product_id.product_manager.id,
                'procurement_id': procurement.id,
                'description': procurement.name + '\n' + (procurement.note or ''),
                'project_id':  project and project.id or False,
                'company_id': procurement.company_id.id,
                'sale_id': procurement.sale_line_id and \
                                procurement.sale_line_id.order_id and \
                                procurement.sale_line_id.order_id.id,
            },context=context)
            self.write(cr, uid, [procurement.id], {'task_id': task_id,
                                                   'state': 'running',
                                                   'message':_('Task created.')}, context=context)
        self.project_task_create_note(cr, uid, ids, context=context)
        return task_id

procurement_order()
