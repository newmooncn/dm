# -*- encoding: utf-8 -*-
##############################################################################
#
#    DMEMS Process Improvements Module - Accounting
#    Copyright (C) 2014 DMEMS (<http://www.dmems.com>).
#
##############################################################################
{
    'name': 'DM Process Account',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
Accounting
=====================
    * 
    """,

    'depends': ['dmp_base','account','purchase','account_voucher','account_analytic_plans',"account_prepayment", "sale_quick_payment", "sale_exceptions"],
    'data':[
            'account_account_view.xml',
            'account_move_view.xml',
            'wizard/account_move_batch.xml',
            'account_analytic_view.xml',
            
            "account_report.xml",
            "wizard/rpt_account_cn_menu.xml",
            "wizard/rpt_account_cn_gl_view.xml",
            "wizard/rpt_account_cn_detail_view.xml",
            "wizard/rpt_account_cn_detail_predefine_view.xml",
            "wizard/rpt_inventory_view.xml",
            "wizard/rpt_account_partner_view.xml",          
            
            "account_financial_report_view.xml",
            "wizard/account_financial_report_wizard_view.xml", 
            
            "account_invoice_view.xml",
            "account_voucher_view.xml",
            "cash_bank_trans_view.xml",
            "emp_borrow_view.xml",
            "emp_reimburse_view.xml",
            
            #the prepayment module
            "payment/pay_po.xml",
            "payment/purchase_payment_view.xml",
            "payment/sale_payment_view.xml",
            "payment/invoice_payment_view.xml"
             
    ],
    'auto_install': False,
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
