# -*- coding: utf-8 -*-
##############################################################################
# OpenERP Connector
# Copyright 2013 DMEMS <johnw@dmems.com>
##############################################################################

import time
from openerp.report import report_sxw
from openerp.osv import osv

class dm_rubylong_sale_order(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(dm_rubylong_sale_order, self).__init__(cr, uid, name, context=context)
        # self.page_size = 'half'#页面大小 分全屏[Full Screen]，半页[Half Page]
        self.localcontext.update({
            'time': time,
            'cr':cr,
            'uid': uid,
            # 'page_size':self._page_size,
        })

report_sxw.report_sxw(
    'report.dm_rubylong_sale_order',
    'sale.order',
    'addons/dm_rubylong_sale_order_T/report/dm_rubylong_sale_order.mako',
    parser=dm_rubylong_sale_order)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
