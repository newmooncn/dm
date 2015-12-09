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
	
#	def _get_main_product_customer(self, cr, uid, product, context=None):
#		"""Determines the main (best) product customer for ``product``,
#		returning the corresponding ``customerinfo`` record, or False
#		if none were found. The default strategy is to select the
#		customer with the highest priority (i.e. smallest sequence).
#
#		:param browse_record product: product to sell
#		:rtype: product.customerinfo browse_record or False
#		"""
#		customers = [(customer_info.sequence, customer_info)
#					   for customer_info in product.customer_ids or []
#					   if customer_info and isinstance(customer_info.sequence, (int, long))]
#		return customers and customers[0][1] or False
#		
#	def _calc_customer(self, cr, uid, ids, fields, arg, context=None):
#		result = {}
#		for product in self.browse(cr, uid, ids, context=context):
#			main_customer = self._get_main_product_customer(cr, uid, product, context=context)
#			main_customer_code = main_customer and (main_customer.product_code and '[%s]'%(main_customer.product_code) or '') or ''
#			main_customer_name = main_customer and main_customer.product_name or ''
#			main_customer_name = '%s%s'%(main_customer_code, main_customer_name)
#			result[product.id] = {
#				'customer_info_id': main_customer and main_customer.id or False,
#				'customer_delay': main_customer.delay if main_customer else 1,
#				'customer_id': main_customer and main_customer.name.id or False,
#				'customer_product_name': main_customer_name
#			}
#		return result
	
	def _get_customer(self, cr, uid, ids, context=None):
		result = {}
		#self is product.supplierinfo not product.product
		for line in self.browse(cr, uid, ids, context=context):
			result[line.product_id.id] = True
		return result.keys()
		
	_columns = {
        #product customers, like seller_ids link to the product.supplierinfo
        'customer_ids': fields.one2many('product.customerinfo', 'product_id', 'Customer'),		
#		'customer_info_id': fields.function(_calc_customer, type='many2one', relation="product.customerinfo", string="Customer Info", multi="customer_info"),
		'customer_id': fields.related('customer_ids','name', type='many2one', relation='res.partner', string='Main Customer',
			store={'product.customerinfo': (_get_customer, None, 10)},
			help="Main Customer who has highest priority in Customer List."),
		'customer_delay': fields.related('customer_ids', 'delay', type='integer', string='Customer Lead Time'),
		'customer_product_code': fields.related('customer_ids','product_code', type='char', string='Customer Product Code',
			store={'product.customerinfo': (_get_customer, None, 10),}),
		'customer_product_name': fields.related('customer_ids','product_name', type='char', string='Customer Product Name',
			store={'product.customerinfo': (_get_customer, None, 10),}),
	}
	
#	def _get_customer_info(self, cr, uid, customer_id, product_id, context=None):
#		if isinstance(product_id,(int,long)):
#			product_id = self.pool.get("product.product").browse(cr, uid, product_id, context=context)
#		for customer_info in product_id.customer_ids:
#				return customer_info
#		return False
#	
#	def get_customer_product(self, cr, uid, customer_id, product_id, context=None):
#		customer_info = self._get_customer_info(cr, uid, customer_id, product_id, context=context)
#		customer_product_name=""
#		if customer_info and customer_info.name.id == customer_id:
#			customer_product_name += (customer_info.product_code and '[%s]'%(customer_info.product_code,) or '')
#			customer_product_name += customer_info.product_name
#		return customer_product_name
#	
#	def create(self, cr, uid, vals, context=None):
#		if vals.get('customer_ids'):
#			#[(0,0,{dict values}),(0,0,{dict values}),(0,0,{dict values})]
#			cust_info = vals['customer_ids'][0][2]
#			cust_product_code = cust_info['product_code'] and '[%s]'%(cust_info['product_code']) or ''
#			cust_product_name = cust_info['product_name'] and cust_info['product_name'] or ''
#			cust_product_name = '%s%s'%(cust_product_code, cust_product_name)
#			vals['customer_product_name'] = cust_product_name
#		return super(product_product,self).create(cr, uid, vals, context=context)

	def get_customer_product_info(self, cr, uid, customer_id, product_id, context=None):
		cust_prod_obj = self.pool['product.customerinfo']
		customer_prod_ids = cust_prod_obj.search(cr, uid, [('name','=', customer_id),('product_id','=', product_id)],context=context)
		resu = {}
		if customer_prod_ids:
			resu = cust_prod_obj.read(cr, uid, customer_prod_ids[0],['product_name','product_code','price'],context=context)
		return resu
	
	def get_customer_product(self, cr, uid, customer_id, product_id, context=None):
		cust_prod_obj = self.pool['product.customerinfo']
		customer_prod_ids = cust_prod_obj.search(cr, uid, [('name','=', customer_id),('product_id','=', product_id)],context=context)
		cust_prod = None
		if customer_prod_ids:
			cust_prod = cust_prod_obj.browse(cr, uid, customer_prod_ids[0],context=context)
		return cust_prod
	
	def _create_prod_customer(self, cr, uid, prod_id, vals, context=None):
		if not prod_id:
			return
		if vals.get('customer_id'):
			prod = self.browse(cr,uid,prod_id,context=context)
			#if there are no customers added, then need add one to customer list
			if not prod.customer_ids:
				vals_new = {'product_id':prod_id, 'name':vals['customer_id']}
				if vals.get('customer_product_name'):
					vals_new['product_name'] = vals.get('customer_product_name')
				self.pool['product.customerinfo'].create(cr, uid,vals_new,context=context)
		
	def create(self, cr, uid, vals, context=None):
		new_id = super(product_product,self).create(cr, uid, vals, context=context)
		self._create_prod_customer(cr, uid, new_id, vals, context=context)
		return new_id
	
	def write(self, cr, uid, ids, vals, context=None):
		resu = super(product_product,self).write(cr, uid, ids, vals, context=context)		
		self._create_prod_customer(cr, uid, ids[0], vals, context=context)
		return resu
		
	#Add customer_product_name search
	def _name_search_domain(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
		name_domain = super(product_product,self)._name_search_domain(cr, user, name, args, operator, context, limit)
		name_domain += [('customer_product_name',operator,name)]
		return name_domain
					
product_product()


class product_customerinfo(osv.osv):
	_name = "product.customerinfo"
	_description = "Information about a product customer"
	_columns = {
        'name' : fields.many2one('res.partner', 'Customer', required=True,domain = [('customer','=',True),('is_company','=',True)], ondelete='cascade'),
        'product_name': fields.char('Customer Product Name', size=128),
        'product_code': fields.char('Customer Product Code', size=64),
        'sequence' : fields.integer('Sequence', help="Assigns the priority to the list of product customer."),
        'product_id' : fields.many2one('product.product', 'Product', required=False, ondelete='cascade', select=True),
        'delay' : fields.integer('Delivery Lead Time', required=True),
        'company_id':fields.many2one('res.company','Company',select=1),
        'price': fields.float('Unit Price', required=False, digits_compute=dp.get_precision('Product Price')),
    }
	_defaults = {
        'sequence': lambda *a: 1,
        'delay': lambda *a: 1,
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'product.customerinfo', context=c),
    }
	_order = 'sequence'

product_customerinfo()