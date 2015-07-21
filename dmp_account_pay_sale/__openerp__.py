# -*- encoding: utf-8 -*-
##############################################################################
#
#    DMEMS Process Improvements Module - Accounting
#    Copyright (C) 2014 DMEMS (<http://www.dmems.com>).
#
##############################################################################
{
    'name': 'DMP Account payment on sale',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
Accounting payment on sale
=====================
    * 07/20/2015, change the sale invoice partner to be same as sale order, do not use partner_invoice_id, 
            since we need make the AP and accounting data to be one partner_id
    """,

    'depends': ['account','sale','sale_quick_payment','account_prepayment'],
    'data':["sale_payment_view.xml"],
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: