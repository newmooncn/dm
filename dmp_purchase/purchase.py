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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from openerp.osv import fields,osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.addons.purchase import purchase
class purchase_order(osv.osv):  
    _inherit = "purchase.order"   
            
    _columns = {
        'warehouse_id': fields.many2one('stock.warehouse', 'Destination Warehouse',states={'confirmed':[('readonly',True)],'approved':[('readonly',True)],'done':[('readonly',True)]}),            
        'create_uid':  fields.many2one('res.users', 'Creator', readonly=True),
        'create_date': fields.datetime('Creation Date', readonly=True, select=True),
        'is_sent_supplier': fields.boolean('Sent to Supplier', select=True),
        'taxes_id': fields.many2many('account.tax', 'po_tax', 'po_id', 'tax_id', 'Taxes', states={'confirmed':[('readonly',True)],'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'has_freight': fields.boolean('Has Freight', states={'confirmed':[('readonly',True)],'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'amount_freight': fields.float('Freight', states={'confirmed':[('readonly',True)],'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'receipt_number': fields.char('Receipt Number', size=64, help="The reference of this invoice as provided by the partner."),
        'comments': fields.text('Comments'),       
        #partner bank info
        'bank_name': fields.related('partner_id', 'bank_name', type='char', string='Bank Name'),
        'bank_account': fields.related('partner_id', 'bank_account', type='char', string='Bank Account Name'),
    }
    _defaults = {
        'is_sent_supplier': False,
    }    
    def _check_duplicated_products(self, cr, uid, ids, context=None):
        for po in self.browse(cr, uid, ids, context=context):
            if po.state in('done','approved', 'wait_receipt'):
                continue
            products = {}
            for line in po.order_line:
                product = line.product_id
                product_id = product.id
                if product_id not in products:
                    products[product_id] = 1
                else:
#                    products[product_id] = products[product_id] + 1
                    raise osv.except_osv(_('Error!'), _('[%s]%s is duplicated in this order!')%(product.default_code,product.name))
        return True 
    _constraints = [
        (_check_duplicated_products, 'Error ! You can not add duplicated products!', ['order_line'])
    ]    
    
    def _get_lines(self,cr,uid,ids,states=None,context=None):
        todo = []
        for po in self.browse(cr, uid, ids, context=context):
            if not po.order_line:
                continue
            for line in po.order_line:
                if states == None or line.state in states:
                    todo.append(line.id)
        return todo
        
    def button_update_uom(self, cr, uid, ids, context=None):
        po_lines = {}
        if context and context.get("uom_todo"):
            po_lines = context.get("uom_todo")
        else:
            for po in self.browse(cr, uid, ids, context=context):
                for line in po.order_line:
                    if line.product_id.id not in po_lines and line.product_uom.id != line.product_id.uom_po_id.id:
                        po_lines.update({line.id:line.product_id.uom_po_id.id})
        for po_line in po_lines:
            cr.execute('update purchase_order_line set product_uom=%s where id=%s',(po_lines[po_line],po_line))
            
        return True
    
    def wkf_confirm_order(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        resu = super(purchase_order, self).wkf_confirm_order(cr, uid, ids, context=context)
        self.button_update_uom(cr, uid, ids, context)
        return resu     
            
    def write(self, cr, user, ids, vals, context=None):
        #if user changed the expected plan date, then update the associated pickings
        if vals.get('minimum_planned_date') and vals.get('minimum_planned_date') != '':
            order = self.browse(cr,user,ids[0],context=context)
            if order.picking_ids:
                pick_ids = []
                for pick in order.picking_ids:
                    if pick.state != 'cancel' and pick.state !='done':
                        pick_ids.append(pick.id)
                self.pool.get('stock.picking.in').write(cr,user,pick_ids,{'min_date':vals.get('minimum_planned_date')})
        return super(purchase_order,self).write(cr,user,ids,vals,context=context)
    
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'receipt_number':None,
        })
        return super(purchase_order, self).copy(cr, uid, id, default, context)
    
    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        #deal the 'date' datetime field query
        new_args = deal_args(self,args)    
        return super(purchase_order,self).search(cr, user, new_args, offset, limit, order, context, count)
          
class purchase_order_line(osv.osv):  
    _name = "purchase.order.line"
    _inherit = 'purchase.order.line' 

    def _get_line_info(self, cr, uid, ids, fields, args, context=None):
        result = {}
        for id in ids:
            result[id] = {'can_change_price':True,'can_change_product':True,'product_uom_base_qty':0}
        uom_obj = self.pool.get("product.uom")
        for line in self.browse(cr,uid,ids,context=context):
            can_change_price = True
            can_change_product = True
            if line.move_ids:
                #once there are moving, then can not change product, 06/07/2014 by johnw
                can_change_product = False
            if line.invoice_lines:
                #once there are invoice lines, then can not change product, 06/07/2014 by johnw
                can_change_product = False
                for inv_line in line.invoice_lines:
                    #if there are done invoices, then can not change price
                    if can_change_price and (inv_line.invoice_id.state == 'paid' or len(inv_line.invoice_id.payment_ids) > 0):
                        can_change_price = False
            product_uom_base_qty = line.product_qty
            if line.product_uom.id != line.product_id.uom_id.id:
                product_uom_base_qty = uom_obj._compute_qty_obj(cr, uid, line.product_uom, line.product_qty, line.product_id.uom_id)
            result[line.id].update({'can_change_price':can_change_price,
                                    'can_change_product':can_change_product,
                                    'product_uom_base_qty':product_uom_base_qty,})
        return result
    def _amount_line(self, cr, uid, ids, prop, arg, context=None):
        res = {}    
        for id in ids:
            res[id] = {'price_subtotal':0,'price_subtotal_withtax':0}         
        cur_obj=self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        for line in self.browse(cr, uid, ids, context=context):
            taxes = tax_obj.compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id]['price_subtotal'] = cur_obj.round(cr, uid, cur, taxes['total'])
            res[line.id]['price_subtotal_withtax'] = cur_obj.round(cr, uid, cur, line.price_unit*line.product_qty)
        return res
 
    _columns = {
        'po_notes': fields.related('order_id','notes',string='Terms and Conditions',readonly=True,type="text"),
        'payment_term_id': fields.related('order_id','payment_term_id',string='Payment Term',readonly=True,type="many2one", relation="account.payment.term"),
        'create_uid':  fields.many2one('res.users', 'Creator', select=True, readonly=True),
        'create_date': fields.datetime('Creation Date', readonly=True, select=True),
        'image_medium': fields.related('product_id','image_medium',type='binary',String="Medium-sized image"),
        'has_freight': fields.related('order_id','has_freight',string='Has Freight', type="boolean", readonly=True),
        'amount_freight': fields.related('order_id','amount_freight',string='Freight', type='float', readonly=True),
        'can_change_price' : fields.function(_get_line_info, type='boolean', string='Can Change Price', multi="line_info"),
        'can_change_product' : fields.function(_get_line_info, type='boolean', string='Can Change Product', multi="line_info"),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account'),multi='amount_line',),
        'price_subtotal_withtax': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account'),multi='amount_line',),
        'product_uom_base': fields.related('product_id','uom_id',type='many2one',relation='product.uom', string='Base UOM',readonly=True),
        'product_uom_base_qty': fields.function(_get_line_info, type='float', digits_compute=dp.get_precision('Product Unit of Measure'), string='Base Quantity', multi="line_info"),
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of sales order lines."),
    }  
    _order = "order_id desc, sequence, id"
    _defaults = {
        'can_change_price': True,
        'can_change_product': True,
    }        
          
    def write(self, cr, uid, ids, vals, context=None):
        if not ids:
            return True
        #add the procut_uom set by product's purchase uom
        if 'product_id' in vals and 'product_uom' not in vals:
            prod = self.pool.get('product.product').browse(cr, uid, vals['product_id'], context=context)
            product_uom = None
            if prod.uom_po_id:
                product_uom = prod.uom_po_id.id
            else:
                product_uom = prod.uom_id.id
            vals.update({'product_uom':product_uom})  
            
        id = ids[0]
        po_line = self.browse(cr,uid,id,context=context)
        resu = super(purchase_order_line,self).write(cr, uid, ids, vals, context=context)
        #if price_unit changed then update it to product_product.standard_price
        if vals.has_key('price_unit'):
            #standard_price = self.pool.get('product.uom')._compute_price(cr, uid, po_line.product_uom.id, vals["price_unit"],po_line.product_id.uom_id.id)
            #self.pool.get('product.product').write(cr,uid,[po_line.product_id.id],{'standard_price':standard_price,'uom_po_price':vals["price_unit"]},context=context)
            self.pool.get('product.product').write(cr,uid,[po_line.product_id.id],{'uom_po_price':vals["price_unit"]},context=context)
            
        return resu
    
    def create(self, cr, user, vals, context=None):
        #add the procut_uom set by product's purchase uom
        if 'product_uom' not in vals:
            prod = self.pool.get('product.product').browse(cr, user, vals['product_id'], context=context)
            product_uom = None
            if prod.uom_po_id:
                product_uom = prod.uom_po_id.id
            else:
                product_uom = prod.uom_id.id
            vals.update({'product_uom':product_uom})            
        resu = super(purchase_order_line,self).create(cr, user, vals, context=context)
        #if price_unit changed then update it to product_product.standard_price
        if vals.has_key('price_unit'):
            prod = self.pool.get('product.product').browse(cr, user, vals['product_id'], context=context)
            #standard_price = self.pool.get('product.uom')._compute_price(cr, user, vals["product_uom"], vals["price_unit"],prod.uom_id.id)            
            #self.pool.get('product.product').write(cr,user,[vals['product_id']],{'standard_price':standard_price,'uom_po_price':vals["price_unit"]},context=context)
            self.pool.get('product.product').write(cr,user,[vals['product_id']],{'uom_po_price':vals["price_unit"]},context=context)
                              
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
        if product_id and context is not None and not res['value'].get('taxes_id') and context.get('po_taxes_id')[0][2]: 
            # - determine taxes_id when purchase_header has taxes_id and produt has not own taxes setting
            account_fiscal_position = self.pool.get('account.fiscal.position')
            account_tax = self.pool.get('account.tax')
            taxes = account_tax.browse(cr, uid, context['po_taxes_id'][0][2])
            fpos = fiscal_position_id and account_fiscal_position.browse(cr, uid, fiscal_position_id, context=context) or False
            taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes)
            res['value'].update({'taxes_id': taxes_ids})
                    
        return res
    
    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        #deal the 'date' datetime field query
        new_args = deal_args(self,args)
        return super(purchase_order_line,self).search(cr, user, new_args, offset, limit, order, context, count)
    
    def open_product(self, cr, uid, ids, context=None):
        res_id = None
        if isinstance(ids, list):
            res_id = ids[0]
        else:
            res_id = ids
        prod_id = self.browse(cr, uid, res_id, context=context).product_id
        if not prod_id:
            return False
        prod_id = prod_id.id
        #got to accountve move form

        form_view = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'product_normal_form_view')
        form_view_id = form_view and form_view[1] or False
        return {
            'name': _('Product'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [form_view_id],
            'res_model': 'product.product',
            'type': 'ir.actions.act_window',
            'res_id': prod_id,
        }
            
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
def deal_args(obj,args):  
    new_args = []
    for arg in args:
        fld_name = arg[0]
        if fld_name == 'create_date' or fld_name == 'write_date':
            fld_operator = arg[1]
            fld_val = arg[2]
            fld = obj._columns.get(fld_name)
            #['date','=','2013-12-12 16:00:00'] the '16' was generated for the timezone
            if fld._type == 'datetime' and fld_operator == "=" and fld_val.endswith('00:00'):
                time_start = [fld_name,'>=',fld_val]
                time_obj = datetime.datetime.strptime(fld_val,DEFAULT_SERVER_DATETIME_FORMAT)
                time_obj += relativedelta(days=1)
                time_end = [fld_name,'<=',time_obj.strftime(DEFAULT_SERVER_DATETIME_FORMAT)]
                new_args.append(time_start)
                new_args.append(time_end)
            else:
                new_args.append(arg)
        else:
            new_args.append(arg)    
    return new_args

from openerp.addons.purchase.purchase import purchase_order_line as oe_po_line
def dmp_po_line_onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
        partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
        name=False, price_unit=False, context=None):
    """
    onchange handler of product_id.
    """
    if context is None:
        context = {}

    res = {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'product_uom' : uom_id or False}}
    if not product_id:
        return res

    product_product = self.pool.get('product.product')
    product_uom = self.pool.get('product.uom')
    res_partner = self.pool.get('res.partner')
    product_pricelist = self.pool.get('product.pricelist')
    account_fiscal_position = self.pool.get('account.fiscal.position')
    account_tax = self.pool.get('account.tax')

    # - check for the presence of partner_id and pricelist_id
    #if not partner_id:
    #    raise osv.except_osv(_('No Partner!'), _('Select a partner in purchase order to choose a product.'))
    #if not pricelist_id:
    #    raise osv.except_osv(_('No Pricelist !'), _('Select a price list in the purchase order form before choosing a product.'))

    # - determine name and notes based on product in partner lang.
    context_partner = context.copy()
    if partner_id:
        lang = res_partner.browse(cr, uid, partner_id).lang
        context_partner.update( {'lang': lang, 'partner_id': partner_id} )
    product = product_product.browse(cr, uid, product_id, context=context_partner)
    name = product.name
    if product.description_purchase:
        name += '\n' + product.description_purchase
    res['value'].update({'name': name})

    # - set a domain on product_uom
    res['domain'] = {'product_uom': [('category_id','=',product.uom_id.category_id.id)]}

    # - check that uom and product uom belong to the same category
    product_uom_po_id = product.uom_po_id.id
    if not uom_id:
        uom_id = product_uom_po_id

    if product.uom_id.category_id.id != product_uom.browse(cr, uid, uom_id, context=context).category_id.id:
        if self._check_product_uom_group(cr, uid, context=context):
            res['warning'] = {'title': _('Warning!'), 'message': _('Selected Unit of Measure does not belong to the same category as the product Unit of Measure.')}
        uom_id = product_uom_po_id

    res['value'].update({'product_uom': uom_id})

    # - determine product_qty and date_planned based on seller info
    if not date_order:
        date_order = fields.date.context_today(self,cr,uid,context=context)


    supplierinfo = False
    for supplier in product.seller_ids:
        if partner_id and (supplier.name.id == partner_id):
            supplierinfo = supplier
            if supplierinfo.product_uom.id != uom_id:
                res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier only sells this product by %s') % supplierinfo.product_uom.name }
            min_qty = product_uom._compute_qty(cr, uid, supplierinfo.product_uom.id, supplierinfo.min_qty, to_uom_id=uom_id)
            if (qty or 0.0) < min_qty: # If the supplier quantity is greater than entered from user, set minimal.
                if qty:
                    res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier has a minimal quantity set to %s %s, you should not purchase less.') % (supplierinfo.min_qty, supplierinfo.product_uom.name)}
                qty = min_qty
    dt = self._get_date_planned(cr, uid, supplierinfo, date_order, context=context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    qty = qty or 1.0
    res['value'].update({'date_planned': date_planned or dt})
    if qty:
        res['value'].update({'product_qty': qty})

    # - determine price_unit and taxes_id
    #only change the price when the price_unir parameter has not value, by john wang, 2014/02/25
    if not price_unit or price_unit == 0:
        if pricelist_id:
            price = product_pricelist.price_get(cr, uid, [pricelist_id],
                    product.id, qty or 1.0, partner_id or False, {'uom': uom_id, 'date': date_order})[pricelist_id]
        else:
            price = product.uom_po_price
    else:
        price = price_unit
        
    taxes = account_tax.browse(cr, uid, map(lambda x: x.id, product.supplier_taxes_id))
    fpos = fiscal_position_id and account_fiscal_position.browse(cr, uid, fiscal_position_id, context=context) or False
    taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes)
    res['value'].update({'price_unit': price, 'taxes_id': taxes_ids})

    return res
oe_po_line.onchange_product_id = dmp_po_line_onchange_product_id    