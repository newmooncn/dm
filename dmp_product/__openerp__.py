# -*- encoding: utf-8 -*-
##############################################################################
#
#    OGO Process Improvements Module
#    Copyright (C) 2012 OGO (<http://www.odoogo.com>).
#
##############################################################################
{
    'name': 'DMP Product',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
Product Improvements
=====================
    """,
    'depends': ["product", "sale", "stock", "purchase", "product_manufacturer"],
    'data':['security/dmp_product_security.xml',
        'security/ir.model.access.csv',            
        'product_sequence.xml',
        'product_view.xml',
        'wizard/product_batch_query_view.xml',
    ],
    'auto_install': False,
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
