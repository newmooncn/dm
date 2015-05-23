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

from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import fields
from openerp.osv import osv
from openerp.tools.translate import _
from openerp import netsvc

class procurement_order(osv.osv):
    _inherit = 'procurement.order'
    
    def make_mo(self, cr, uid, ids, context=None):
        """ Make Manufacturing(production) order from procurement
        @return: New created Production Orders procurement wise 
        """
        res = {}
        company = self.pool.get('res.users').browse(cr, uid, uid, context).company_id
        production_obj = self.pool.get('mrp.production')
        move_obj = self.pool.get('stock.move')
        wf_service = netsvc.LocalService("workflow")
        procurement_obj = self.pool.get('procurement.order')
        for procurement in procurement_obj.browse(cr, uid, ids, context=context):
            res_id = procurement.move_id.id
            newdate = datetime.strptime(procurement.date_planned, '%Y-%m-%d %H:%M:%S') - relativedelta(days=procurement.product_id.produce_delay or 0.0)
            newdate = newdate - relativedelta(days=company.manufacturing_lead)
            #get the bom_id and routing id, johnw, 08/04/2014
            #begin
            bom_id = procurement.bom_id and procurement.bom_id.id or False
            if not bom_id:
                props = procurement.property_ids and [prop.id for prop in procurement.property_ids] or None
                bom_id = self.pool.get('mrp.bom')._bom_find(cr, uid, procurement.product_id.id, procurement.product_uom.id, props)
            routing_id = bom_id and self.pool.get('mrp.bom').browse(cr,uid,bom_id,context=context).routing_id.id or False
            #end
            produce_id = production_obj.create(cr, uid, {
                'origin': procurement.origin,
                'product_id': procurement.product_id.id,
                'product_qty': procurement.product_qty,
                'product_uom': procurement.product_uom.id,
                'product_uos_qty': procurement.product_uos and procurement.product_uos_qty or False,
                'product_uos': procurement.product_uos and procurement.product_uos.id or False,
                #use system default material source location, johnw, 05/10/2014
#                'location_src_id': procurement.location_id.id,
                'location_dest_id': procurement.location_id.id,
                #johnw, improve the bom_id logic
                #'bom_id': procurement.bom_id and procurement.bom_id.id or False,
                'bom_id': bom_id,
                'date_planned': newdate.strftime('%Y-%m-%d %H:%M:%S'),
                'move_prod_id': res_id,
                'company_id': procurement.company_id.id,
                #add the routing_id, johnw@07/14/2014    
                'routing_id': routing_id,           
            })
            
            res[procurement.id] = produce_id
            self.write(cr, uid, [procurement.id], {'state': 'running', 'production_id': produce_id})  
            #johnw, 05/10/2015, disable the auto confirm MO 
#            bom_result = production_obj.action_compute(cr, uid,
#                    [produce_id], properties=[x.id for x in procurement.property_ids])
#            wf_service.trg_validate(uid, 'mrp.production', produce_id, 'button_confirm', cr)
            
            '''
            johnw, remove the code, 05/23/2015, the procurement.order.move_id.location_id is the product_product.property_stock_procurement
            see procurement.order.action_confirm() for detail
            '''
            #johnw, add the location_id
#            if res_id:
#                move_obj.write(cr, uid, [res_id],{'location_id': procurement.location_id.id})
                
        self.production_order_create_note(cr, uid, ids, context=context)
        return res

procurement_order()

class sale_order(osv.osv):
    _inherit = 'sale.order'
    #add bom_id
    def _prepare_order_line_procurement(self, cr, uid, order, line, move_id, date_planned, context=None):
        result = super(sale_order, self)._prepare_order_line_procurement(cr, uid, order, line, move_id, date_planned, context)
        if line.type == 'make_to_order' and line.product_id.supply_method == 'produce':
            #get the bom_id
            props = line.property_ids and [prop.id for prop in line.property_ids] or None
            bom_id = self.pool.get('mrp.bom')._bom_find(cr, uid, line.product_id.id, False, props)
            #bom_id
            result.update({'bom_id': bom_id})
        return result
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
