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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from openerp.osv import fields,osv
from openerp.tools.translate import _
from openerp.addons.dm_base import utils

class purchase_order(osv.osv):  
    _inherit = 'purchase.order' 
    def create(self, cr, uid, vals, context=None):
        if vals.get('order_line') and vals.get('partner_id'):
            #[(0,0,{dict values}),(0,0,{dict values}),(0,0,{dict values})]
            for line in vals.get('order_line'):
                line = line[2]
                if line.get('product_id'):
                    supplier_prod_name = self.pool.get('product.product').get_supplier_product(cr, uid, vals.get('partner_id'), line.get('product_id'), context=context)
                    line['supplier_prod_name'] = supplier_prod_name
        return super(purchase_order, self).create(cr, uid, vals, context=context)
    
class purchase_order_line(osv.osv):  
    _name = "purchase.order.line"
    _inherit = 'purchase.order.line' 
    
    _columns = {
        'supplier_prod_name': fields.char('Supplier Product Name', 64),
    }
    def create(self, cr, uid, vals, context=None):
        if not vals.get('supplier_prod_name') and vals.get('order_id') and vals.get('product_id'):
            partner_id = self.pool.get('purchase.order').browse(cr, uid, vals.get('order_id'), context=context).partner_id.id
            supplier_prod_name = self.pool.get('product.product').get_supplier_product(cr, uid, partner_id, vals.get('product_id'), context=context)
            vals['supplier_prod_name'] = supplier_prod_name
        return super(purchase_order_line, self).create(cr, uid, vals, context=context)
            
    '''
    update purchase_order_line a
    set supplier_prod_name = c.product_name
    from purchase_order b,
    product_supplierinfo c
    where a.order_id = b.id
    and a.product_id = c.product_id
    and b.partner_id = c.name    
    '''        
    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
        partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
        name=False, price_unit=False, state='draft', context=None):
        if not context:
            context = {}
        """
        onchange handler of product_id.
        """
        res = super(purchase_order_line,self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id,
                                partner_id, date_order, fiscal_position_id, date_planned,name, price_unit, state, context)
        #when this is product id changing not uom changing, check product's supplier setting
        if not uom_id and product_id and partner_id:
            prod = self.pool['product.product'].browse(cr, uid, product_id, context=context)
            supplier_ids = [seller.name.id for seller in prod.seller_ids]
            if partner_id not in supplier_ids:
                partner_name = self.pool['res.partner'].read(cr, uid, partner_id, ['name'], context=context)['name']
                message = _('[%s] is not defined in supplier list of [%s]')%(partner_name, prod['name'])
                #set the return warning messages
                utils.set_resu_warn(res, message, title = _('Warn'))
                            
        #add supplier product name
        if product_id and partner_id:            
            supplier_prod_name, supplier_prod_price = self.pool.get('product.product').get_supplier_product_data(cr, uid, partner_id, product_id, context=context)
            res['value']['supplier_prod_name'] = supplier_prod_name
            if supplier_prod_price:
                res['value']['price_unit'] = supplier_prod_price
            
        return res     