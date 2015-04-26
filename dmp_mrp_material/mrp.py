# -*- encoding: utf-8 -*-
from openerp.osv import fields,osv
from openerp.tools.translate import _
from openerp import netsvc
from openerp.tools import float_compare
    
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
    
    def _produce_consume_material_get_raw_products(self, cr, uid, mo, mo_scheduled_product, context=None):
        #add the 'consume_move_id' when matching the wo.product_lines and consume moves
        return [move for move in mo.move_lines if move.product_id.id==mo_scheduled_product.product_id.id and move.id==mo_scheduled_product.consume_move_id.id]
    
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