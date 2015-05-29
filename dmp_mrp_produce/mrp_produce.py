# -*- encoding: utf-8 -*-
from openerp.osv import fields,osv
from openerp.tools.translate import _
from openerp import netsvc
from openerp.tools import float_compare

class stock_picking_in(osv.osv):
    _inherit = "stock.picking.in" 
    _columns = {
        'production_id': fields.many2one('mrp.production', 'Manufacture Order', ondelete='set null', select=True),
    }
    _defaults = {
        'production_id': False
    }
        
class mrp_production(osv.osv):
    _inherit = 'mrp.production'
    '''
    change the domain for the produced product moves, once there are pikcing_id assigned to them, 
    then we can think the product are produced and warehouse keeper will do the stocking in of the products.
    ''' 
    _columns = {
        'move_created_ids': fields.one2many('stock.move', 'production_id', 'Products to Produce',
            domain=[('picking_id','=', False,)], readonly=True, states={'draft':[('readonly',False)]}),
        'move_created_ids2': fields.one2many('stock.move', 'production_id', 'Produced Products',
            domain=[('picking_id','!=', False)], readonly=True, states={'draft':[('readonly',False)]}),   
        
#        'move_lines2': fields.many2many('stock.move', 'mrp_production_move_ids', 'production_id', 'move_id', 'Consumed Products',
#            domain=[('state','in', ('done', 'cancel'))], readonly=True, states={'draft':[('readonly',False)]}),          
    }

    def _make_production_produce_line(self, cr, uid, production, context=None):
        #update the produce product move line's quantity_out_available
        move_id = super(mrp_production,self)._make_production_produce_line(cr, uid, production, context=context)
        self.pool.get('stock.move').write(cr, uid, [move_id], {'quantity_out_available':production.product_qty}, context=context)
        return move_id
            
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
            #johnw, add the checking for the produced prodcuts move's state checking
            if production.move_created_ids2:
                for move in production.move_created_ids2:
                    if move.state != 'done':
                        res = False
                        break
        return res
        
    def _make_production_done_pick(self, cr, uid, production, context=None):
        ir_sequence = self.pool.get('ir.sequence')
        stock_picking = self.pool.get('stock.picking.in')
        routing_loc = None
        pick_type = 'in'
        partner_id = False

        # Take routing address as a Shipment Address.
        # If usage of routing location is a internal, make outgoing shipment otherwise internal shipment
        routing_id = production.routing_id or production.bom_id.routing_id
        if routing_id and routing_id.location_id:
            routing_loc = routing_id.location_id
            if routing_loc.usage == 'internal':
                pick_type = 'internal'
            partner_id = routing_loc.partner_id and routing_loc.partner_id.id or False

        # Take next Sequence number of shipment base on type
        if pick_type!='internal':
            pick_name = ir_sequence.get(cr, uid, 'stock.picking.' + pick_type)
        else:
            pick_name = ir_sequence.get(cr, uid, 'stock.picking')
            
        warehouse_ids = self.pool.get('stock.warehouse').search(cr, uid, [('lot_input_id','=',production.location_dest_id.id),\
                                                  ('lot_stock_id','=',production.location_dest_id.id)], \
                                        context=context)
        picking_id = stock_picking.create(cr, uid, {
            'name': pick_name,
            'origin': (production.origin or '').split(':')[0] + ':' + production.name,
            'type': pick_type,
            'move_type': 'one',
            'state': 'assigned',
            'partner_id': partner_id,
            'auto_picking': self._get_auto_picking(cr, uid, production),
            'company_id': production.company_id.id,
            'warehouse_id': warehouse_ids and warehouse_ids[0],
            'production_id': production.id
        })
        return picking_id
    
    def _produce_consume_product_get_context(self, cr, uid, mo, product_move, context=None):
        '''
        add context 'stock_move_consume_manual_done' parameter when do producing
        @return: the context that will be transfered to the produced product consuming action_consume()
        '''
        c = context.copy()
        c['stock_move_consume_manual_done'] = True        
        return c
'''
johnw, 04/16/2015, generate a product picking for the production finishing
'''
class stock_move(osv.osv):
    _inherit = 'stock.move'

    def action_consume_done_before(self, cr, uid, ids, context=None):
        '''
        johnw, 04/16/2015, add the 'stock_move_consume_manual_done' flag checking in the context
        will be used for the mrp production(mo.action_produce()) to produce a product
        generated one new move but not finish it automatically.
        '''    
        if context:       
            return not context.get('stock_move_consume_manual_done')
        else:
            return True
    
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
#                for move in self.browse(cr, uid, new_moves, context=context):
#                    self.write(cr, uid, move.id, {'quantity_out_available':move.product_qty}, context=context)
                #cr.execute('update stock_move set quantity_out_available=product_qty where picking_id=%s' % (picking_done_id,))
#                self.pool.get('stock.picking').draft_force_assign(cr, uid, [picking_done_id])
                netsvc.LocalService("workflow").trg_validate(uid, 'stock.picking', picking_done_id,'button_confirm', cr)
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
            #mrp_production.test_production_done() will be call
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
        print move.state
        #move.action_confirm(context)
        #new_moves = super(StockMove, self).action_consume(cr, uid, [move.id], product_qty, location_id, context=context)
        new_moves = super(stock_move_mrp_patch, self).action_consume(cr, uid, [move.id], product_qty, location_id, context=context)
        production_ids = production_obj.search(cr, uid, [('move_lines', 'in', [move.id])])
        for prod in production_obj.browse(cr, uid, production_ids, context=context):
            if prod.state == 'confirmed':
                production_obj.force_production(cr, uid, [prod.id])
            wf_service.trg_validate(uid, 'mrp.production', prod.id, 'button_produce', cr)
        for new_move in new_moves:
            '''
            johnw, 04/16/2015, also return the move_ids without new moves created, 
            this will keep the stock_move.action_consume() original logic, do not remove the data(new_move == move.id)
            And the action_consume() of MO's producing product will use the returned move ids to generate a picking in for the products.
            '''
            res.append(new_move)
            if new_move == move.id:
                #This move is already there in move lines of production order
                continue
            production_obj.write(cr, uid, production_ids, {'move_lines': [(4, new_move)]})
            #res.append(new_move)
    return res    
stock_move_mrp_patch.action_consume = action_consume_mrp_dmp_mrp_pick    