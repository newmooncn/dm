# -*- coding: utf-8 -*-
##############################################################################
# OpenERP Connector
# Copyright 2013 DMEMS <johnw@dmems.com>
##############################################################################

{
    'name': 'dm rubylong sale.order',
    'summary': '锐浪报表 销售订单',
    'version': '1.0',
    'category': 'report',
    'sequence': 21,
    'author': 'DMEMS',
    'website': 'http://www.dmems.com',
    'images': [''],
   'depends': ['base', 'dm_rubylong'],
    'data': [
        'dm_rubylong_sale_order_T_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'description': """
    使用时下载 Grid++Report  官方网站：http://www.rubylong.cn
""",
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
