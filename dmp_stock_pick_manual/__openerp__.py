# -*- encoding: utf-8 -*-
##############################################################################
#
#    OGO Process Improvements Module
#    Copyright (C) 2012 OGO (<http://www.odoogo.com>).
#
##############################################################################
{
    'name': 'DMP Stock Picking manual entering',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
Stock Picking manual entering
1.Add the warehouse, warehouse_dest to picking, and make the warehouse/location, warehouse_dest/location_dest to be visible for picking
This is used for purchase sotcking order manual input
2.Imrpove the UOM selection
=====================
    """,
    'depends': ["stock"],
    'data':['stock_view.xml'],
    'auto_install': True,
    'installable': True,
#    "js": ["static/src/js/dmp_stock.js"],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
