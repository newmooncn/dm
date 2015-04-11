# -*- encoding: utf-8 -*-
##############################################################################
#
#    DMEMS Process Improvements Module - Accounting
#    Copyright (C) 2014 DMEMS (<http://www.dmems.com>).
#
##############################################################################
{
    'name': 'DMP Account financial report',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
Accounting  financial report
=====================
    * 
    """,

    'depends': ['account','dmp_account_rpt_account'],
    'data':[
            'ir.model.access.csv',
            "account_financial_report_view.xml",
            "wizard/account_financial_report_wizard_view.xml", 
    ],
    'auto_install': False,
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
