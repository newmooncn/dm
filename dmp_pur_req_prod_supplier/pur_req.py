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
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from openerp import netsvc

from openerp.osv import fields,osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare
from openerp.addons.dm_base import utils
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP

class pur_req_po_line(osv.osv_memory):
    _inherit = "pur.req.po.line"

    _columns = {
        'supplier_prod_id': fields.integer(string='Supplier Product ID', required=False),
        'supplier_prod_name': fields.char(string='Supplier Product Name', required=True),
        'supplier_prod_code': fields.char(string='Supplier Product Code', required=False),
        'supplier_delay' : fields.integer(string='Supplier Lead Time', required=False),
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
            user = self.pool.get("res.users").browse(cr,uid,uid,context=context)
            if ids:
                #from order line update
                for line in self.browse(cr,uid,ids,context=context):
                    new_vals.update({'name':line.wizard_id.partner_id.id,'product_id':line.product_id.product_tmpl_id.id,'currency':user.company_id.currency_id.id})
                    if line.supplier_prod_id:
                        #update the prodcut supplier info
                        prod_supp_obj.write(cr,uid,line.supplier_prod_id,new_vals,context=context)
                    else:
                        supplier_prod_id = prod_supp_obj.create(cr,uid,new_vals,context=context)     
            else:
                # from order line create
                po = self.pool.get('pur.req.po').browse(cr,uid,vals['wizard_id'])
                product = self.pool.get('product.product').browse(cr, uid, vals['product_id'], context=context)
                new_vals.update({'name':po.partner_id.id,'product_id':product.product_tmpl_id.id,'currency':user.company_id.currency_id.id})
                prod_supp_ids = prod_supp_obj.search(cr,uid,[('product_id','=',new_vals['product_id']),('name','=',new_vals['name'])])
                if prod_supp_ids and len(prod_supp_ids) > 0:
                    #update the prodcut supplier info
                    prod_supp_obj.write(cr,uid,prod_supp_ids[0],new_vals,context=context)
                else:
                    supplier_prod_id = prod_supp_obj.create(cr,uid,new_vals,context=context)  
                    
    def create(self, cr, user, vals, context=None):
        #check the product supplier info
        if not vals.has_key('supplier_prod_name') or vals['supplier_prod_name'] == '':
            product_name = self.pool.get("product.product").read(cr,user,[vals['product_id']],['name'],context=context)[0]['name']
            raise osv.except_osv(_('Error!'),
                                 _('The product supplier name is required to product .\n %s'%product_name))     

        resu = super(pur_req_po_line,self).create(cr, user, vals, context=context)
        #update product supplier info
        self._update_prod_supplier(cr, user, [], vals, context)
        return resu 
                        
    def write(self, cr, uid, ids, vals, context=None):
        if not ids:
            return True
        resu = super(pur_req_po_line,self).write(cr, uid, ids, vals, context=context)
        #update product supplier info
        self._update_prod_supplier(cr, uid, ids, vals, context)
        return resu  
                            
pur_req_po_line()
                    
class pur_req_po(osv.osv_memory):
    _inherit = 'pur.req.po'
    
    def onchange_partner(self,cr,uid,ids,partner_id,lines,context):
        resu = super(pur_req_po, self).onchange_partner(cr, uid, ids, partner_id, lines, context)
        if not resu:
            resu = {'value':{}}
        value = resu.get('value',{})
        prod_supp_obj = self.pool.get('product.supplierinfo')
        line_rets = []         
        for line in lines:
            if not line[2]:
                continue
            line_dict = line[2]
            # update the product supplier info
            prod_supp_ids = prod_supp_obj.search(cr,uid,[('product_id','=',line_dict['product_id']),('name','=',partner_id)])
            if prod_supp_ids and len(prod_supp_ids) > 0:
                prod_supp = prod_supp_obj.browse(cr,uid,prod_supp_ids[0],context=context)
                line_dict.update({'supplier_prod_id': prod_supp.id,
                                    'supplier_prod_name': prod_supp.product_name,
                                    'supplier_prod_code': prod_supp.product_code,
                                    'supplier_delay' : prod_supp.delay})
            else:
                line_dict.update({'supplier_prod_id': False,
                                    'supplier_prod_name': '',
                                    'supplier_prod_code': '',
                                    'supplier_delay' : 1})      
            line_rets.append(line_dict)
        value['line_ids'] = line_rets
        resu['value'] = value
        return resu
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
