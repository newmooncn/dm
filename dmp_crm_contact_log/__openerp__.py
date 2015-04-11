# -*- encoding: utf-8 -*-
##############################################################################
#
#    OGO Process Improvements Module
#    Copyright (C) 2012 OGO (<http://www.odoogo.com>).
#
##############################################################################
{
    'name': 'DMP CRM Contacts Log',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
CRM Contacts Log
=====================
    * 1.Lead/Opporunity: add the data visibility by sales team, team manager only can see its own team's members
    """,

    'depends': ['dmp_base','crm'],
    'data':[
        'ir.model.access.csv',
        'crm_view.xml'
    ],
    'auto_install': False,
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
