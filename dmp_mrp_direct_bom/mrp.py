# -*- encoding: utf-8 -*-
from openerp.osv import fields,osv
from openerp.tools.translate import _
from openerp import netsvc
import time
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from lxml import etree
from openerp.addons.mrp.mrp import rounding as mrp_rounding
from openerp import tools
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp

class mrp_bom(osv.osv):
    _inherit = 'mrp.bom'
    _columns = {
                #08/21/2014, the direct bom id, will be used in manufacture order, the the action_compute()-->_bom_explode() 
                #1.user set the bom_lines of this bom, then will use bom_lines to explode the products and work centers
                #2.if no bom_lines, then check this field 'direct_bom_id', if there is a bom setted, then use this bom to do _bom_explode
                #3.if no above 2 fields, and the 'addthis' parameter is true, then return the product line  
                'direct_bom_id': fields.many2one('mrp.bom','Direct BOM',domain="[('product_id','=',product_id),('bom_id','=',False)]"),
                }
     
    def onchange_product_id(self, cr, uid, ids, product_id, name, context=None):
        res = super(mrp_bom,self).onchange_product_id(cr, uid, ids, product_id, name, context)
        if not res.get('value',False):
            res['value']={}
        #set the direct_bom_id
        if product_id:
            direct_bom_id = self._bom_find(cr, uid, product_id, None, properties=None)
            res['value'].update({'direct_bom_id':direct_bom_id})
        return res
    
    def _bom_explode(self, cr, uid, bom, factor, properties=None, addthis=False, level=0, routing_id=False):
        result, result2 = super(mrp_bom, self)._bom_explode(cr, uid, bom, factor, properties, addthis, level, routing_id)
        phantom = False
        if bom.type == 'phantom' and not bom.bom_lines:
            newbom = self._bom_find(cr, uid, bom.product_id.id, bom.product_uom.id, properties)
            if newbom:
                phantom = True
            else:
                phantom = False
        if not phantom:
            if addthis and not bom.bom_lines and bom.direct_bom_id:
                #remove the line with product_id = bom.product_id
                result_new = []
                for line in result:
                    #'bom_id' comes from the improved _bom_explode at dmp_mrp.mrp.py
                    if not(line.get('product_id',False) == bom.product_id.id and line.get('bom_id',False) == bom.id):
                        result_new.append(line)
                result = result_new
                #fetch the bom data from direct_bom_id
                res = self._bom_explode(cr, uid, bom.direct_bom_id, factor, properties, addthis=True, level=level+10)
                result = result + res[0]
                result2 = result2 + res[1]
        return result, result2