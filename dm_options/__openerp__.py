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
    'sequence': 1000,
    'summary': 'DMEMS Base option list',
    'description': """
==================================
1.add the common option list feature
------------------------------------------------------
    """,
    'author': 'DMEMS',
    'website': 'http://www.dmems.com',
    'images': [],
    'depends': ['base'],
    'data': [
        'ir.model.access.csv',
        'option_view.xml',
        ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
