# -*- encoding: utf-8 -*-
##############################################################################
#
#    OGO Process Improvements Module
#    Copyright (C) 2012 OGO (<http://www.odoogo.com>).
#
##############################################################################
{
    'name': 'DMP Stock Deliver Ticket#',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
Stock Deliver Ticket#
=====================
    """,
    'depends': ["stock"],
    'data':['stock_view.xml',
        'wizard/stock_partial_picking_view.xml',
    ],
    'auto_install': False,
    'installable': True,
#    "js": ["static/src/js/dmp_stock.js"],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
