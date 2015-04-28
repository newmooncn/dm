# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp.addons.mrp.mrp import rounding as mrp_rounding
from openerp import tools
from openerp import netsvc
from openerp.tools import float_compare

class mrp_bom(osv.osv):
    _inherit = 'mrp.bom'
    def _hook_bom_prod_line(self, cr, uid, bom):
        '''
        @param bom: mrp.bom object
        @return: dict to fill the mo's product line: mrp_production_product_line
        '''
        return {}
    
    def _hook_bom_wo_line(self, cr, uid, bom, route_workcenter):
        '''
        @param bom: mrp.bom object
        @param route_workcenter: mrp.routing.workcenter_lines: mrp.routing.workcenter
        @return: dict to fill the mo's workorder: mrp_production_workcenter_line
        '''
        return {}
    
'''
Add hook methods for the prod&wo line data filling
_hook_bom_prod_line(cr, uid, bom)
_hook_bom_wo_line(cr, uid, bom, route_workcenter)
'''
from openerp.addons.mrp.mrp import mrp_bom as mrp_bom_patch
def _bom_explode_dmp_mrp(self, cr, uid, bom, factor, properties=None, addthis=False, level=0, routing_id=False):
    """ Finds Products and Work Centers for related BoM for manufacturing order.
    @param bom: BoM of particular product.
    @param factor: Factor of product UoM.
    @param properties: A List of properties Ids.
    @param addthis: If BoM found then True else False.
    @param level: Depth level to find BoM lines starts from 10.
    @return: result: List of dictionaries containing product details.
             result2: List of dictionaries containing Work Center details.
    """
    routing_obj = self.pool.get('mrp.routing')
    factor = factor / (bom.product_efficiency or 1.0)
    #+++John Wang+++, 07/10/2014# change to use mrp_rounding refer the mrp.rounding
    #factor = _common.ceiling(factor, bom.product_rounding)
    factor = mrp_rounding(factor, bom.product_rounding)
    if factor < bom.product_rounding:
        factor = bom.product_rounding
    result = []
    result2 = []
    phantom = False
    if bom.type == 'phantom' and not bom.bom_lines:
        newbom = self._bom_find(cr, uid, bom.product_id.id, bom.product_uom.id, properties)

        if newbom:
            res = self._bom_explode(cr, uid, self.browse(cr, uid, [newbom])[0], factor*bom.product_qty, properties, addthis=True, level=level+10)
            result = result + res[0]
            result2 = result2 + res[1]
            phantom = True
        else:
            phantom = False
    if not phantom:
        if addthis and not bom.bom_lines:
#            result.append(
#            {
#                'name': bom.product_id.name,
#                'product_id': bom.product_id.id,
#                'product_qty': bom.product_qty * factor,
#                'product_uom': bom.product_uom.id,
#                'product_uos_qty': bom.product_uos and bom.product_uos_qty * factor or False,
#                'product_uos': bom.product_uos and bom.product_uos.id or False,
#            })
            #johnw, add hook for other customized code to fill more data of product line of mo
            prod_data = {
                    'name': bom.product_id.name,
                    'product_id': bom.product_id.id,
                    'product_qty': bom.product_qty * factor,
                    'product_uom': bom.product_uom.id,
                    'product_uos_qty': bom.product_uos and bom.product_uos_qty * factor or False,
                    'product_uos': bom.product_uos and bom.product_uos.id or False,
                    }
            prod_data.update(self._hook_bom_prod_line(cr, uid, bom))
            result.append(prod_data)
            
        routing = (routing_id and routing_obj.browse(cr, uid, routing_id)) or bom.routing_id or False
        if routing:
            for wc_use in routing.workcenter_lines:
                wc = wc_use.workcenter_id
                d, m = divmod(factor, wc_use.workcenter_id.capacity_per_cycle)
                mult = (d + (m and 1.0 or 0.0))
                cycle = mult * wc_use.cycle_nbr
#                    result2.append({
#                        'name': tools.ustr(wc_use.name) + ' - '  + tools.ustr(bom.product_id.name),
#                        'workcenter_id': wc.id,
#                        'sequence': level+(wc_use.sequence or 0),
#                        'cycle': cycle,
#                        'hour': float(wc_use.hour_nbr*mult + ((wc.time_start or 0.0)+(wc.time_stop or 0.0)+cycle*(wc.time_cycle or 0.0)) * (wc.time_efficiency or 1.0)),
#                    })
                #johnw, add hook for other customized code to fill more data of work order line of mo
                wo_data = {
                    'name': tools.ustr(wc_use.name) + ' - '  + tools.ustr(bom.product_id.name),
                    'workcenter_id': wc.id,
                    'sequence': level+(wc_use.sequence or 0),
                    'cycle': cycle,
                    'hour': float(wc_use.hour_nbr*mult + ((wc.time_start or 0.0)+(wc.time_stop or 0.0)+cycle*(wc.time_cycle or 0.0)) * (wc.time_efficiency or 1.0)),
                }
                wo_data.update(self._hook_bom_wo_line(cr, uid, bom, wc_use))
                result2.append(wo_data)
                                    
        for bom2 in bom.bom_lines:
            res = self._bom_explode(cr, uid, bom2, factor, properties, addthis=True, level=level+10)
            result = result + res[0]
            result2 = result2 + res[1]
            
    return result, result2

mrp_bom_patch._bom_explode = _bom_explode_dmp_mrp

class mrp_production(osv.osv):
    _inherit = 'mrp.production'
    def _produce_consume_material_get_raw_products(self, cr, uid, mo, mo_scheduled_product, context=None):
        '''
        called before do the raw material consuming, to get the material moves need to consume
        @return: the move list for one MO's consuming product
        '''
        return [move for move in mo.move_lines if move.product_id.id==mo_scheduled_product.product_id.id]
    def _produce_consume_product_get_context(self, cr, uid, mo, product_move, context=None):
        '''
        @return: the context that will be transfered to the produced product consuming action_consume()
        '''
        return context
    def _action_confirm_material_picking_confirm_before(self, cr, uid, material_pick_id, context=None):
        '''
        Called before do the material picking validation 
        @return:True to allow do picking validation
        '''
        return True
    
from openerp.addons.mrp.mrp import mrp_production as mrp_prod_patch
'''
johnw, 04/26/2015, add hooks:
_produce_consume_material_get_raw_products()
_produce_consume_product_get_context()
'''
def action_produce_dmp_mrp(self, cr, uid, production_id, production_qty, production_mode, context=None):
    """ To produce final product based on production mode (consume/consume&produce).
    If Production mode is consume, all stock move lines of raw materials will be done/consumed.
    If Production mode is consume & produce, all stock move lines of raw materials will be done/consumed
    and stock move lines of final product will be also done/produced.
    @param production_id: the ID of mrp.production object
    @param production_qty: specify qty to produce
    @param production_mode: specify production mode (consume/consume&produce).
    @return: True
    """
    stock_mov_obj = self.pool.get('stock.move')
    production = self.browse(cr, uid, production_id, context=context)

    wf_service = netsvc.LocalService("workflow")
    if not production.move_lines and production.state == 'ready':
        # trigger workflow if not products to consume (eg: services)
        wf_service.trg_validate(uid, 'mrp.production', production_id, 'button_produce', cr)

    produced_qty = 0
    for produced_product in production.move_created_ids2:
        if (produced_product.scrapped) or (produced_product.product_id.id != production.product_id.id):
            continue
        produced_qty += produced_product.product_qty
    if production_mode in ['consume','consume_produce']:
        consumed_data = {}

        # Calculate already consumed qtys
        for consumed in production.move_lines2:
            if consumed.scrapped:
                continue
            if not consumed_data.get(consumed.product_id.id, False):
                consumed_data[consumed.product_id.id] = 0
            consumed_data[consumed.product_id.id] += consumed.product_qty

        # Find product qty to be consumed and consume it
        for scheduled in production.product_lines:

            # total qty of consumed product we need after this consumption
            total_consume = ((production_qty + produced_qty) * scheduled.product_qty / production.product_qty)

            # qty available for consume and produce
            qty_avail = scheduled.product_qty - consumed_data.get(scheduled.product_id.id, 0.0)

            if float_compare(qty_avail, 0, precision_rounding=scheduled.product_id.uom_id.rounding) <= 0:
                # there will be nothing to consume for this raw material
                continue            
            
            #johnw, 04/26/2015, add hook to get raw material consuming moves for one scheduled mo's product line
            #raw_product = [move for move in production.move_lines if move.product_id.id==scheduled.product_id.id]
            raw_product = self._produce_consume_material_get_raw_products(cr, uid, production, scheduled, context=context)
            if raw_product:
                # qtys we have to consume
                qty = total_consume - consumed_data.get(scheduled.product_id.id, 0.0)
                if float_compare(qty, qty_avail, precision_rounding=scheduled.product_id.uom_id.rounding) == 1:
                    # if qtys we have to consume is more than qtys available to consume
                    prod_name = scheduled.product_id.name_get()[0][1]
                    raise osv.except_osv(_('Warning!'), _('You are going to consume total %s quantities of "%s".\nBut you can only consume up to total %s quantities.') % (qty, prod_name, qty_avail))
                if float_compare(qty, 0, precision_rounding=scheduled.product_id.uom_id.rounding) <= 0:                        
                    # we already have more qtys consumed than we need
                    continue
                #johnw, change calling use stock_mov_obj
                #raw_product[0].action_consume(qty, raw_product[0].location_id.id, context=context)
                stock_mov_obj.action_consume(cr, uid, [raw_product[0].id], qty, raw_product[0].location_id.id, context=context)

    if production_mode == 'consume_produce':
        # To produce remaining qty of final product
        #vals = {'state':'confirmed'}
        #final_product_todo = [x.id for x in production.move_created_ids]
        #stock_mov_obj.write(cr, uid, final_product_todo, vals)
        #stock_mov_obj.action_confirm(cr, uid, final_product_todo, context)
        produced_products = {}
        for produced_product in production.move_created_ids2:
            if produced_product.scrapped:
                continue
            if not produced_products.get(produced_product.product_id.id, False):
                produced_products[produced_product.product_id.id] = 0
            produced_products[produced_product.product_id.id] += produced_product.product_qty

        for produce_product in production.move_created_ids:
            produced_qty = produced_products.get(produce_product.product_id.id, 0)
            subproduct_factor = self._get_subproduct_factor(cr, uid, production.id, produce_product.id, context=context)
            rest_qty = (subproduct_factor * production.product_qty) - produced_qty

            if rest_qty < (subproduct_factor * production_qty):
                prod_name = produce_product.product_id.name_get()[0][1]
                raise osv.except_osv(_('Warning!'), _('You are going to produce total %s quantities of "%s".\nBut you can only produce up to total %s quantities.') % ((subproduct_factor * production_qty), prod_name, rest_qty))
            if rest_qty > 0 :
                stock_mov_obj.action_consume(cr, uid, [produce_product.id], (subproduct_factor * production_qty), context=context)
                #johnw, 04/26/2015, add hook to get produced product's consuming context
                c = self._produce_consume_product_get_context(cr, uid, production, produce_product, context=context)
                stock_mov_obj.action_consume(cr, uid, [produce_product.id], (subproduct_factor * production_qty), context=c)

    for raw_product in production.move_lines2:
        new_parent_ids = []
        parent_move_ids = [x.id for x in raw_product.move_history_ids]
        for final_product in production.move_created_ids2:
            if final_product.id not in parent_move_ids:
                new_parent_ids.append(final_product.id)
        for new_parent_id in new_parent_ids:
            stock_mov_obj.write(cr, uid, [raw_product.id], {'move_history_ids': [(4,new_parent_id)]})

    wf_service.trg_validate(uid, 'mrp.production', production_id, 'button_produce_done', cr)
    return True

mrp_prod_patch.action_produce = action_produce_dmp_mrp    
'''
add the hook: _action_confirm_material_picking_confirm_before()
'''
def action_confirm_dmp_mrp(self, cr, uid, ids, context=None):
    """ Confirms production order.
    @return: Newly generated Shipment Id.
    """
    shipment_id = False
    wf_service = netsvc.LocalService("workflow")
    uncompute_ids = filter(lambda x:x, [not x.product_lines and x.id or False for x in self.browse(cr, uid, ids, context=context)])
    self.action_compute(cr, uid, uncompute_ids, context=context)
    for production in self.browse(cr, uid, ids, context=context):
        shipment_id = self._make_production_internal_shipment(cr, uid, production, context=context)
        produce_move_id = self._make_production_produce_line(cr, uid, production, context=context)

        # Take routing location as a Source Location.
        source_location_id = production.location_src_id.id
        if production.routing_id and production.routing_id.location_id:
            source_location_id = production.routing_id.location_id.id

        for line in production.product_lines:
            consume_move_id = self._make_production_consume_line(cr, uid, line, produce_move_id, source_location_id=source_location_id, context=context)
            if shipment_id:
                shipment_move_id = self._make_production_internal_shipment_line(cr, uid, line, shipment_id, consume_move_id,\
                             destination_location_id=source_location_id, context=context)
                self._make_production_line_procurement(cr, uid, line, shipment_move_id, context=context)
            
        #johnw, add the hook: action_confirm_material_picking_confirm_before()
        #if shipment_id:
        if shipment_id and self._action_confirm_material_picking_confirm_before(cr, uid, production, shipment_id):
            wf_service.trg_validate(uid, 'stock.picking', shipment_id, 'button_confirm', cr)
        production.write({'state':'confirmed'}, context=context)
    return shipment_id

mrp_prod_patch.action_confirm = action_confirm_dmp_mrp