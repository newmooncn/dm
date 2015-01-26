# -*- encoding: utf-8 -*-
##############################################################################
#
#    OGO Process Improvements Module
#    Copyright (C) 2012 OGO (<http://www.odoogo.com>).
#
##############################################################################
{
    'name': 'DMP Sale Product',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
Sale Product ID
=====================
    """,
    'depends': ["dmp_base", "dmp_mto","product", "sale", "mrp", "project"],
    'data':['sale_product_view.xml',
        'sale_product_workflow.xml',
        'sale_product_sequence.xml',
    ],
    'auto_install': False,
    'installable': True,
#    "js": ["static/src/js/dmp_stock.js"],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
