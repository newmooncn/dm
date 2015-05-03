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
	def _calc_seller(self, cr, uid, ids, fields, arg, context=None):
		result = {}
		for product in self.browse(cr, uid, ids, context=context):
			main_supplier = self._get_main_product_supplier(cr, uid, product, context=context)
			result[product.id] = {
				'seller_info_id': main_supplier and main_supplier.id or False,
				'seller_delay': main_supplier.delay if main_supplier else 1,
				'seller_qty': main_supplier and main_supplier.qty or 0.0,
				'seller_id': main_supplier and main_supplier.name.id or False,
				'seller_product_code': main_supplier and main_supplier.product_code or '',
				'seller_product_name': main_supplier and main_supplier.product_name or ''
			}
		return result
	
	def _get_seller(self, cr, uid, ids, context=None):
		result = {}
		#self is product.supplierinfo not product.product
		for line in self.browse(cr, uid, ids, context=context):
			product_ids = self.pool.get('product.product').search(cr, uid, [('product_tmpl_id','=',line.product_id.id)], context=context)
			if product_ids:
				result[product_ids[0]] = True
		return result.keys()
		
	_columns = {
		'seller_info_id': fields.function(_calc_seller, type='many2one', relation="product.supplierinfo", string="Supplier Info", multi="seller_info"),
		'seller_delay': fields.function(_calc_seller, type='integer', string='Supplier Lead Time', multi="seller_info", help="This is the average delay in days between the purchase order confirmation and the reception of goods for this product and for the default supplier. It is used by the scheduler to order requests based on reordering delays."),
		'seller_qty': fields.function(_calc_seller, type='float', string='Supplier Quantity', multi="seller_info", help="This is minimum quantity to purchase from Main Supplier."),
		'seller_id': fields.function(_calc_seller, type='many2one', relation="res.partner", string='Main Supplier', help="Main Supplier who has highest priority in Supplier List.", multi="seller_info"),
		#johnw, 05/03/2015, add supplier product code and name
		'seller_product_code': fields.function(_calc_seller, type='char', size=64, string='Supplier Product Code', multi="seller_info"),
		'seller_product_name': fields.function(_calc_seller, type='char', size=128, string='Supplier Product Name', multi="seller_info", 
				store={
                'product.supplierinfo': (_get_seller, None, 10),
            }),
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
				
product_product()