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
from openerp.osv import fields,osv
          
class stock_picking(osv.osv):
    _inherit = "stock.picking"        
    #warehouse_id are allocated in purchase module, one field related to purchase_order.warehouse_id 
    _columns = {   
        'warehouse_origin_id': fields.many2one('stock.warehouse', 'Original Warehouse'),
        'warehouse_dest_id': fields.many2one('stock.warehouse', 'Destination Warehouse'),
    }     
    def onchange_warehouse_origin_id(self, cr, uid, ids, warehouse_id):
        if not warehouse_id:
            return {}
        warehouse = self.pool.get('stock.warehouse').browse(cr, uid, warehouse_id)
        return {'value':{'location_id': warehouse.lot_stock_id.id, 'dest_address_id': False}}    
    def onchange_warehouse_dest_id(self, cr, uid, ids, warehouse_id):
        if not warehouse_id:
            return {}
        warehouse = self.pool.get('stock.warehouse').browse(cr, uid, warehouse_id)
        return {'value':{'location_dest_id': warehouse.lot_input_id.id, 'dest_address_id': False}}

class stock_picking_in(osv.osv):
    _inherit = "stock.picking.in"         
    _columns = {   
        'warehouse_origin_id': fields.many2one('stock.warehouse', 'Original Warehouse'),
        'warehouse_dest_id': fields.many2one('stock.warehouse', 'Destination Warehouse'),
    }     
    def onchange_warehouse_origin_id(self, cr, uid, ids, warehouse_id):
        return self.pool.get('stock.picking').onchange_warehouse_origin_id(cr, uid, ids, warehouse_id)    
    def onchange_warehouse_dest_id(self, cr, uid, ids, warehouse_id):
        return self.pool.get('stock.picking').onchange_warehouse_dest_id(cr, uid, ids, warehouse_id)
    
    def _update_warehouse(self, cr, uid, vals, context=None):
        if 'warehouse_id' in vals and 'warehouse_dest_id' not in vals:
            vals['warehouse_dest_id'] = vals['warehouse_id']
            vals['location_dest_id'] = self.pool.get('stock.warehouse').browse(cr, uid, vals['warehouse_id'], context=context).lot_input_id.id
        elif 'warehouse_dest_id' in vals and 'warehouse_id' not in vals:
            vals['warehouse_id'] = vals['warehouse_dest_id']
            
    def create(self, cr, uid, vals, context=None):
        self._update_warehouse(cr, uid, vals, context=context)            
        return super(stock_picking_in, self).create(cr, uid, vals, context=context)
    
    def write(self, cr, uid, ids, vals, context=None):
        self._update_warehouse(cr, uid, vals, context=context)
        return super(stock_picking_in, self).create(cr, uid, ids, vals, context=context)
    
class stock_picking_out(osv.osv):
    _inherit = "stock.picking.out"         
    _columns = {   
        'warehouse_origin_id': fields.many2one('stock.warehouse', 'Original Warehouse'),
        'warehouse_dest_id': fields.many2one('stock.warehouse', 'Destination Warehouse'),
    } 
    def onchange_warehouse_origin_id(self, cr, uid, ids, warehouse_id):
        return self.pool.get('stock.picking').onchange_warehouse_origin_id(cr, uid, ids, warehouse_id)    
    def onchange_warehouse_dest_id(self, cr, uid, ids, warehouse_id):
        return self.pool.get('stock.picking').onchange_warehouse_dest_id(cr, uid, ids, warehouse_id)   
                
class stock_move(osv.osv):
    _inherit = "stock.move"         
    _columns = {   
        'uom_categ_id': fields.related('product_uom','category_id',type='many2one',relation='product.uom.categ',String="UOM Category"),
    } 
    
    def onchange_product_id(self, cr, uid, ids, prod_id=False, loc_id=False,
                            loc_dest_id=False, partner_id=False):    
        '''
        Add the uom_categ_id, johnw, 04/29/2015
        '''
        res = super(stock_move, self).onchange_product_id(cr, uid, ids, prod_id, loc_id, loc_dest_id, partner_id)
        product = self.pool.get('product.product').browse(cr, uid, prod_id)
        if res['value'].get('product_uom') and res['value']['product_uom'] != product.uom_id.id:
            #if user changed product, then need to change to new product's uom, this is an issue in addons/stock.py
            res['value']['product_uom'] = product.uom_id.id     
        #if there is a partner then
#        if partner_id:
#            res['value']['product_uom'] = product.uom_po_id.id
                       
        res['value']['uom_categ_id'] = product.uom_id.category_id.id
        return res  