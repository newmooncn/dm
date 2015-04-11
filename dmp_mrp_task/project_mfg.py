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
from lxml import etree
from openerp import netsvc
from openerp import tools
    
class project_task_work(osv.osv):
    _inherit = "project.task.work"
    _columns = {
        'emp_ids': fields.many2many("hr.employee","task_work_emp","work_id","emp_id",string="Employees"),
    }    

    def default_get(self, cr, uid, fields_list, context=None):
        res = super(project_task_work,self).default_get(cr, uid, fields_list, context=context)
        if not res:
            res = {}
        if context.get('task_employee_ids',False):
            #task_employee_ids structure is like: 'task_employee_ids': [[6, False, [392, 391]]
            res.update({'emp_ids':context['task_employee_ids'][0][2]})
        return res
    def get_emp_related_details(self, cr, uid, emp_id):
        res = {}
        emp_obj = self.pool.get('hr.employee')
        emp = emp_obj.browse(cr, uid, emp_id)
        if not emp.product_id:
            raise osv.except_osv(_('Bad Configuration !'),
                 _('Please define product and product category property account on the related employee.\nFill in the HR Settings tab of the employee form.%s')%(emp.name,))

        if not emp.journal_id:
            raise osv.except_osv(_('Bad Configuration !'),
                 _('Please define journal on the related employee.\nFill in the timesheet tab of the employee form.%s')%(emp.name,))

        acc_id = emp.product_id.property_account_expense.id
        if not acc_id:
            acc_id = emp.product_id.categ_id.property_account_expense_categ.id
            if not acc_id:
                raise osv.except_osv(_('Bad Configuration !'),
                        _('Please define product and product category property account on the related employee.\nFill in the timesheet tab of the employee form.%s')%(emp.name,))

        res['product_id'] = emp.product_id.id
        res['journal_id'] = emp.journal_id.id
        res['general_account_id'] = acc_id
        res['product_uom_id'] = emp.product_id.uom_id.id
        res['employee_id'] = emp_id
        return res
    
    def get_user_related_details(self, cr, uid, user_id):
        res = {}
        emp_obj = self.pool.get('hr.employee')
        emp_id = emp_obj.search(cr, uid, [('user_id', '=', user_id)])
        if not emp_id:
            user_name = self.pool.get('res.users').read(cr, uid, [user_id], ['name'])[0]['name']
            raise osv.except_osv(_('Bad Configuration !'),
                 _('Please define employee for user "%s". You must create one.')% (user_name,))
        return self.get_emp_related_details(cr, uid, emp_id[0])

from openerp.addons.project_timesheet import project_timesheet   
'''
Improve the timesheet account analytic generating logic, replace the account analytic account for the mfg task
''' 
def _project_timesheet_create(self, cr, uid, vals, context=None):
    timesheet_obj = self.pool.get('hr.analytic.timesheet')
    task_obj = self.pool.get('project.task')
    uom_obj = self.pool.get('product.uom')        
    vals_line = {}
    if not context:
        context = {}
    if not context.get('no_analytic_entry',False):
        #johnw, 08/08/2014, Improve the timesheet account analytic generating logic, replace the account analytic account for the mfg task
        def _add_ana_line(ana_acc_id, employee_id):
            #set data from employee
            result = self.get_emp_related_details(cr, uid, employee_id)
            vals_line['employee_id'] = employee_id
            vals_line['product_id'] = result['product_id']            
            vals_line['product_uom_id'] = result['product_uom_id']
            vals_line['general_account_id'] = result['general_account_id']
            vals_line['journal_id'] = result['journal_id']
            # Calculate quantity based on employee's product's uom
            if result['product_uom_id'] != default_uom:
                vals_line['unit_amount'] = uom_obj._compute_qty(cr, uid, default_uom, vals_line['unit_amount'], result['product_uom_id'])
                        
            vals_line['account_id'] = ana_acc_id
            res = timesheet_obj.on_change_account_id(cr, uid, False, ana_acc_id)
            if res.get('value'):
                vals_line.update(res['value'])
                
            vals_line['amount'] = 0.0
            
            timeline_id = timesheet_obj.create(cr, uid, vals=vals_line, context=context)
            
            amount = vals_line['unit_amount']
            prod_id = vals_line['product_id']
            unit = False
            # Compute based on pricetype
            #add the employee_id parameter, so dmp_hr.hr_timesheet.on_change_unit_amount() will calculate cost based on employee setting
            context.update({'employee_id':vals_line['employee_id']})
            amount_unit = timesheet_obj.on_change_unit_amount(cr, uid, timeline_id,
                prod_id, amount, False, unit, vals_line['journal_id'], context=context)
            if amount_unit and 'amount' in amount_unit.get('value',{}):
                updv = { 'amount': amount_unit['value']['amount'] }
                timesheet_obj.write(cr, uid, [timeline_id], updv, context=context)
            vals['hr_analytic_timesheet_id'] = timeline_id
                    
        task_data = task_obj.browse(cr, uid, vals['task_id'])
        emp_obj = self.pool.get('hr.employee')
        default_uom = self.pool.get('res.users').browse(cr, uid, uid).company_id.project_time_mode_id.id
        #set the common values
        vals_line['name'] = '%s: %s' % (tools.ustr(task_data.name), tools.ustr(vals['name'] or '/'))
        vals_line['user_id'] = vals['user_id']
        vals_line['date'] = vals['date'][:10]
        vals_line['unit_amount'] = vals['hours']
        #get the employee ids
        emp_ids = vals['emp_ids'][0][2]
        if not emp_ids:
            emp_id = emp_obj.search(cr, uid, [('user_id', '=', vals.get('user_id', uid))])
            if not emp_id:
                user_name = self.pool.get('res.users').read(cr, uid, [vals.get('user_id', uid)], ['name'])[0]['name']
                raise osv.except_osv(_('Bad Configuration !'),
                     _('Please define employee for user "%s". You must create one.')% (user_name,))
            emp_ids.append(emp_id[0])
                                    
        if task_data.project_type != 'mfg':
            acc_id = task_data.project_id and task_data.project_id.analytic_account_id.id or False
            for emp_id in emp_ids:
                _add_ana_line(acc_id, emp_id)
        else:            
            #add ref
            vals_line['ref'] = '%s : %s'%(task_data.workorder_id.production_id.name, task_data.workorder_id.code)
    return super(project_timesheet.project_work,self).create(cr, uid, vals, context=context)   
project_timesheet.project_work.create = _project_timesheet_create     