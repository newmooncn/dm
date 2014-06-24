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
    'name': 'YANHUI',
    'version': '1.0',
    'category': 'General',
    'description': """
    
       YANHUI Extension:  
        
        """,
        
        
    'author': 'DMEMS Inc.',
    'maintainer': 'DMEMS Inc.',
    'website': 'http://www.dmems.com/',
    'depends': ["base","crm"],
    'init_xml': [],
    'update_xml': [],
    'demo_xml': [],
    'test': [],
    'js': [
        'static/src/js/common.js'
    ],    
    'css': ['static/src/css/common.css',],
    'qweb' : [
        "static/src/xml/common.xml",
    ],	
    'installable': True,
    'auto_install': False,
    'active': False,
	'sequence': 150,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
