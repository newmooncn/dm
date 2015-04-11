# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp.addons.mrp.mrp import rounding as mrp_rounding
from openerp import tools

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