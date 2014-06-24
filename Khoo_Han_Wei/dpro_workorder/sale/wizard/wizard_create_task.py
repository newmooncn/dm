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
from openerp.osv import fields, osv, orm
import time
from openerp.tools.translate import _

class wizard_create_task(osv.osv_memory):
    _name = "wizard.create.task"

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(wizard_create_task, self).default_get(cr, uid, fields, context=context)
        if context.get('active_id'):
            workorder = self.pool.get('sale.order').browse(cr,
                                                uid, context['active_id'])
            if workorder.project_id:
                project_id = self.pool.get('project.project').search(cr,
                                uid, [('analytic_account_id', '=', workorder.project_id.id)])
                if project_id:
                    res.update({'project_id': project_id[0]})
            res.update({'partner_id': workorder.partner_id.id})
        return res

    _columns = {
        'name': fields.char('Name', size=256),
        'project_id': fields.many2one('project.project', 'Project'),
        'user_id': fields.many2one('res.users', 'Assigned To'),
        'partner_id': fields.many2one('res.partner', 'Customer'),
        'date_deadline': fields.date('Deadline'),
        'description': fields.text('Description'),
    }

    def action_create(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        record = self.browse(cr, uid, ids[0])
        if not record.project_id:
            raise osv.except_osv(_('Error!'),
                                 _('Please define project for create task.'))
        task = {
            'name': record.name,
            'project_id': record.project_id.id,
            'user_id': record.user_id and record.user_id.id or False,
            'partner_id': record.partner_id and record.partner_id.id or False,
            'date_deadline': record.date_deadline or False,
            'description': record.description or False,
        }
        self.pool.get('project.task').create(cr, uid, task)
        return True

wizard_create_task()
