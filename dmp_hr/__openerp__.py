# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010 OpenERP s.a. (<http://openerp.com>).
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
{
    'name': 'DMP Human Resource',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
    DMP HR Extension:  
        
        """,
    'depends': ["dmp_base", "hr", "hr_holidays", "product", "hr_timesheet", "multi_image", "hr_recruitment", "hr_contract"],
    'init_xml': [],
    'update_xml': [
        'hr_emp_menu.xml',
        'hr_view.xml',
        'hr_timesheet_view.xml',
        'hr_contract_view.xml',
        'wizard/hr_clock_emp_sync_view.xml',
        'wizard/hr_emp_worktime_view.xml',
        'wizard/hr_attend_calc_action_view.xml',
        'wizard/hr_rpt_attend_month_view.xml',
        'wizard/hr_rpt_attend_month_workflow.xml',
        'wizard/hr_rpt_attend_emp_day_view.xml',
        'wizard/hr_attend_report.xml',
        'hr_attendance_view.xml',
        'hr_attendance_data.xml',
        'wizard/hr_attend_emp.xml',
        'hr_clock_view.xml',
        'hr_clock_data.xml',
        'hr_holidays.xml',
        'emppay/hr_emppay_sequence.xml',
        'emppay/hr_emppay_view_setup.xml',
        'emppay/hr_emppay_view_main.xml',
        'emppay/ir.model.access.csv',
        'emppay/hr_contact_emppay_batchset_view.xml',
        'emppay/hr_emppay_report.xml',
        'emppay/hr_emppay_emp.xml',
        'security/ir.model.access.csv',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'active': False,
	'sequence': 150,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
