# -*- encoding: utf-8 -*-
##############################################################################
#
#    OGO Process Improvements Module
#    Copyright (C) 2012 OGO (<http://www.odoogo.com>).
#
##############################################################################
{
    'name': 'DMP Partner defaults',
    'version': '1.0',
    'category': 'Customization',
    'author': 'DMEMS',
    'website': 'www.dmems.com',
    'description': """
Partner defaults for sale, purchase
Improve the domain and context to customers/suppliers menu
1.Customer,Supplier menu: only show companies
2.Only the customers with company can be select in sales order
3.Only the suppliers with company can be select in purchase order
4.Set 'is company' to true in customer,supplier menu list create new data.
    """,

    'depends': ['sale','purchase'],
    'data':[
     'partner_comp_supp_cust.xml',
    ],
    'auto_install': False,
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
