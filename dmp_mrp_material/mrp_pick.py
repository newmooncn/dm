# -*- encoding: utf-8 -*-
from openerp.osv import fields,osv
from openerp.tools.translate import _
from openerp import netsvc
from openerp.tools import float_compare

class product(osv.osv):
    _inherit = "product.product"
    #field from module, set the auto pick to false by default
    _defaults = {
        'auto_pick': False
    }
    
class mrp_production(osv.osv):
    _inherit = 'mrp.production'
    _columns = {
        'move_created_ids': fields.one2many('stock.move', 'production_id', 'Products to Produce',
            domain=[('picking_id','=', False,)], readonly=True, states={'draft':[('readonly',False)]}),
        'move_created_ids2': fields.one2many('stock.move', 'production_id', 'Produced Products',
            domain=[('picking_id','!=', False)], readonly=True, states={'draft':[('readonly',False)]}),
    }

    def _make_production_internal_shipment(self, cr, uid, production, context=None):
        picking_id = super(mrp_production, self)._make_production_internal_shipment(cr, uid, production, context=context)
        self.pool.get('stock.picking').write(cr, uid, picking_id, {'state': 'draft'}, context=context)
        return picking_id
        
    def test_production_done(self, cr, uid, ids):
        """ Tests whether production is done or not.
        @return: True or False
        """
        res = True
        for production in self.browse(cr, uid, ids):
            if production.move_lines:
                res = False
                break
            if production.move_created_ids:
                res = False
                break
            if production.move_created_ids2:
                for move in production.move_created_ids2:
                    if move.state != 'done':
                        res = False
                        break
        return res
        
    def _make_production_done_pick(self, cr, uid, production, context=None):
        ir_sequence = self.pool.get('ir.sequence')
        stock_picking = self.pool.get('stock.picking')
        routing_loc = None
        pick_type = 'internal'
        partner_id = False

        # Take routing address as a Shipment Address.
        # If usage of routing location is a internal, make outgoing shipment otherwise internal shipment
        if production.bom_id.routing_id and production.bom_id.routing_id.location_id:
            routing_loc = production.bom_id.routing_id.location_id
            if routing_loc.usage != 'internal':
                pick_type = 'in'
            partner_id = routing_loc.partner_id and routing_loc.partner_id.id or False

        # Take next Sequence number of shipment base on type
        if pick_type!='internal':
            pick_name = ir_sequence.get(cr, uid, 'stock.picking.' + pick_type)
        else:
            pick_name = ir_sequence.get(cr, uid, 'stock.picking')

        picking_id = stock_picking.create(cr, uid, {
            'name': pick_name,
            'origin': (production.origin or '').split(':')[0] + ':' + production.name,
            'type': pick_type,
            'move_type': 'one',
            'state': 'assigned',
            'partner_id': partner_id,
            'auto_picking': self._get_auto_picking(cr, uid, production),
            'company_id': production.company_id.id,
        })
        return picking_id

'''
johnw, 04/16/2015, add the 'stock_move_consume_manual_done' flag checking in the context
will be used for the mrp production to generated one new move but not finish it automatically.
'''    
from openerp.addons.stock.stock import stock_move as stock_move_patch
def action_consume_dmp_mrp_pick(self, cr, uid, ids, quantity, location_id=False, context=None):
    """ Consumed product with specific quatity from specific source location
    @param cr: the database cursor
    @param uid: the user id
    @param ids: ids of stock move object to be consumed
    @param quantity : specify consume quantity
    @param location_id : specify source location
    @param context: context arguments
    @return: Consumed lines
    """
    #quantity should in MOVE UOM
    if context is None:
        context = {}
    if quantity <= 0:
        raise osv.except_osv(_('Warning!'), _('Please provide proper quantity.'))
    res = []
    for move in self.browse(cr, uid, ids, context=context):
        move_qty = move.product_qty
        if move_qty <= 0:
            raise osv.except_osv(_('Error!'), _('Cannot consume a move with negative or zero quantity.'))
        quantity_rest = move.product_qty
        quantity_rest -= quantity
        uos_qty_rest = quantity_rest / move_qty * move.product_uos_qty
        if quantity_rest <= 0:
            quantity_rest = 0
            uos_qty_rest = 0
            quantity = move.product_qty

        uos_qty = quantity / move_qty * move.product_uos_qty
        if float_compare(quantity_rest, 0, precision_rounding=move.product_id.uom_id.rounding):
            default_val = {
                'product_qty': quantity,
                'product_uos_qty': uos_qty,
                'state': move.state,
                'location_id': location_id or move.location_id.id,
            }
            current_move = self.copy(cr, uid, move.id, default_val)
            res += [current_move]
            update_val = {}
            update_val['product_qty'] = quantity_rest
            update_val['product_uos_qty'] = uos_qty_rest
            self.write(cr, uid, [move.id], update_val)

        else:
            quantity_rest = quantity
            uos_qty_rest =  uos_qty
            res += [move.id]
            update_val = {
                    'product_qty' : quantity_rest,
                    'product_uos_qty' : uos_qty_rest,
                    'location_id': location_id or move.location_id.id,
            }
            self.write(cr, uid, [move.id], update_val)
    #johnw, 04/16/2015, add 'stock_move_consume_manual_done' paramter handling
    #self.action_done(cr, uid, res, context=context)
    if not context.get('stock_move_consume_manual_done'):
        self.action_done(cr, uid, res, context=context)

    return res    

stock_move_patch.action_consume = action_consume_dmp_mrp_pick   

'''
johnw, 04/16/2015, generate a product picking for the production finishing
'''
class stock_move(osv.osv):
    _inherit = 'stock.move'
    def action_consume(self, cr, uid, ids, product_qty, location_id=False, context=None):
        """ Consumed product with specific quatity from specific source location.
        @param product_qty: Consumed product quantity
        @param location_id: Source location
        @return: Consumed lines
        """       
        '''
        johnw, 04/16/2015, generate picking based on 
        stock.stock.stock_move.action_consume 
        action_consume_dmp_mrp_pick
        mrp.stock.StockMove.action_consume()
        '''
        new_moves = super(stock_move, self).action_consume(cr, uid, ids, product_qty, location_id=location_id, context=context)
        if context.get('stock_move_consume_manual_done'):
            #create the product done picking, and assign it to the done moves
            production_obj = self.pool.get('mrp.production')
            production_ids = production_obj.search(cr, uid, [('move_created_ids', 'in', new_moves)])
            if production_ids:
                mo = production_obj.browse(cr, uid, production_ids[0], context=context)
                picking_done_id = production_obj._make_production_done_pick(cr, uid, mo, context=context)
                self.write(cr, uid, new_moves, {'picking_id':picking_done_id}, context=context)
                self.pool.get('stock.picking').draft_force_assign(cr, uid, [picking_done_id])
                self.pool.get('stock.picking').force_assign(cr, uid, [picking_done_id])
            
        return new_moves
    
    '''
    johnw, call the realted mo's done method
    '''
    def action_done(self, cr, uid, ids, context=None):
        resu = super(stock_move,self).action_done(cr, uid, ids, context=context)
        done_moves = self.search(cr, uid, [('id','in',ids),('state','=','done')], context=context)
        production_ids = self.pool.get('mrp.production').search(cr, uid, [('move_created_ids2', 'in', done_moves)])
        if production_ids:
            netsvc.LocalService("workflow").trg_validate(uid, 'mrp.production', production_ids[0], 'button_produce_done', cr)
        return resu
'''
johnw, 04/16/2015, also return the move_ids without new moves created
'''            
from openerp.addons.mrp.stock import StockMove as stock_move_mrp_patch
def action_consume_mrp_dmp_mrp_pick(self, cr, uid, ids, product_qty, location_id=False, context=None):
    """ Consumed product with specific quatity from specific source location.
    @param product_qty: Consumed product quantity
    @param location_id: Source location
    @return: Consumed lines
    """       
    res = []
    production_obj = self.pool.get('mrp.production')
    wf_service = netsvc.LocalService("workflow")
    for move in self.browse(cr, uid, ids):
        move.action_confirm(context)
        #new_moves = super(StockMove, self).action_consume(cr, uid, [move.id], product_qty, location_id, context=context)
        new_moves = super(stock_move_mrp_patch, self).action_consume(cr, uid, [move.id], product_qty, location_id, context=context)
        production_ids = production_obj.search(cr, uid, [('move_lines', 'in', [move.id])])
        for prod in production_obj.browse(cr, uid, production_ids, context=context):
            if prod.state == 'confirmed':
                production_obj.force_production(cr, uid, [prod.id])
            wf_service.trg_validate(uid, 'mrp.production', prod.id, 'button_produce', cr)
        for new_move in new_moves:
            #johnw, 04/16/2015, also return the move_ids without new moves created
            res.append(new_move)
            if new_move == move.id:
                #This move is already there in move lines of production order
                continue
            production_obj.write(cr, uid, production_ids, {'move_lines': [(4, new_move)]})
            #res.append(new_move)
    return res    
stock_move_mrp_patch.action_consume = action_consume_mrp_dmp_mrp_pick    