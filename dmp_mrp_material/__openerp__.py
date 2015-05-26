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
    'name': 'DMP MRP Materials Consuming',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
Manufacture Materials Consuming and Picking Improvements
1.Set auto_pick to False by default
2.hide the two 'Force Reservation' buttons on MO
3.When do MO's produce, generate a finished stock picking for the finished stock moving everytime, 
and do not auto done the moves, warehouse will do the receiving based on the picking,
Once all products are finisehd and receiving then the MO will be finished.
=====================
    """,
    'depends': ["mrp","dmp_mrp_hook","dmp_stock_mt","stock_no_autopicking","dmp_mrp_bom_route","dmp_stock_partial_pick"],
    'data': [
        'wizard/wo_material_request_view.xml',
        'wizard/mrp_pick_replace_product_view.xml',
        'mrp_view.xml',
        'mrp_pick_view.xml',
        'mrp_workflow.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
