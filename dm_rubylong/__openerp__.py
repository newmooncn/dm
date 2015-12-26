# -*- coding: utf-8 -*-
##############################################################################
# OpenERP Connector
# Copyright 2013 DMEMS <johnw@dmems.com>
##############################################################################

{
    'name': 'dm rubylong',
    'summary': '锐浪报表JS',
    'version': '1.0',
    'category': 'report',
    'sequence': 21,
    'author': 'DMEMS',
    'website': 'http://www.dmems.com',
    'images': [''],
   "depends": ['base', 'report_webkit','web_pdf_preview'],
    'data': [
        'data/data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'description': """
    使用时下载 Grid++Report  官方网站：http://www.rubylong.cn
""",
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
