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
    * 2.Improve the domain and context to customers/suppliers menu
    *   2.1.Customer,Supplier menu: only show companies
    *   2.2.Only the customers with company can be select in sales order
    *   2.3.Only the suppliers with company can be select in purchase order
    *   2.4.Set 'is company' to true in customer,supplier menu list create new data.
    * 3.Partner's attachment
    """,

    'depends': ['dmp_base','sale','purchase'],
    'data':[
     'partner_map_view.xml',
     'partner_comp_supp_cust.xml',
     'ir_attachment_view.xml',
    ],
    'auto_install': False,
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
