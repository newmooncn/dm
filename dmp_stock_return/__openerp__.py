# -*- encoding: utf-8 -*-
##############################################################################
#
#    OGO Process Improvements Module
#    Copyright (C) 2012 OGO (<http://www.odoogo.com>).
#
##############################################################################
{
    'name': 'DMP Stock Returning',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
Stock Returning Improvements
=====================
    """,
    'depends': ["stock","product_fifo_lifo"],
    'data':['wizard/stock_return_picking_view.xml', 
        'stock_view.xml',
    ],
    'auto_install': False,
    'installable': True,
#    "js": ["static/src/js/dmp_stock.js"],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
