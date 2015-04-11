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

class purchase_order_line(osv.osv):  
    _name = "purchase.order.line"
    _inherit = 'purchase.order.line' 
        
    def _get_supp_prod(self, cr, uid, ids, fields, arg, context=None):
        result = {}
        for line in self.browse(cr,uid,ids,context=context):
            result[line.id] = {
                'supplier_prod_id': False,  
                'supplier_prod_name': '',
                'supplier_prod_code': '',
                'supplier_delay': 1,
            }
            if not line.product_id or not line.product_id.seller_ids:
                continue
            for seller_info in line.product_id.seller_ids:
                if seller_info.name == line.partner_id:
                    #found the product supplier info
                    result[line.id].update({
                        'supplier_prod_id': seller_info.id,                    
                        'supplier_prod_name': seller_info.product_name,
                        'supplier_prod_code': seller_info.product_code,
                        'supplier_delay': seller_info.delay,
                        
                    })
                    break
        return result
    
    _columns = {
        'supplier_prod_id': fields.function(_get_supp_prod, type='integer', string='Supplier Product ID', multi="seller_info"),
        'supplier_prod_name': fields.function(_get_supp_prod, type='char', string='Supplier Product Name', required=True, multi="seller_info"),
        'supplier_prod_code': fields.function(_get_supp_prod, type='char', string='Supplier Product Code', multi="seller_info"),
        'supplier_delay' : fields.function(_get_supp_prod, type='integer', string='Supplier Lead Time', multi="seller_info"), 
    }  

    #write the product supplier information
    def _update_prod_supplier(self,cr,uid,ids,vals,context=None):
        if vals.has_key('supplier_prod_name') or vals.has_key('supplier_prod_code') or vals.has_key('supplier_delay'):
            prod_supp_obj = self.pool.get('product.supplierinfo')
            new_vals = {'min_qty':0}
            if vals.has_key('supplier_prod_name'):
                new_vals.update({'product_name':vals['supplier_prod_name']})
            if vals.has_key('supplier_prod_code'):
                new_vals.update({'product_code':vals['supplier_prod_code']})
            if vals.has_key('supplier_delay'):
                new_vals.update({'delay':vals['supplier_delay']})
            #for the dmp_currency module, set the currency
            if ids:
                #from order line update
                for line in self.browse(cr,uid,ids,context=context):
                    new_vals.update({'name':line.partner_id.id,'product_id':line.product_id.product_tmpl_id.id,'currency':line.order_id.pricelist_id.currency_id.id})
                    if line.supplier_prod_id:
                        #update the prodcut supplier info
                        prod_supp_obj.write(cr,uid,line.supplier_prod_id,new_vals,context=context)
                    else:
                        supplier_prod_id = prod_supp_obj.create(cr,uid,new_vals,context=context)     
            else:
                # from order line create
                po = self.pool.get('purchase.order').browse(cr,uid,vals['order_id'])
                product = self.pool.get('product.product').browse(cr, uid, vals['product_id'], context=context)
                new_vals.update({'name':po.partner_id.id,'product_id':product.product_tmpl_id.id,'currency':po.pricelist_id.currency_id.id})
                prod_supp_ids = prod_supp_obj.search(cr,uid,[('product_id','=',new_vals['product_id']),('name','=',new_vals['name'])])
                if prod_supp_ids and len(prod_supp_ids) > 0:
                    #update the prodcut supplier info
                    prod_supp_obj.write(cr,uid,prod_supp_ids[0],new_vals,context=context)
                else:
                    supplier_prod_id = prod_supp_obj.create(cr,uid,new_vals,context=context)  
                  
          
    def write(self, cr, uid, ids, vals, context=None):
        if not ids:
            return True
        resu = super(purchase_order_line,self).write(cr, uid, ids, vals, context=context)
        #update product supplier info
        self._update_prod_supplier(cr, uid, ids, vals, context)            
        return resu
    
    def create(self, cr, user, vals, context=None):     
        resu = super(purchase_order_line,self).create(cr, user, vals, context=context)
        #update product supplier info
        self._update_prod_supplier(cr, user, [], vals, context)
        return resu  
    
    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None):
        if not context:
            context = {}
        """
        onchange handler of product_id.
        """
        res = super(purchase_order_line,self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id,
                                partner_id, date_order, fiscal_position_id, date_planned,name, price_unit, context)
        
        # update the product supplier info
        if product_id and not context.get('supplier_prod_id'):
            prod_supp_obj = self.pool.get('product.supplierinfo')
            product = self.pool.get("product.product").browse(cr, uid, product_id, context=context)
            prod_supp_ids = prod_supp_obj.search(cr,uid,[('product_id','=',product.product_tmpl_id.id),('name','=',partner_id)])
            if prod_supp_ids and len(prod_supp_ids) > 0:
                prod_supp = prod_supp_obj.browse(cr,uid,prod_supp_ids[0],context=context)
                res['value'].update({'supplier_prod_id': prod_supp.id,
                                    'supplier_prod_name': context.get('supplier_prod_name') or prod_supp.product_name,
                                    'supplier_prod_code': context.get('supplier_prod_code') or prod_supp.product_code,
                                    'supplier_delay' :context.get('supplier_delay') or  prod_supp.delay})
            else:
                res['value'].update({'supplier_prod_id': False,
                                    'supplier_prod_name': context.get('supplier_prod_name') or '',
                                    'supplier_prod_code': context.get('supplier_prod_code') or '',
                                    'supplier_delay' : context.get('supplier_delay') or 1})
            
        return res    