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
    'name': 'DMP MRP',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
Manufacture Improvements
=====================
    """,
    #'depends': ["dmp_base", "sale", "dmp_stock", "product_manufacturer", "document", "mrp_operations", "procurement", "mrp","dmp_project"],
    #dmp_project: simple task...
    #dmp_stock: material request
    #dmp_engineer: Add bom import button to engineer proeject/task
    'depends': ["dmp_base","dmp_project", "dmp_engineer", "dmp_stock", "sale", "product_manufacturer", "document", "mrp_operations", "procurement", "mrp"],
    'data': [
        'security/ir.model.access.csv',
        'security/mrp_security.xml',
        'wizard/wo_material_request_view.xml',
        'wizard/mo_actions_view.xml',
        'mrp_view.xml',
        'mrp_sequence.xml',
        'wizard/add_common_bom_view.xml',
        'wizard/bom_import_view.xml',
        'mrp_workflow.xml',
        'pdm.xml',
        'procurement_view.xml',
        'project_mfg_view.xml',
        'project_report.xml',
        'project_data.xml',
        'board_tasks_view.xml',
        'wizard/task_print.xml',
    ],
    'test': [],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
