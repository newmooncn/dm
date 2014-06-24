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
import datetime
import pytz
from pytz import timezone
from tzlocal import get_localzone
import netsvc

from openerp import SUPERUSER_ID
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class work_order(osv.Model):
    _inherit = 'sale.order'
    _order = 'date_in desc, id desc'

    def _task_work_ids(self, cr, uid, ids, name, arg, context=None):
        res = {}
        task_obj = self.pool.get('project.task')
        project_obj = self.pool.get('project.project')
        for sale in self.browse(cr, uid, ids, context=context):
            res[sale.id] = []
            if sale.project_id:
                project_id = project_obj.search(cr, uid, [('analytic_account_id', '=', sale.project_id.id)])
                if project_id:
                    task_ids = task_obj.search(cr, uid, [('project_id', 'in', project_id)])
                    if task_ids:
                        for task in task_obj.browse(cr, uid, task_ids):
                            res[sale.id] += map(lambda a: a.id, task.work_ids or [])
        return res

    def _project_tasks(self, cr, uid, ids, name, arg, context=None):
        res = {}
        task_obj = self.pool.get('project.task')
        project_obj = self.pool.get('project.project')
        for sale in self.browse(cr, uid, ids, context=context):
            res[sale.id] = []
            if sale.project_id:
                project_id = project_obj.search(cr, uid, [('analytic_account_id', '=', sale.project_id.id)])
                if project_id:
                    task_ids = task_obj.search(cr, uid, [('project_id', 'in', project_id)])
                    if task_ids:
                        res[sale.id] = task_ids
        return res

    _columns = {
        'date_in': fields.datetime('Date In'),
        'date_due': fields.datetime('Date Due'),
        'date_closed': fields.datetime('Date Closed'),
        'mode_test_result_id': fields.char('Mode Test Result ID', size=256),
        'work_requested': fields.text('Repair Work Requested'),
        'm_work_requested': fields.text('Maintenance Work Requested'),
        'comment': fields.text('Comments'),
        'action_taken': fields.text('Action Taken'),
        'defect': fields.text('Defect/Cause'),
        'm_defect': fields.text('Defect/Cause'),
        'rev_test_result': fields.char('Rev Test Result', size=256),
        'relevancy': fields.char('Relevancy', size=256),
        'acc_distance': fields.integer('Acc Distance'),
        'acc_time': fields.integer('Acc Time'),
#        'work_type': fields.selection([('maintenance', 'Maintenance'),
#                                       ('repair', 'Repair')], 'Work Type'),
        'work_type': fields.many2one('dpro.work.type', 'Work Type'),
        'wr_code_id': fields.many2one('work.request.code', 'Repair WR Code'),
        'm_wr_code_id': fields.many2one('work.request.code', 'Maintenance WR Code'),
        'problem_code_id': fields.many2one('base.problem.code', 'Repair Problem Code'),
        'm_problem_code_id': fields.many2one('base.problem.code', 'Maintenance Problem Code'),
        'action_code_id': fields.many2one('base.action.code', 'Action Code'),
        'sla_id': fields.many2one('base.sla', 'SLA'),
        'status_id': fields.selection([('Pending', 'Pending Confirmation'), ('Confirmed', 'Confirmed'),
                                       ('In Progress', 'In Progress'), ('Completed', 'Completed'), ('QA', 'Quality Assurance'),
                                       ('Closed', 'Closed')], 'Status'),
        'loss_discovery': fields.text('Loss Discovery'),
        'part_replace_ids': fields.one2many('workorder.part.replace', 'workorder_id', 'Part Replaced'),
        'qc_ids': fields.one2many('workorder.quality.control', 'workorder_id', 'Quality Control'),
        'opportunity_subject': fields.char('Subject/Summary', size=256),
        'task_ids': fields.function(_project_tasks, type='many2many',
                                    relation='project.task',  string='Task'),
        'task_work_ids': fields.function(_task_work_ids, type='many2many',
                            relation='project.task.work', string='Time'),
        'color': fields.integer('Color Index'),
        'state': fields.selection([
            ('draft', 'Draft Work Order'),
            ('sent', 'Work Order Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Work Order'),
            ('manual', 'Work Order to Invoice'),
            ('shipping_except', 'Shipping Exception'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ], 'Status', readonly=True,help="Gives the status of the quotation or sales order.\
              \nThe exception status is automatically set when a cancel operation occurs \
              in the invoice validation (Invoice Exception) or in the picking list process (Shipping Exception).\nThe 'Waiting Schedule' status is set when the invoice is confirmed\
               but waiting for the scheduler to run on the order date.", select=True),
        'user_id': fields.many2one('res.users', 'Announcer',
                                   states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, select=True, track_visibility='onchange'),
        #Mod/Test ID (single line input), ), half width of content   
        'mod_test_id': fields.char('Mod/Test ID', size=64),
        #Rev. Test (single line input), same line as mod result id, half width of content 
        'rev_test': fields.char('Rev. Test', size=64),
        #- Maintenance Reason (multiline input)          
        'maintain_reason': fields.text('Maintenance Reason'),    
    }
    _defaults = {
        'color': 0,
        'status_id': 'pending',
    }

    def create(self, cr, uid, vals, context=None):
        if vals.get('name','/')=='/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'work.order') or '/'
        return super(work_order, self).create(cr, uid, vals, context=context)

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'date_order': fields.date.context_today(self, cr, uid, context=context),
            'state': 'draft',
            'invoice_ids': [],
            'date_confirm': False,
            'client_order_ref': '',
            'name': self.pool.get('ir.sequence').get(cr, uid, 'work.order'),
        })
        return super(work_order, self).copy(cr, uid, id, default, context=context)

    def onchange_datein_sla(self, cr, uid, ids, datein, sla_id, context=None):
        if context is None:
            context = {}
        result = {'value': {'date_due': False}}
        if not datein or not sla_id:
            return result
        sla_rec = self.pool.get('base.sla').browse(cr, uid, sla_id)
        user = self.pool.get('res.users').browse(cr, uid, uid)
        if sla_rec.due_date_opt != 'no_due':
            datein = datetime.datetime.strptime(datein, DATETIME_FORMAT)
            if sla_rec.due_date_opt == 'due_hour':
                if sla_rec.due_hour:
                    time = str(sla_rec.due_hour).split(':')
                    new_date = datein + datetime.timedelta(hours=int(time[0]), minutes=int(time[1]))
            if sla_rec.due_date_opt == 'due_time':
                new_date = datein + datetime.timedelta(days=1)
                if sla_rec.due_hour:
                    time = str(sla_rec.due_hour).split(':')
                    new_date = new_date.replace(hour=int(time[0]), minute=int(time[1]), second=0)
                    local_zone = get_localzone()
                    if user.tz:
                        local_zone = timezone(user.tz)
                    new_date = local_zone.localize(new_date)
                    new_date = new_date.astimezone(pytz.UTC)
            if sla_rec.due_date_opt == 'due_day_time':
                new_date = datein + datetime.timedelta(days=sla_rec.due_day)
                if sla_rec.due_hour:
                    time = str(sla_rec.due_hour).split(':')
                    new_date = new_date.replace(hour=int(time[0]), minute=int(time[1]))
                    local_zone = get_localzone()
                    if user.tz:
                        local_zone = timezone(user.tz)
                    new_date = local_zone.localize(new_date)
                    new_date = new_date.astimezone(pytz.UTC)

            result['value']['date_due'] = new_date.strftime(DATETIME_FORMAT)
        return result

    def action_button_confirm(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        #start code added for check stock available
        for order in self.browse(cr, uid, ids):
            for line in order.order_line:
                if line.product_id and line.product_id.type == 'product' \
                                and line.product_id.qty_available <=0:
                    raise osv.except_osv(_('Error!'),
                                         _('There is no enough stock available for products.'))
        self.write(cr, uid, ids, {'status_id': 'Confirmed'})
        #end code added
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(uid, 'sale.order', ids[0], 'order_confirm', cr)

        # redisplay the record as a sales order
        view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sale', 'view_order_form')
        view_id = view_ref and view_ref[1] or False,
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales Order'),
            'res_model': 'sale.order',
            'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'nodestroy': True,
        }

    def open_map(self, cr, uid, ids, context=None):
        sale = self.browse(cr, uid, ids[0], context=context)
        url="http://maps.google.com/maps?oi=map&q="
        if sale.partner_id:
            partner = sale.partner_id
            if partner.street:
                url += partner.street.replace(' ','+')
            if partner.city:
                url += '+' + partner.city.replace(' ','+')
            if partner.state_id:
                url += '+' + partner.state_id.name.replace(' ','+')
            if partner.country_id:
                url += '+' + partner.country_id.name.replace(' ','+')
            if partner.zip:
                url += '+' + partner.zip.replace(' ','+')
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'new',
            }
        return True

work_order()


class work_order_line(osv.Model):
    _inherit = 'sale.order.line'

    def _avail_qty(self, cr, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        res = {}
        for line in self.browse(cr, uid, ids):
            res[line.id] = 'AVAILABLE'
            if line.product_id and line.product_id.type == 'product' \
                            and line.product_id.qty_available <=0:
                res[line.id] = 'NOT AVAIL'
        return res

    _columns = {
        'prodlot_id': fields.many2one('stock.production.lot', 'Serial No'),
        'available_qty': fields.function(_avail_qty, string='Available Qty',
                                         type='char', size=32),
    }

work_order_line()

class dpro_work_type(osv.osv):
    _name = "dpro.work.type"
    _description = "Work Type"
    _columns = {
        'name': fields.char('Name', size=32),
    }

