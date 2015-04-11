# -*- encoding: utf-8 -*-
##############################################################################
#
#    DMEMS Process Improvements Module - Accounting
#    Copyright (C) 2014 DMEMS (<http://www.dmems.com>).
#
##############################################################################
{
    'name': 'DMP Account payment on purhcae',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
Accounting payment on purhcae
=====================
    * 
    """,

    'depends': ['account','purchase'],
    'data':["pay_po.xml",
            "purchase_payment_view.xml"],
    'auto_install': False,
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
