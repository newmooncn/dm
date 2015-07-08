# -*- encoding: utf-8 -*-
from openerp.osv import fields,osv
from openerp.tools.translate import _
from openerp import netsvc

class product(osv.osv):
    _inherit = "product.product"
    #field from module, set the auto pick to false by default
    _defaults = {
        'auto_pick': False
    }
class stock_picking_out(osv.osv):
    _inherit = "stock.picking.out" 
    _columns = {
        'production_id': fields.many2one('mrp.production', 'Manufacture Order', ondelete='set null', select=True),
    }
    _defaults = {
        'production_id': False
    }
    
class stock_picking(osv.osv):
    _inherit = "stock.picking" 
    _columns = {
        'production_id': fields.many2one('mrp.production', 'Manufacture Order', ondelete='set null', select=True),
    }
    _defaults = {
        'production_id': False
    }
    
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        if not default.get('production_id'):
            default['production_id'] = None
        return super(stock_picking, self).copy(cr, uid, id, default, context)
                   
    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        res = super(stock_picking,self).do_partial(cr, uid, ids, partial_datas, context)
        '''
        1.update the quantity_out_available of the target moves
        For MRP, the target moves is mrp.production.move_lines2
        2.Add new picking to MO's picking_ids
        3.trigger related mo to be ready
        '''
        move_obj = self.pool.get('stock.move')
        wf_service = netsvc.LocalService("workflow")
        for pick_id, new_pick_id in res.items():
            if new_pick_id.get('delivered_picking') and pick_id != new_pick_id.get('delivered_picking'):
                new_pick_id = new_pick_id.get('delivered_picking')
            else:
                new_pick_id = None
            if new_pick_id:
                #partial picking
                new_pick = self.browse(cr, uid, new_pick_id, context=context)
                for move in new_pick.move_lines:
                    if move.move_history_ids2 and move.move_history_ids2[0].move_dest_id:
                        move_dest = move.move_history_ids2[0].move_dest_id
                        move_obj.write(cr, uid, move_dest.id, {'quantity_out_available':move_dest.quantity_out_available + move.product_qty})
            else:
                #full picking
                pick = self.browse(cr, uid, pick_id, context=context)
                for move in pick.move_lines:
                    if move.move_dest_id:
                        move_dest = move.move_dest_id
                        move_obj.write(cr, uid, move_dest.id, {'quantity_out_available':move_dest.quantity_out_available + move.product_qty})
            
            mo_obj = self.pool.get('mrp.production')
            mo_ids = mo_obj.search(cr, uid, [('picking_id', '=', pick_id)], context=context)
            if mo_ids:
                if new_pick_id:
                    #update mo's picking_ids
                    mo_obj.write(cr, uid, mo_ids[0], {'picking_ids':[(4,new_pick_id)]}, context=context)
                    self.write(cr, uid, new_pick_id, {'production_id':mo_ids[0]})
                #go to 'ready' state
                wf_service.trg_validate(uid, 'mrp.production', mo_ids[0], 'material_ready', cr)
                    
        return res
    
    #MRP picking move products replacement
    def action_assign(self, cr, uid, ids, *args):
        assign_resu = super(stock_picking, self).action_assign(cr, uid, ids, args)
        if isinstance(ids, list) and len(ids) > 1:
            #only check the replace products for single picking
            return assign_resu
        pick_id = None
        if isinstance(ids, list):
            pick_id = ids[0]
        else:
            pick_id = ids
        #05/25/2015, check all of the stocking moves, pop the window to let user select the alter products for the not available products
        #store the moves found replaced products, format: move_id, prod_old_id, prod_new_id, product_qty, prod_new_available
        replace_moves = []   
        #the products will be replace, format. product_id: product_qty
        replace_products = {}
        pick = self.browse(cr, uid, pick_id)
        if pick.type =='out':
            prod_obj = self.pool.get('product.product')
            field_names=['qty_onhand','qty_out_assigned','qty_out_available']
            for move in pick.move_lines:
                if move.state == 'confirmed' \
                and move.mrp_material_bom_id \
                and move.mrp_material_bom_id.replace_prod_ids\
                and move.move_dest_id\
                and move.product_id.id == move.move_dest_id.product_id.id \
                and move.product_qty == move.move_dest_id.product_qty:
                    context={'location':move.location_id.id}
                    #loop to get all the replaceable product out available
                    for prod in move.mrp_material_bom_id.replace_prod_ids:
                        prod_qty = prod_obj._product_available(cr, uid, [prod.id], field_names, arg=False, context=context)
                        replace_qty = replace_products.get(prod.id,0)
                        prod_qty = prod_qty[prod.id]['qty_out_available'] - replace_qty
                        if prod_qty >= move.product_qty:
                            #the replaceable product is available
                            replace_moves.append({'move_id':move.id, 
                                                  'prod_old_id':move.product_id.id,
                                                  'prod_new_id':prod.id,
                                                  'product_qty':move.product_qty,
                                                  'prod_new_available':prod_qty})
                            
                            replace_qty += move.product_qty
                            replace_products.update({'product_id':replace_qty})
                            break
            
        if replace_moves:
            #create data
            vals = {'picking_id':pick.id}
            replace_lines = []
            for replace in replace_moves:
                replace_lines.append((0,0,replace))
            vals['replace_line_ids'] = replace_lines
            replace_id = self.pool.get('mrp.pick.replace.product').create(cr, uid, vals)
            #go to wizard
            form_view = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'dmp_mrp_material', 'view_mrp_pick_replace_product_form')
            form_view_id = form_view and form_view[1] or False
            return {
                'name': _('Manufacture Picking Products Replacement'),
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': [form_view_id],
                'res_model': 'mrp.pick.replace.product',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': replace_id,
            }    
                    
        else:
            return assign_resu

class mrp_bom(osv.osv):
    _inherit = "mrp.bom" 
    _columns = {
        'replace_prod_ids': fields.many2many('product.product', 'bom_replace_prod', 'bom_id', 'prod_id', 'Replaceable Products',readonly=False),
    }
    
class stock_move(osv.osv):
    _inherit = "stock.move" 
    _columns = {
        'mrp_material_bom_id': fields.many2one('mrp.bom', string='Material BOM', readonly=True),
    }
            
class mrp_production(osv.osv):
    _inherit = 'mrp.production'
    '''
    picking_ids:
    many2many for the multi time material requistions
    the above original picking_id is also link to the newest picking_id
    Except the above picking, the others should be done
    ''' 
    _columns = {
        #change 'ondelete' to setnull, user can delete the MO's picking, and generate again on the MO's screen
        'picking_id': fields.many2one('stock.picking', 'Picking List', readonly=True, ondelete="set null",
            help="This is the Internal Picking List that brings the finished product to the production plan"), 
        'picking_ids': fields.many2many('stock.picking', 'mrp_production_picking_ids', 'mo_id', 'material_pick_id', 'Material Picking',readonly=True),
                               
    }
    
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        if not default.get('picking_ids'):
            default['picking_ids'] = None
        return super(mrp_production, self).copy(cr, uid, id, default, context)

    def _make_production_internal_shipment(self, cr, uid, production, context=None):
        picking_id = super(mrp_production, self)._make_production_internal_shipment(cr, uid, production, context=context)
        #change move_type from 'one' to 'direct', state: auto-->draft
        self.pool.get('stock.picking').write(cr, uid, picking_id, {'move_type':'direct', 'state': 'draft', 'production_id':production.id}, context=context)
        #update mo's picking_ids
        self.write(cr, uid, production.id, {'picking_ids':[(4,picking_id)]}, context=context)
        return picking_id
    
    def _make_production_internal_shipment_line(self, cr, uid, production_line, shipment_id, parent_move_id, destination_location_id=False, context=None):
        move_id = super(mrp_production,self)._make_production_internal_shipment_line(cr, uid, production_line, shipment_id, parent_move_id, destination_location_id, context)
        #state: waiting --> draft
        mrp_material_bom_id = production_line.bom_id and production_line.bom_id.id or None
        self.pool.get('stock.move').write(cr, uid, [move_id], {'state':'draft', 'mrp_material_bom_id': mrp_material_bom_id})
        return move_id
    
    def _action_confirm_material_picking_confirm_before(self, cr, uid, mo, material_pick_id, context=None):
        '''
        Called before do the material picking validation 
        @return:True to allow do picking validation
        johnw, make the internal material picking do auto confirm when the auto picking is true
        '''
        return self._get_auto_picking(cr, uid, mo)
        
from openerp.addons.mrp.mrp import mrp_production as mrp_prod_patch
'''
johnw, 04/25/2015, for the internal mateial picking type, need consider the mo's routing first to decide it is internal or deliver picking
'''
def _make_production_internal_shipment_dmp(self, cr, uid, production, context=None):
    ir_sequence = self.pool.get('ir.sequence')
    stock_picking = self.pool.get('stock.picking')
    routing_loc = None
    pick_type = 'internal'
    partner_id = False

    # Take routing address as a Shipment Address.
    # If usage of routing location is a internal, make outgoing shipment otherwise internal shipment
#    if production.bom_id.routing_id and production.bom_id.routing_id.location_id:
#        routing_loc = production.bom_id.routing_id.location_id
#        if routing_loc.usage != 'internal':
#            pick_type = 'out'
#        partner_id = routing_loc.partner_id and routing_loc.partner_id.id or False
        
    #johnw, 04/25/2015, for the internal mateial picking type, need consider the mo's routing first to decide it is internal or deliver picking
    routing_id = production.routing_id or production.bom_id.routing_id
    if routing_id and routing_id.location_id:
        routing_loc = routing_id.location_id
        if routing_loc.usage != 'internal':
            pick_type = 'out'
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
        'state': 'auto',
        'partner_id': partner_id,
        'auto_picking': self._get_auto_picking(cr, uid, production),
        'company_id': production.company_id.id,
    })
    production.write({'picking_id': picking_id}, context=context)
    return picking_id

mrp_prod_patch._make_production_internal_shipment = _make_production_internal_shipment_dmp 
'''
johnw, 04/25/2014, improve the picking checking, if the picking does not exist then no need raise error
'''
def action_cancel_dmp(self, cr, uid, ids, context=None):
    """ Cancels the production order and related stock moves.
    @return: True
    """
    if context is None:
        context = {}
    move_obj = self.pool.get('stock.move')
    for production in self.browse(cr, uid, ids, context=context):
        #if production.state == 'confirmed' and production.picking_id.state not in ('draft', 'cancel'):
        #improve the picking checking, if the picking does not exist then no need raise error
        if production.state == 'confirmed' and production.picking_id and production.picking_id.state not in ('draft', 'cancel'):
            raise osv.except_osv(
                _('Cannot cancel manufacturing order!'),
                _('You must first cancel related internal picking attached to this manufacturing order.'))
        if production.move_created_ids:
            move_obj.action_cancel(cr, uid, [x.id for x in production.move_created_ids])
        move_obj.action_cancel(cr, uid, [x.id for x in production.move_lines])
    self.write(cr, uid, ids, {'state': 'cancel'})
    return True

mrp_prod_patch.action_cancel = action_cancel_dmp   