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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
from openerp.osv import fields,osv
from openerp.tools.translate import _
from openerp.addons.dm_base import utils

from openerp.addons.sale_stock.sale_stock import sale_order_line as so_line_stock    
#Improve the waring message setting logic, johnw, 07/17/2015    
def product_id_change_imrpove(self, cr, uid, ids, pricelist, product, qty=0,
        uom=False, qty_uos=0, uos=False, name='', partner_id=False,
        lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
    context = context or {}
    product_uom_obj = self.pool.get('product.uom')
    partner_obj = self.pool.get('res.partner')
    product_obj = self.pool.get('product.product')
    warning = {}
    res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty=qty,
        uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
        lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)

    if not product:
        res['value'].update({'product_packaging': False})
        return res

    #update of result obtained in super function
    product_obj = product_obj.browse(cr, uid, product, context=context)
    res['value']['delay'] = (product_obj.sale_delay or 0.0)
    res['value']['type'] = product_obj.procure_method

    #check if product is available, and if not: raise an error
    uom2 = False
    if uom:
        uom2 = product_uom_obj.browse(cr, uid, uom, context=context)
        if product_obj.uom_id.category_id.id != uom2.category_id.id:
            uom = False
    if not uom2:
        uom2 = product_obj.uom_id

    # Calling product_packaging_change function after updating UoM
    res_packing = self.product_packaging_change(cr, uid, ids, pricelist, product, qty, uom, partner_id, packaging, context=context)
    res['value'].update(res_packing.get('value', {}))
    warning_msgs = res_packing.get('warning') and res_packing['warning']['message'] or ''
    compare_qty = float_compare(product_obj.virtual_available, qty, precision_rounding=uom2.rounding)
    if (product_obj.type=='product') and int(compare_qty) == -1 \
       and (product_obj.procure_method=='make_to_stock'):
        warn_msg = _('You plan to sell %.2f %s but you only have %.2f %s available !\nThe real stock is %.2f %s. (without reservations)') % \
                (qty, uom2.name,
                 max(0,product_obj.virtual_available), uom2.name,
                 max(0,product_obj.qty_available), uom2.name)
        warning_msgs += _("Not enough stock ! : ") + warn_msg + "\n\n"

    #update of warning messages
    #johnw, 07/17/2015, se warning message
#    if warning_msgs:
#        warning = {
#                   'title': _('Configuration Error!'),
#                   'message' : warning_msgs
#                }
#    res.update({'warning': warning})    
    utils.set_resu_warn(res, warning_msgs, title = _('Configuration Error!'))
    return res    

#so_line_stock.product_id_change = product_id_change_imrpove

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
                message = _('[%s] is not defined in customer list of [%s]')%(partner_name, prod['name'])
                #set the return warning messages
                utils.set_resu_warn(res, message, title = _('Warn'))
                    
        #add customer product name
        if product and partner_id:
            res['value']['customer_prod_name'] = self.pool.get('product.product').get_customer_product(cr, uid, partner_id, product, context=context)
        
        return res