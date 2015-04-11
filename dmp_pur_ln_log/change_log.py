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

class change_log_po_line(osv.osv):  
    _name = "change.log.po.line"
    _columns = {
        'po_line_id': fields.many2one('purchase.order.line','PO Line'),
        'po_id': fields.many2one('purchase.order','PO'),
        'product_id': fields.many2one('product.product','Product'),
        'field_name':  fields.char('Field Name', size=30, readonly=True),
        'value_old': fields.char('Old Value', readonly=True),
        'value_new': fields.char('New Value', readonly=True),
        'create_uid': fields.many2one('res.users', 'User', readonly=True),
        'create_date':  fields.datetime('Time', readonly=True),
    }
    _order = 'create_date desc'
change_log_po_line()    

class purchase_order(osv.osv):  
    _inherit = "purchase.order"

#    def _change_log_line(self, cr, uid, ids, field_names=None, arg=False, context=None):
#        """ Finds the line change log
#        @return: Dictionary of values
#        """
#        if not field_names:
#            field_names = []
#        if context is None:
#            context = {}
#        res = {}
#        for id in ids:
#            res[id] = {}.fromkeys(field_names)
#
#        for purchase in self.browse(cr, uid, ids, context=context):
#            #check the invoice paid  
#            change_log_ids = []          
#            for line in purchase.order_line:
#                change_log_ids.extend([change_log.id for change_log in line.change_log])
#            res[purchase.id] = change_log_ids
#        return res
    
    _columns = {
#        'change_log_line': fields.function(_change_log_line, type='one2many', relation='change.log.po.line', string='Line Changing'),
        'change_log_line': fields.one2many('change.log.po.line','po_id','Line Changing Log', readonly=True),  
    }    

class purchase_order_line(osv.osv):  
    _name = "purchase.order.line"
    _inherit = 'purchase.order.line' 
    _columns = {
        'change_log': fields.one2many('change.log.po.line','po_line_id','Changing Log'),      
    }    
    def write(self, cr, uid, ids, vals, context=None):
        if not ids:
            return True
        resu = super(purchase_order_line,self).write(cr, uid, ids, vals, context=context)
        #only when orders confirmed, then record the quantity&price changing log
        po_line = self.browse(cr,uid,ids[0],context=context)
        if po_line.order_id.state != 'draft':
            log_obj = self.pool.get('change.log.po.line')
            field_names = ['product_qty','price_unit','product_id'];
            for field_name in field_names:
                if vals.has_key(field_name):
                    value_old = getattr(po_line,field_name)
                    value_new = vals[field_name]
                    if field_name == 'product_id':
                        prod_obj = self.pool.get('product.product')
                        value_old = prod_obj.name_get(cr, uid, [value_old.id], context=context)[0][1]
                        value_new = prod_obj.name_get(cr, uid, [vals[field_name]], context=context)[0][1]
                    log_vals = {'po_id':po_line.order_id.id,'po_line_id':po_line.id,'product_id':po_line.product_id.id,
                                'field_name':field_name,'value_old':value_old,'value_new':value_new}
                    log_obj.create(cr,uid,log_vals,context=context)
        return resu
    
    def create(self, cr, user, vals, context=None):          
        resu = super(purchase_order_line,self).create(cr, user, vals, context=context)
        #only when orders confirmed, then record the po lines adding
        uid = user
        po_line = self.browse(cr, uid, resu, context=context)
        if po_line.order_id.state != 'draft':
            log_obj = self.pool.get('change.log.po.line')
            log_vals = {'po_id':po_line.order_id.id,'po_line_id':po_line.id,'product_id':po_line.product_id.id,
                                'field_name':'Add Product','value_old':'','value_new':'price:%s, quantity:%s'%(po_line.product_qty, po_line.price_unit)}
            log_obj.create(cr,uid,log_vals,context=context)                    
        return resu  
    
    def unlink(self, cr, uid, ids, context=None):
        resu = super(purchase_order_line,self).unlink(cr,uid,ids,context=context)
        lines = self.browse(cr,uid,ids,context=context)
        for line in lines:
            #only when orders confirmed, then record the po lines deleting
            if line.order_id.state != 'draft':
                log_obj = self.pool.get('change.log.po.line')
                log_vals = {'po_id':line.order_id.id,'po_line_id':line.id,'product_id':line.product_id.id,
                                'field_name':'Delete Product','value_old':'price:%s, quantity:%s'%(line.product_qty, line.price_unit),'value_new':''}
                log_obj.create(cr,uid,log_vals,context=context)
        return resu
    
    def copy_data(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({'change_log':None})
        return super(purchase_order_line, self).copy_data(cr, uid, id, default, context)    