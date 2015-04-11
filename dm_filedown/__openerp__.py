# -*- encoding: utf-8 -*-
##############################################################################
#
#    DMEMS Base Module
#    Copyright (C) 2014 DMEMS (<http://www.dmems.com>).
#
##############################################################################
{
    'name': 'DM file download',
    'version': '1.0',
    'category': 'Customization',
    'sequence': 1000,
    'summary': 'DMEMS file download',
    'description': """
File download utility
    """,
    'author': 'DMEMS',
    'website': 'http://www.dmems.com',
    'images': [],
    'depends': ['base'],
    'data': ['file_down_view.xml',],
    #web
    'installable': True,
    'auto_install': False,
    'application': True,
}
