# -*- encoding: utf-8 -*-
##############################################################################
#
#    DMEMS Base Module
#    Copyright (C) 2014 DMEMS (<http://www.dmems.com>).
#
##############################################################################
{
    'name': 'DM cron improvements',
    'version': '1.0',
    'category': 'Customization',
    'sequence': 1000,
    'summary': 'DMEMS cron improvements',
    'description': """
cron improvements
    """,
    'author': 'DMEMS',
    'website': 'http://www.dmems.com',
    'images': [],
    'depends': ['base','mail'],
    'data': ['ir_cron_view.xml',],
    #web
    'installable': True,
    'auto_install': False,
    'application': True,
}
