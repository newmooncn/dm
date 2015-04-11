# -*- encoding: utf-8 -*-
##############################################################################
#
#    DMEMS Base Module
#    Copyright (C) 2014 DMEMS (<http://www.dmems.com>).
#
##############################################################################
{
    'name': 'DM confirm message',
    'version': '1.0',
    'category': 'Customization',
    'sequence': 1000,
    'summary': 'DM confirm message',
    'description': """
Confirm message dialog
    """,
    'author': 'DMEMS',
    'website': 'http://www.dmems.com',
    'images': [],
    'depends': ['base'],
    'data': ["confirm_message_view.xml",],
    #web
    'installable': True,
    'auto_install': False,
    'application': True,
}
