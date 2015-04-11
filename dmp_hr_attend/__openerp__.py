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
    'name': 'DMP HR Attendance',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
    DMP HR Attendance:  
        
        """,
    'depends': ["dmp_hr_empcode", "dmp_hr_my", "hr_attendance", "audittrail"],
    'init_xml': [],
    'update_xml': [     
        'security/ir.model.access.csv',   
        'wizard/hr_clock_emp_sync_view.xml',
        'wizard/hr_emp_wtgrp_set_view.xml',
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
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
