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

from openerp.osv import fields, osv

class product_product(osv.osv):
	_inherit = "product.product"
#	def _calc_seller(self, cr, uid, ids, fields, arg, context=None):
#		result = {}
#		for product in self.browse(cr, uid, ids, context=context):
#			main_supplier = self._get_main_product_supplier(cr, uid, product, context=context)
#			seller_product_code = main_supplier and (main_supplier.product_code and '[%s]'%(main_supplier.product_code) or '') or ''
#			seller_product_name = main_supplier and main_supplier.product_name or ''
#			seller_product_name = '%s%s'%(seller_product_code, seller_product_name)
#			result[product.id] = {
#				'seller_info_id': main_supplier and main_supplier.id or False,
#				'seller_delay': main_supplier.delay if main_supplier else 1,
#				'seller_qty': main_supplier and main_supplier.qty or 0.0,
#				'seller_id': main_supplier and main_supplier.name.id or False,
#				'seller_product_name': seller_product_name
#			}
#		return result
#	
	def _get_seller(self, cr, uid, ids, context=None):
		result = {}
		#self is product.supplierinfo not product.product
		for line in self.browse(cr, uid, ids, context=context):
			product_ids = self.pool.get('product.product').search(cr, uid, [('product_tmpl_id','=',line.product_tmpl_id.id)], context=context)
			if product_ids:
				result[product_ids[0]] = True
		return result.keys()
		
	_columns = {
		#johnw, 05/03/2015, add supplier product code and name
		'seller_id': fields.related('seller_ids','name', type='many2one', relation='res.partner', string='Main Supplier',
			store={'product.supplierinfo': (_get_seller, None, 10)},
			help="Main Supplier who has highest priority in Supplier List."),
		'seller_product_name': fields.related('seller_ids','product_name', type='char', string='Supplier Product Name',
			store={'product.supplierinfo': (_get_seller, None, 10),}),
	}  
		
	def get_supplier_product(self, cr, uid, supplier_id, product_id, context=None):
		"""
		Get supplier product name, used by PDF
		"""
		supplier_product_name=""
		if isinstance(product_id,(int,long)):
			product_id = self.pool.get("product.product").browse(cr, uid, product_id, context=context)
		for supplier_info in product_id.seller_ids:
			if supplier_info and supplier_info.name.id == supplier_id:
				supplier_product_name += (supplier_info.product_code and '[%s]'%(supplier_info.product_code,) or '')
				supplier_product_name += supplier_info.product_name
		return supplier_product_name
	
	def get_supplier_product_data(self, cr, uid, supplier_id, product_id, context=None):
		if isinstance(product_id,(int,long)):
			product_id = self.pool.get("product.product").browse(cr, uid, product_id, context=context)
		supplier_product_name = ""
		supplier_product_price = 0.0
		for supplier_info in product_id.seller_ids:
			if supplier_info and supplier_info.name.id == supplier_id:
				supplier_product_name += (supplier_info.product_code and '[%s]'%(supplier_info.product_code,) or '')
				supplier_product_name += supplier_info.product_name
				if supplier_info.pricelist_ids:
					for price in supplier_info.pricelist_ids:
						supplier_product_price = price.price
		return supplier_product_name, supplier_product_price
	
#	def create(self, cr, uid, vals, context=None):
#		if vals.get('seller_ids'):
#			#[(0,0,{dict values}),(0,0,{dict values}),(0,0,{dict values})]
#			sup_info = vals['seller_ids'][0][2]
#			seller_product_code = sup_info['product_code'] and '[%s]'%(sup_info['product_code']) or ''
#			seller_product_name = sup_info['product_name'] and sup_info['product_name'] or ''
#			seller_product_name = '%s%s'%(seller_product_code, seller_product_name)
#			vals['seller_product_name'] = seller_product_name
#		return super(product_product,self).create(cr, uid, vals, context=context)

	def _create_prod_supplier(self, cr, uid, prod_id, vals, context=None):
		if not prod_id:
			return
		if vals.get('seller_id'):
			prod = self.browse(cr,uid,prod_id,context=context)
			#if there are no customers added, then need add one to customer list
			if not prod.seller_ids:
				vals_new = {'product_tmpl_id':prod.product_tmpl_id.id, 'name':vals['seller_id']}
				if vals.get('seller_product_name'):
					vals_new['product_name'] = vals.get('seller_product_name')
				self.pool['product.supplierinfo'].create(cr, uid,vals_new,context=context)
				
	def create(self, cr, uid, vals, context=None):
		new_id = super(product_product,self).create(cr, uid, vals, context=context)
		self._create_prod_supplier(cr, uid, new_id, vals, context=context)
		return new_id
	
	def write(self, cr, uid, ids, vals, context=None):
		resu = super(product_product,self).write(cr, uid, ids, vals, context=context)		
		self._create_prod_supplier(cr, uid, ids[0], vals, context=context)
		return resu

	#Add customer_product_name search
	def _name_search_domain(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
		name_domain = super(product_product,self)._name_search_domain(cr, user, name, args, operator, context, limit)
		name_domain += [('seller_product_name',operator,name)]
		return name_domain
				
product_product()