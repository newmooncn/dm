# -*- encoding: utf-8 -*-
##############################################################################
#
#    OGO Process Improvements Module
#    Copyright (C) 2012 OGO (<http://www.odoogo.com>).
#
##############################################################################
{
    'name': 'DMP Base',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
Process Base
=====================
    """,

    'depends': ['base','dm_base', "base_custom_attributes", "document"],
    'data':['rpt_base_view.xml',
            'ir_attachment_view.xml',
            'security/security.xml',
            'security/ir.model.access.csv',
            'hr_view.xml',
    ],
    'auto_install': False,
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
