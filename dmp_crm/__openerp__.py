# -*- encoding: utf-8 -*-
##############################################################################
#
#    OGO Process Improvements Module
#    Copyright (C) 2012 OGO (<http://www.odoogo.com>).
#
##############################################################################
{
    'name': 'DM Process CRM',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
CRM
=====================
    * 1.Lead/Opporunity: add the data visibility by sales team, team manager only can see its own team's members
    """,

    'depends': ['dmp_base','crm'],
    'data':[
     'security/crm_security.xml'
    ],
    'auto_install': False,
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
