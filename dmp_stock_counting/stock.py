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
from openerp.osv import fields,osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
          
class stock_inventory(osv.osv):
    _inherit = "stock.inventory"
    _order = "id desc"
    _columns = {
        'comments': fields.text('Comments', size=64, readonly=False, states={'done': [('readonly', True)]}),
        'create_uid': fields.many2one('res.users', 'Creator',readonly=True),        
    }
    def unlink(self, cr, uid, ids, context=None):
        inventories = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for s in inventories:
            if s['state'] in ['draft','cancel']:
                unlink_ids.append(s['id'])
            else:
                raise osv.except_osv(_('Invalid Action!'), _('Only the physical inventory orders with Draft or Cancelled state can be delete!'))

        return super(stock_inventory, self).unlink(cr, uid, unlink_ids, context=context)
        
class stock_inventory_line(osv.osv):
    _inherit = "stock.inventory.line"
    _columns = {   
        'image_medium': fields.related('product_id','image_medium',type='binary',String="Medium-sized image"),
        'state': fields.related('inventory_id','state',type='selection',selection=(('draft', 'Draft'), ('cancel','Cancelled'), ('confirm','Confirmed'), ('done', 'Done')),
                                string='Status',readonly=True),
        'uom_categ_id': fields.related('product_uom','category_id',type='many2one',relation='product.uom.categ',String="UOM Category"),
    }
    #override the parent's _default_stock_location, to avoid the location reading right issue under multi company's environment 
    def _default_stock_location(self, cr, uid, context=None):
        loc_ids = self.pool.get('stock.location').search(cr, uid, [('usage','=','internal')], context=context)
        if loc_ids:
            return loc_ids[0]
        else:
            return False

    _defaults = {
        'location_id': _default_stock_location
    }    

    def on_change_product_id(self, cr, uid, ids, location_id, product_id, uom=False, to_date=False):
        '''
        Add the uom_categ_id, johnw, 01/07/2015
        '''
        res = super(stock_inventory_line, self).on_change_product_id(cr, uid, ids, location_id, product_id, uom, to_date)
        if not product_id:
            return res        
        product = self.pool.get('product.product').browse(cr, uid, product_id)
        if res['value'].get('product_uom') and res['value']['product_uom'] != product.uom_id.id:
            #if user changed product, then need to change to new product's uom, this is an issue in addons/stock.py
            res['value']['product_uom'] = product.uom_id.id        
        res['value']['uom_categ_id'] = product.uom_id.category_id.id
        return res  