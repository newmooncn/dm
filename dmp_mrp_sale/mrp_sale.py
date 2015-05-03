# -*- encoding: utf-8 -*-
from openerp.osv import fields,osv
    
class mrp_production(osv.osv):
    _inherit = 'mrp.production'
    _columns = {
        'customer_id': fields.many2one('res.partner', 'Customer', domain=[('customer','=',True),('is_company','=',True)],\
                                       readonly=True, states={'draft': [('readonly', False)]}),
        'customer_product_name': fields.char('Customer Product Name', size=128, readonly=True, states={'draft': [('readonly', False)]}),          
    }
    def onchange_customer_id(self, cr, uid, ids, customer_id, product_id, context=None):
        cust_prod_name = None
        if customer_id and product_id:
            cust_prod_name = self.pool.get("product.product").get_customer_product(cr, uid, customer_id, product_id, context=context)
        return {'value':{'customer_product_name':cust_prod_name}}