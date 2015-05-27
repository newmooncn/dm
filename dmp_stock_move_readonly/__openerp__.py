# -*- encoding: utf-8 -*-
##############################################################################
#
#    OGO Process Improvements Module
#    Copyright (C) 2012 OGO (<http://www.odoogo.com>).
#
##############################################################################
{
    'name': 'DMP Stock Move Readonly',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
Stocking Move Improvements
04/19:
For the moves with sale/purchsae/maunfacuture related orders, the product/qty/uom are readonly
Depend the modules with stock_picking.purchase_id,sale_id,production_id
=====================
    """,
    'depends': ["purchase","sale_stock","dmp_mrp_material"],
    'data':['stock_view.xml'],
    'auto_install': False,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
