# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from openerp.osv import fields, osv
from openerp.tools.translate import _

import base64
import xlrd
import re
import types
import os

class product_product(osv.osv):
    _inherit = 'product.product'  
    def _parent_products(self, cr, uid, ids, field_names, args, context=None):
        bom_obj = self.pool.get('mrp.bom')
        res = {} 
        for id in ids:
            res[id] = []
        bom_ids = bom_obj.search(cr, uid, [('product_id', 'in', ids)])
#        for product_id in ids:
#            bom_ids = bom_obj.search(cr, uid, [('product_id', '=', product_id)])
        for bom in bom_obj.browse(cr, uid, bom_ids, context=context):
            if bom.bom_id:
                res[bom.product_id.id].append(bom.bom_id.product_id.id)
                
        return res
            
    _columns={
              'parent_product_ids': fields.function(_parent_products, type='one2many', relation="product.product", string='Parent Products'),
              }
    def create(self, cr, uid, vals, context=None):
        #if importing need to find direct bom and no bom lines, then system will search the existing bom, and set the direct_bom_id
        if vals.get('direct_bom_find',False) and not vals.get('bom_lines'):
            direct_bom_id = self._bom_find(cr, uid, vals['product_id'], None, properties=None)
            if direct_bom_id:
                vals.update({'direct_bom_id':direct_bom_id})
        return super(mrp_bom,self).create(cr, uid, vals, context)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
