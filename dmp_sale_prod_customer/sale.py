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

class sale_order_line(osv.osv):  
    _inherit = 'sale.order.line' 
    
    _columns = {
        'customer_prod_name': fields.char('Customer Product Name', 64),
    }
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False,
            fiscal_position=False, flag=False, context=None):

        res=super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty,
            uom, qty_uos, uos, name, partner_id,
            lang, update_tax, date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)

        #check product's customer setting
        if product and partner_id:
            prod = self.pool['product.product'].browse(cr, uid, product, context=context)
            customer_ids = [customer.name.id for customer in prod.customer_ids]
            if partner_id not in customer_ids:
                partner_name = self.pool['res.partner'].read(cr, uid, partner_id, ['name'], context=context)['name']
                raise osv.except_osv(_('Warn!'),_('[%s] is not defined in customer list of [%s]')%(partner_name, prod['name']))
                    
        #add customer product name
        if product and partner_id:
            res['value']['customer_prod_name'] = self.pool.get('product.product').get_customer_product(cr, uid, partner_id, product, context=context)
        
        return res