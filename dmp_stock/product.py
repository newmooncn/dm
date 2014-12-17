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
import openerp.addons.decimal_precision as dp
	
class product_product(osv.osv):
	_inherit = "product.product"
	
	def _get_move_products(self, cr, uid, ids, context=None):
		res = set()
		move_obj = self.pool.get("stock.move")
		for move in move_obj.browse(cr, uid, ids, context=context):
			res.add(move.product_id.id)
		return res

	def rpc_product_available(self, cr, uid, ids, field_names=None, arg=False, context=None):
		res = self._product_available(cr, uid, ids, field_names, arg, context)
		rpc_res = {}
		#convert the ket of dictory yo string, since the dumps() method in below code only allow the string key in dictory.
		#openerp/service/wsgi_server.py
		#response = xmlrpclib.dumps((result,), methodresponse=1, allow_none=False, encoding=None)
		for id in ids:
			rpc_res['%s'%id] = res[id]
		return rpc_res
	'''
	def _product_partner_ref(self, cr, uid, ids, name, arg, context=None):
		res = {}
		if context is None:
			context = {}
		names = self.name_get(cr, uid, ids, context=context)
		for name in names:
			res[name[0]] = name[1]
		return res		
	'''
	def _product_available(self, cr, uid, ids, field_names=None, arg=False, context=None):
		""" Finds the incoming and outgoing quantity of product.
		@return: Dictionary of values
		"""
		if not field_names:
			field_names = []
		if context is None:
			context = {}
		res = {}
		for id in ids:
			res[id] = {}.fromkeys(field_names, 0.0)
		for f in field_names:
			c = context.copy()
			'''
			add the columns(qty_onhand,qty_virtual,qty_in,qty_out)
			display on GUI for user sort and query, johnw, 12/17/2014
			'''
			if f in ('qty_available','qty_onhand'):
				c.update({ 'states': ('done',), 'what': ('in', 'out') })
			if f in ('virtual_available','qty_virtual'):
				c.update({ 'states': ('confirmed','waiting','assigned','done'), 'what': ('in', 'out') })
			if f in ('incoming_qty','qty_in'):
				c.update({ 'states': ('confirmed','waiting','assigned'), 'what': ('in',) })
			if f in ('outgoing_qty','qty_out'):
				c.update({ 'states': ('confirmed','waiting','assigned'), 'what': ('out',) })
			stock = self.get_product_available(cr, uid, ids, context=c)
			for id in ids:
				res[id][f] = stock.get(id, 0.0)
		return res		
	
	_columns = {
		'safe_qty': fields.float('Minimal Inventory'),
		'safe_warn': fields.boolean('Safe Warn'),
		'max_qty': fields.float('Maximal Inventory'),
		#实施上述库存大小最则的库位
		'property_prod_loc': fields.property('stock.location', type='many2one', relation='stock.location', string="Location", view_load=True, ),		
		'loc_pos_code': fields.char('Storage Position Code',size=16),
		'is_print_barcode': fields.boolean('Print barcode label'),
        #add the field qty_onhand, qty_virtual, qty_in, qty_out, to store them into database, then user can sort and query them on GUI
        #they are corresponding to the original columns: qty_available, virtual_available, incoming_qty, outgoing_qty
        #replace the xml view with the new columns, and other program also read from the original qty function columns
		'qty_onhand': fields.function(_product_available, multi='qty_available',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Quantity On Hand',
             store = {'stock.move': (_get_move_products, ['product_qty', 'location_id', 'location_dest_id', 'state'], 10),
					'material.request.line': (_get_move_products, ['product_qty', 'location_id', 'location_dest_id', 'state'], 10)}
			 ),
		'qty_virtual': fields.function(_product_available, multi='qty_available',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Forecasted Quantity',
             store = {'stock.move': (_get_move_products, ['product_qty', 'location_id', 'location_dest_id', 'state'], 10),
					'material.request.line': (_get_move_products, ['product_qty', 'location_id', 'location_dest_id', 'state'], 10)}
             ),
		'qty_in': fields.function(_product_available, multi='qty_available',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Incoming',
             store = {'stock.move': (_get_move_products, ['product_qty', 'location_id', 'location_dest_id', 'state'], 10),
					'material.request.line': (_get_move_products, ['product_qty', 'location_id', 'location_dest_id', 'state'], 10)}
             ),
		'qty_out': fields.function(_product_available, multi='qty_available',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Outgoing',
             store = {'stock.move': (_get_move_products, ['product_qty', 'location_id', 'location_dest_id', 'state'], 10),
					'material.request.line': (_get_move_products, ['product_qty', 'location_id', 'location_dest_id', 'state'], 10)}
             ),		
		'qty_available': fields.function(_product_available, multi='qty_available',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Quantity On Hand(FUNC)',
			help="Current quantity of products.\n"
				 "In a context with a single Stock Location, this includes "
				 "goods stored at this Location, or any of its children.\n"
				 "In a context with a single Warehouse, this includes "
				 "goods stored in the Stock Location of this Warehouse, or any "
				 "of its children.\n"
				 "In a context with a single Shop, this includes goods "
				 "stored in the Stock Location of the Warehouse of this Shop, "
				 "or any of its children.\n"
				 "Otherwise, this includes goods stored in any Stock Location "
				 "with 'internal' type."),
		'virtual_available': fields.function(_product_available, multi='qty_available',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Forecasted Quantity(FUNC)',
			help="Forecast quantity (computed as Quantity On Hand "
				 "- Outgoing + Incoming)\n"
				 "In a context with a single Stock Location, this includes "
				 "goods stored in this location, or any of its children.\n"
				 "In a context with a single Warehouse, this includes "
				 "goods stored in the Stock Location of this Warehouse, or any "
				 "of its children.\n"
				 "In a context with a single Shop, this includes goods "
				 "stored in the Stock Location of the Warehouse of this Shop, "
				 "or any of its children.\n"
				 "Otherwise, this includes goods stored in any Stock Location "
				 "with 'internal' type."),
		'incoming_qty': fields.function(_product_available, multi='qty_available',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Incoming(FUNC)',
			help="Quantity of products that are planned to arrive.\n"
				 "In a context with a single Stock Location, this includes "
				 "goods arriving to this Location, or any of its children.\n"
				 "In a context with a single Warehouse, this includes "
				 "goods arriving to the Stock Location of this Warehouse, or "
				 "any of its children.\n"
				 "In a context with a single Shop, this includes goods "
				 "arriving to the Stock Location of the Warehouse of this "
				 "Shop, or any of its children.\n"
				 "Otherwise, this includes goods arriving to any Stock "
				 "Location with 'internal' type."),
		'outgoing_qty': fields.function(_product_available, multi='qty_available',
			type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
			string='Outgoing(FUNC)',
			help="Quantity of products that are planned to leave.\n"
				 "In a context with a single Stock Location, this includes "
				 "goods leaving this Location, or any of its children.\n"
				 "In a context with a single Warehouse, this includes "
				 "goods leaving the Stock Location of this Warehouse, or "
				 "any of its children.\n"
				 "In a context with a single Shop, this includes goods "
				 "leaving the Stock Location of the Warehouse of this "
				 "Shop, or any of its children.\n"
				 "Otherwise, this includes goods leaving any Stock "
				 "Location with 'internal' type."),			
	}
	
	#auto update order point by the product min/max qty fields
	def _orderpoint_update(self, cr, uid, ids, vals, context=None):
		if 'safe_qty' in vals or 'max_qty' in vals or 'property_prod_loc' in vals:
			wh_obj = self.pool.get('stock.warehouse')
			op_obj = self.pool.get('stock.warehouse.orderpoint')
			
			min_qty = 'safe_qty' in vals and vals['safe_qty'] or -1
			max_qty = 'max_qty' in vals and vals['max_qty'] or 0
			location_id = 'property_prod_loc' in vals and vals['property_prod_loc'] or -1
			upt_op_ids = []
			for prod in self.browse(cr, uid, ids, context=context):
				if location_id <= 0:
					location_id = prod.property_prod_loc
					if location_id:
						location_id = location_id.id
				if not prod.orderpoint_ids:
					#for new order point, must have min qty and loc, otherwise then miss it.
					if min_qty <= 0 or location_id <= 0:
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
				if min_qty > 0:
					upt_vals.update({'product_min_qty':min_qty})
				if max_qty > 0:
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
		
	def print_barcode(self,cr,uid,ids,context=None):
		self.write(cr,uid,ids,{'is_print_barcode':context.get("print_flag")})
		return True
				
product_product()