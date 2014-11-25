# -*- encoding: utf-8 -*-
##############################################################################
#
#    OGO Process Improvements Module
#    Copyright (C) 2012 OGO (<http://www.odoogo.com>).
#
##############################################################################
{
    'name': 'DM Process Partner',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
Partner
=====================
    * 1.Parnter Google Map
    * 2.Customer,Supplier menu: only show companies
    * 3.Only the customers with company can be select in sales order
    * 4.Only the suppliers with company can be select in purchase order
    * 5.Set 'is company' to true in customer,supplier menu list create new data.
    """,

    'depends': ['dmp_base','sale','purchase'],
    'data':[
     'partner_map_view.xml',
     'partner_view.xml',
    ],
    'auto_install': False,
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
