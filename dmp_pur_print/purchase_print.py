# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from dateutil.relativedelta import relativedelta
import time
import datetime
from openerp import netsvc
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from openerp.osv import fields,osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.addons.purchase import purchase
from openerp import pooler

#redefine the purchase PDF report to new rml
from openerp.addons.purchase.report.order import order
from openerp.report import report_sxw

class dmp_pur_order(order):
    def __init__(self, cr, uid, name, context):
        super(order, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'get_taxes_name':self._get_tax_name})
        self.localcontext.update({'get_boolean_name':self._get_boolean_name})
    #get the taxes name             
    def _get_tax_name(self,taxes_id):
        names = ''
        for tax in taxes_id:
            names += ", " + tax.name
        if names != '': 
            names = names[2:]
        return names      
    def _get_boolean_name(self,bool_val):
#        def _get_source(self, cr, uid, name, types, lang, source=None):
        bool_name = self.pool.get("ir.translation")._get_source(self.cr, self.uid, None, 'code', self.localcontext['lang'], 'bool_' + str(bool_val))
        return bool_name
          
report_sxw.report_sxw('report.purchase.order.dmp','purchase.order','addons/dmp_pur_print/report/purchase_order.rml',parser=dmp_pur_order)
report_sxw.report_sxw('report.purchase.quotation.dmp','purchase.order','addons/dmp_pur_print/report/purchase_quotation.rml',parser=dmp_pur_order)

