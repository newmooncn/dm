# -*- encoding: utf-8 -*-
##############################################################################
#
#    DMEMS Base Module
#    Copyright (C) 2014 DMEMS (<http://www.dmems.com>).
#
##############################################################################
{
    'name': 'DM Base',
    'version': '1.0',
    'category': 'Customization',
    'sequence': 1000,
    'summary': 'DMEMS Base',
    'description': """
DM Base
==================================

------------------------------------------------------
    """,
    'author': 'DMEMS',
    'website': 'http://www.dmems.com',
    'images': [],
    'depends': ['base','web'],
    'data': [
        'security/dm_base_security.xml',
        'views/dm_base.xml',
        'workflow_view.xml'
        ],
    'demo': [],
    'installable': True,
    'auto_install': True,
    'application': True,
}
