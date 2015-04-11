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
                #09/12/2014, the flag to tell system do not generate consuming move lines, will be used in manufacture order, the the action_compute()-->_bom_explode()
                'no_consume': fields.boolean('No Consume'),
                }
    _defaults = {
        'no_consume' : False,
    }
    
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
            if addthis and not bom.bom_lines and bom.no_consume:
                #remove the line with product_id = bom.product_id and bom_id = bom.id
                result_new = []
                for line in result:
                    #'bom_id' comes from the improved _bom_explode at dmp_mrp.mrp.py
                    if not(line.get('product_id',False) == bom.product_id.id and line.get('bom_id',False) == bom.id):
                        result_new.append(line)
                result = result_new
        return result, result2