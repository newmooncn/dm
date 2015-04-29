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
	
	def get_supplier_product(self, cr, uid, supplier_id, product_id, context=None):
		"""Determines the main (best) product supplier for ``product``,
		returning the corresponding ``product_supplierinfo`` record, or False
		if none were found. The default strategy is to select the
		customer with the highest priority (i.e. smallest sequence).
		
		:param browse_record product: product to sell
		:rtype: product.customerinfo browse_record or False
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