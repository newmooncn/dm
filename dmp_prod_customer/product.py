# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP S.A. <http://www.openerp.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

import re
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.addons.dm_base.utils import deal_args_dt
import openerp.addons.decimal_precision as dp
	
class product_product(osv.osv):
	_inherit = "product.product"
	
	def _get_main_product_customer(self, cr, uid, product, context=None):
		"""Determines the main (best) product customer for ``product``,
		returning the corresponding ``customerinfo`` record, or False
		if none were found. The default strategy is to select the
		customer with the highest priority (i.e. smallest sequence).

		:param browse_record product: product to sell
		:rtype: product.customerinfo browse_record or False
		"""
		customers = [(customer_info.sequence, customer_info)
					   for customer_info in product.customer_ids or []
					   if customer_info and isinstance(customer_info.sequence, (int, long))]
		return customers and customers[0][1] or False
		
	def _calc_customer(self, cr, uid, ids, fields, arg, context=None):
		result = {}
		for product in self.browse(cr, uid, ids, context=context):
			main_customer = self._get_main_product_customer(cr, uid, product, context=context)
			result[product.id] = {
				'customer_info_id': main_customer and main_customer.id or False,
				'customer_delay': main_customer.delay if main_customer else 1,
				'customer_id': main_customer and main_customer.name.id or False
			}
		return result
		
	_columns = {
        #product customers, like seller_ids link to the product.supplierinfo
        'customer_ids': fields.one2many('product.customerinfo', 'product_id', 'Customer'),		
		'customer_info_id': fields.function(_calc_customer, type='many2one', relation="product.customerinfo", string="Customer Info", multi="customer_info"),
		'customer_delay': fields.function(_calc_customer, type='integer', string='Supplier Lead Time', multi="customer_info"),
		'customer_id': fields.function(_calc_customer, type='many2one', relation="res.partner", multi="customer_info", string='Main Supplier', help="Main customer who has highest priority in Customer List."),
        
	}
	
	def get_customer_product(self, cr, uid, customer_id, product_id, context=None):
		"""Determines the main (best) product customer for ``product``,
		returning the corresponding ``customerinfo`` record, or False
		if none were found. The default strategy is to select the
		customer with the highest priority (i.e. smallest sequence).
		
		:param browse_record product: product to sell
		:rtype: product.customerinfo browse_record or False
		"""
		customer_product_name=""
		if isinstance(product_id,(int,long)):
			product_id = self.pool.get("product.product").browse(cr, uid, product_id, context=context)
		for customer_info in product_id.customer_ids:
			if customer_info and customer_info.name.id == customer_id:
				customer_product_name += (customer_info.product_code and '[%s]'%(customer_info.product_code,) or '')
				customer_product_name += customer_info.product_name
		return customer_product_name
				
product_product()


class product_customerinfo(osv.osv):
	_name = "product.customerinfo"
	_description = "Information about a product customer"
	_columns = {
        'name' : fields.many2one('res.partner', 'Customer', required=True,domain = [('customer','=',True),('is_company','=',True)], ondelete='cascade'),
        'product_name': fields.char('Customer Product Name', size=128),
        'product_code': fields.char('Customer Product Code', size=64),
        'sequence' : fields.integer('Sequence', help="Assigns the priority to the list of product supplier."),
        'product_id' : fields.many2one('product.product', 'Product', required=False, ondelete='cascade', select=True),
        'delay' : fields.integer('Delivery Lead Time', required=True),
        'company_id':fields.many2one('res.company','Company',select=1),
    }
	_defaults = {
        'sequence': lambda *a: 1,
        'delay': lambda *a: 1,
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'product.customerinfo', context=c),
    }
	_order = 'sequence'

product_customerinfo()