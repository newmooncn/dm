# -*- encoding: utf-8 -*-
##############################################################################
#
#    DMEMS Base Module
#    Copyright (C) 2014 DMEMS (<http://www.dmems.com>).
#
##############################################################################
{
    'name': 'DM Announce removing',
    'version': '1.0',
    'category': 'Customization',
    'sequence': 1000,
    'summary': 'DM Announce removing',
    'description': """
DM Announce removing
    """,
    'author': 'DMEMS',
    'website': 'http://www.dmems.com',
    'images': [],
    'depends': ['base'],
    'data': [],
    'js': ['static/src/js/dm_announce.js'],
    #web    
    'installable': True,
    'auto_install': False,
    'application': True,
}
