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
class mrp_production(osv.osv):
    _inherit = 'mrp.production'
    _order = 'id desc, priority, date_planned asc';
    _columns = {
        'move_lines': fields.many2many('material.request.line', 'mrp_production_move_ids', 'production_id', 'move_id', 'Products to Consume',
            domain=[('state','not in', ('done', 'cancel'))], readonly=True, states={'draft':[('readonly',False)]}),
        'move_lines2': fields.many2many('material.request.line', 'mrp_production_move_ids', 'production_id', 'move_id', 'Consumed Products',
            domain=[('state','in', ('done', 'cancel'))], readonly=True, states={'draft':[('readonly',False)]}),
    }
    
    def _make_production_consume_line(self, cr, uid, production_line, parent_move_id, source_location_id=False, context=None):
        consume_move_id = super(mrp_production, self)._make_production_consume_line(cr, uid, production_line, parent_move_id, 
                                                                         source_location_id=source_location_id, context=context)
        #johnw, update mrp_production_product_line.consume_move_id once get the consume move
        self.pool.get('mrp.production.product.line').write(cr, uid, production_line.id, {'consume_move_id':consume_move_id},context=context)
        return consume_move_id
    
class mrp_production_workcenter_line(osv.osv):
    _inherit = 'mrp.production.workcenter.line'
    '''
    Get one work order's stock moving by the bom/routing/operation, join with mrp_bom_routing_operation, mrp_production_product_line
    These moves are the moves can make material requistion
    Since one bom component can have more than one routing operation, so one stock move may be occured under several work orders \
    but they are one move in fact. 
    '''
    def _move_lines(self, cr, uid, ids, field_name, arg, context=None):
        res=dict.fromkeys(ids,[])
        sql = '''
        select b.id, c.consume_move_id
        from mrp_bom_routing_operation a
        join mrp_production_workcenter_line b 
            on a.bom_id = b.bom_id and a.routing_id = b.routing_id and a.routing_workcenter_id = b.routing_operation_id and a.consume_material = true
        join mrp_production_product_line c
            on b.production_id = c.production_id and a.bom_comp_id = c.parent_bom_id
        where b.id = ANY(%s)
        '''
        cr.execute(sql, (ids,))
        for data in cr.fetchall():
            res[data[0]].append(data[1])
        return res
    
    _columns = {
        'stock_move_ids': fields.function(_move_lines, relation='material.request.line', type='one2many', string='Material'),
    }

class mrp_production_product_line(osv.osv):
    _inherit = 'mrp.production.product.line'
    _columns = {
        'parent_bom_id': fields.many2one('mrp.bom', string='Parent BOM', readonly=True),
        'bom_id': fields.many2one('mrp.bom', string='BOM', readonly=True),
        'consume_move_id': fields.many2one('stock.move', string='Consume Move', readonly=True),
    }

class mrp_bom(osv.osv):
    _inherit = 'mrp.bom'
    def _hook_bom_prod_line(self, cr, uid, bom):
        '''
        @param bom: mrp.bom object
        @return: dict to fill the mo's product line: mrp_production_product_line
        '''
        data = super(mrp_bom,self)._hook_bom_prod_line(cr, uid, bom)
        #+++John Wang, 07/10/2014+++# add the bom_id and parent_bom_id to supply the product's bom info
        data.update({'parent_bom_id': bom.bom_id and bom.bom_id.id or False, 'bom_id': bom.id})
        return data
    
from openerp.addons.mrp.mrp import mrp_production as mrp_prod_patch
#add the 'consume_move_id' when matching the wo.product_lines and consume moves
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

#                raw_product = [move for move in production.move_lines if move.product_id.id==scheduled.product_id.id]
            #johnw, 07/11/2014, add the 'consume_move_id' when matching the wo.product_lines and consume moves
            #begin
            raw_product = [move for move in production.move_lines if move.product_id.id==scheduled.product_id.id and move.id==scheduled.consume_move_id.id]
            #end                
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

                raw_product[0].action_consume(qty, raw_product[0].location_id.id, context=context)

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