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

* Add product User/Officer/Manager role, to control the product data changing activity
* Rename 'Products Variants' menu to 'Products' to list product.product, and hide the original 'Products' menu listing product.template
* Add Create User/Date fields
* Add Product Code sequence
* Product code/name/cn name must be unique
//* Add cn_name searching based on the original product code, ean13 and name
* add the multi part# query, user can enter default_code like: %code1%,%code2%...%coden%
//* Product batch query by one excel


    """,
    'depends': ['dm_base', "product", "sale", "stock", "purchase", "account"],
    'data':['security/dmp_product_security.xml',
        'security/ir.model.access.csv',
        'product_menu.xml',          
        'product_sequence.xml',
        'product_view.xml',
#        'wizard/product_batch_query_view.xml',
    ],
    'auto_install': False,
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
