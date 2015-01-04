# -*- encoding: utf-8 -*-
##############################################################################
#
#    OGO Process Improvements Module
#    Copyright (C) 2012 OGO (<http://www.odoogo.com>).
#
##############################################################################
{
    'name': 'DMP Stock',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
Stocking Improvements
=====================
    """,
    'depends': ["dmp_base", "dmp_sale_product", "product", "purchase", "sale", "stock", 
                "product_manufacturer", "mrp", "product_fifo_lifo","stock_cancel"],
    'data':['product_view.xml',
        'wizard/product_set_printflag.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/stock_import_inventory_view.xml',       
        'wizard/stock_change_product_qty_view.xml',    
        'wizard/stock_return_picking_view.xml', 
        'wizard/stock_partial_picking_view.xml', 
        'wizard/stock_invoice_onshipping_single_view.xml',
        'stock_view.xml',
        'stock_sequence.xml',
        'stock_wh_loc.xml',     
        'stock_barcode_view.xml',
    ],
    'auto_install': False,
    'installable': True,
#    "js": ["static/src/js/dmp_stock.js"],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
