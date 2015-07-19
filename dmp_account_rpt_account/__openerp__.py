# -*- encoding: utf-8 -*-
##############################################################################
#
#    DMEMS Process Improvements Module - Accounting
#    Copyright (C) 2014 DMEMS (<http://www.dmems.com>).
#
##############################################################################
{
    'name': 'DMP Account Account report',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
Accounting Account report
=====================
    * 
    """,

    'depends': ['dmp_base','account','dmp_account_move_source','dmp_account_account'],
    'data':["account_report.xml",
            "rpt_account_cn_menu.xml",
            "rpt_account_cn_gl_view.xml",
            "rpt_account_cn_detail_view.xml",
            "rpt_account_cn_detail_predefine_view.xml",            
            "rpt_account_cn_detail_money_view.xml",
    ],
    'auto_install': False,
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
