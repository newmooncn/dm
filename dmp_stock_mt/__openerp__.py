# -*- encoding: utf-8 -*-
##############################################################################
#
#    OGO Process Improvements Module
#    Copyright (C) 2012 OGO (<http://www.odoogo.com>).
#
##############################################################################
{
    'name': 'DMP Stock Material Request',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
Stock Material Request
=====================
    """,
    'depends': ["stock", "dmp_stock_ticket", 'product_fifo_lifo'],
    'data':['stock_view.xml',
        'stock_sequence.xml',
        'stock_mt_rpt_view.xml',
    ],
    'auto_install': False,
    'installable': True,
#    "js": ["static/src/js/dmp_stock.js"],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
