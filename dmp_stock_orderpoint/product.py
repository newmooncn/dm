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
from openerp.tools.translate import _
	
class product_product(osv.osv):
	_inherit = "product.product"
	
	_columns = {
		'safe_qty': fields.float('Minimal Inventory'),
		'safe_warn': fields.boolean('Safe Warn'),
		'max_qty': fields.float('Maximal Inventory'),
		#实施上述库存大小最则的库位
		'property_prod_loc': fields.property('stock.location', type='many2one', relation='stock.location', string="Location", view_load=True, ),		
	}
	
	#auto update order point by the product min/max qty fields
	def _orderpoint_update(self, cr, uid, ids, vals, context=None):
		if 'safe_qty' in vals or 'max_qty' in vals or 'property_prod_loc' in vals:
			wh_obj = self.pool.get('stock.warehouse')
			op_obj = self.pool.get('stock.warehouse.orderpoint')
			
			min_qty_new = -1
			if 'safe_qty' in vals:
				min_qty_new = vals['safe_qty']
			max_qty_new = 0
			if 'max_qty' in vals:
				max_qty_new = vals['max_qty']
			location_id_new = 'property_prod_loc' in vals and vals['property_prod_loc'] or -1
			upt_op_ids = []
			for prod in self.browse(cr, uid, ids, context=context):
				min_qty = min_qty_new < 0 and prod.safe_qty or min_qty_new
				max_qty = max_qty_new < 0 and prod.max_qty or max_qty_new
				if min_qty < 0 or max_qty < 0:
					raise osv.except_osv(_('Error'), _('[%s]%s minimal or maximal quantity can not be negative!')%(prod.default_code, prod.name))
				location_id = location_id_new
				if location_id <= 0:
					location_id = prod.property_prod_loc
					if location_id:
						location_id = location_id.id
				if not prod.orderpoint_ids:
					#for new order point, must have min qty and loc, otherwise then miss it.
					if min_qty < 0 or location_id <= 0:
						continue
					wh_ids = wh_obj.search(cr, uid, [('lot_stock_id','=',location_id)],context=context)
					op_vals = {'product_id':prod.id,
							'product_uom':prod.uom_id.id,
							'product_min_qty':min_qty, 
							'product_max_qty':max_qty,
							'warehouse_id':wh_ids and wh_ids[0] or False,
							'location_id':location_id,
							}
					op_obj.create(cr, uid, op_vals, context=context)
				else:
					upt_op_ids.append(prod.orderpoint_ids[0].id)
			#update the order point
			if upt_op_ids:
				upt_vals = {}
				if min_qty >= 0:
					upt_vals.update({'product_min_qty':min_qty})
				if max_qty >= 0:
					upt_vals.update({'product_max_qty':max_qty})
				if location_id > 0:
					upt_vals.update({'location_id':location_id})
				op_obj.write(cr, uid, upt_op_ids, upt_vals, context=context)
		return True
	
	def create(self, cr, uid, vals, context=None):
		new_id = super(product_product, self).create(cr, uid, vals, context)
		self._orderpoint_update(cr, uid, [new_id], vals, context)
		return new_id
	
	def write(self, cr, uid, ids, vals, context=None):
		resu = super(product_product, self).write(cr, uid, ids, vals, context=context)
		self._orderpoint_update(cr, uid, ids, vals, context)
		return resu
				
product_product()