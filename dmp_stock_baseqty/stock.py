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
          
class stock_move(osv.osv):
    _inherit = "stock.move" 
    def _get_rec_info(self, cr, uid, ids, fields, args, context=None):
        result = {}
        for id in ids:
            result[id] = {'product_uom_base_qty':0,}
        for m in self.browse(cr,uid,ids,context=context):
            #calculate the product base uom quantity
            product_uom_base_qty = m.product_qty
            if m.product_uom.id != m.product_id.uom_id.id:
                product_uom_base_qty = self.pool.get('product.uom')._compute_qty_obj(cr, uid, m.product_uom, m.product_qty, m.product_id.uom_id)
            
            result[m.id].update({'product_uom_base_qty':product_uom_base_qty})
        return result    
    _columns = {
        'product_uom_base': fields.related('product_id','uom_id',type='many2one',relation='product.uom', string='Base UOM',readonly=True),
        'product_uom_base_qty': fields.function(_get_rec_info, type='float', string='Base Quantity', multi="baseqty_info", digits_compute=dp.get_precision('Product Unit of Measure'),readonly=True),
    }