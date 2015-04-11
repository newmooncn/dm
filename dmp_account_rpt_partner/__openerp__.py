# -*- encoding: utf-8 -*-
##############################################################################
#
#    DMEMS Process Improvements Module - Accounting
#    Copyright (C) 2014 DMEMS (<http://www.dmems.com>).
#
##############################################################################
{
    'name': 'DMP Account partner report',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
Accounting partner report
=====================
    * 
    """,

    'depends': ['account'],
    'data':[
            "account_report.xml",
            "rpt_account_partner_view.xml",
    ],
    'auto_install': False,
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
