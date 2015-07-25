# -*- encoding: utf-8 -*-
##############################################################################
#
#    DMEMS Process Improvements Module - Accounting
#    Copyright (C) 2014 DMEMS (<http://www.dmems.com>).
#
##############################################################################
{
    'name': 'DMP Account base',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
Accounting Account base
=====================
    * allow to delete invoice with draft/cancel, but have been invalidated
    * improve sales order invoice preparation
    * Add account_voucher.invoice_id and account_move.invoice_id for the Invoice Payment
    """,

    'depends': ['dmp_base','account','sale'],
    'data':[],
    'auto_install': False,
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
