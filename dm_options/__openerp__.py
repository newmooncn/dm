# -*- encoding: utf-8 -*-
##############################################################################
#
#    DMEMS Base Module
#    Copyright (C) 2014 DMEMS (<http://www.dmems.com>).
#
##############################################################################
{
    'name': 'DM Base option list',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
DMEMS Base option list
==================================
    """,
    'depends': ['base'],
    'data': [
        'ir.model.access.csv',
        'option_view.xml',
        ],
    'installable': True,
    'auto_install': True,
    'application': False,
}
