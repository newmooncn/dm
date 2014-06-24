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
{
    'name': 'dPro',
    'version': '1.0',
    'category': 'Service Management',
    'description': """dPro""",
    'author': 'Acespritech',
    'website': 'http://www.acespritech.com',
    'depends': ['base', 'crm', 'account', 'sale', 'project',
                'hr_timesheet_sheet', 'project_timesheet', 'project_mrp',
                'sale_crm', 'sale_margin', 'sale_stock'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'base/base_sequence.xml',
        'base/base_view.xml',
        'partner/partner_view.xml',
        'product/product_view.xml',
        'sale/wizard/wizard_create_task_view.xml',
        'sale/sale_sequence.xml',
        'sale/sale_view.xml',
        'sale/sale_report.xml',
        'stock/stock_view.xml',
        'project/project_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
