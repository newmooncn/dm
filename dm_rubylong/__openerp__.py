# -*- coding: utf-8 -*-
##############################################################################
# OpenERP Connector
# Copyright 2015 DMEMS <johnw@dmems.com>
##############################################################################

{
    'name': 'dm rubylong',
    'summary': '锐浪报表模版',
    'version': '1.0',
    'category': 'report',
    'sequence': 21,
    'author': 'DMEMS',
    'website': 'http://www.dmems.com',
    'images': [''],
   "depends": ['base', 'web_pdf_preview'],
    'data': [
        'rubylong_security.xml',
        'rubylong_templates.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'description': """
    使用时下载 Grid++Report  官方网站：http://www.rubylong.cn
""",
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
