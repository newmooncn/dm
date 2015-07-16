from openerp.osv import osv, fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
from openerp.tools.translate import _
from openerp.osv.orm import browse_record, browse_null
from openerp import netsvc

class purchase_order(osv.osv):  
    _inherit = "purchase.order"
    #inherited from purchase.py.purchase_order.do_merge(),
    #copy the old po line's procurement_id to the new line
    def do_merge(self, cr, uid, ids, context=None):
        def get_new_origin(old_origin, so_name):
            if old_origin.find(so_name) >= 0: return False
            return old_origin + ' '+ so_name
        """
        To merge similar type of purchase orders.
        Orders will only be merged if:
        * Purchase Orders are in draft
        * Purchase Orders belong to the same partner
        * Purchase Orders are have same stock location, same pricelist
        Lines will only be merged if:
        * Order lines are exactly the same except for the quantity and unit

         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param ids: the ID or list of IDs
         @param context: A standard dictionary

         @return: new purchase order id

        """
        #TOFIX: merged order line should be unlink
        wf_service = netsvc.LocalService("workflow")
        def make_key(br, fields):
            list_key = []
            for field in fields:
                field_val = getattr(br, field)
                if field in ('product_id', 'move_dest_id', 'account_analytic_id'):
                    if not field_val:
                        field_val = False
                if isinstance(field_val, browse_record):
                    field_val = field_val.id
                elif isinstance(field_val, browse_null):
                    field_val = False
                elif isinstance(field_val, list):
                    field_val = ((6, 0, tuple([v.id for v in field_val])),)
                list_key.append((field, field_val))
            list_key.sort()
            return tuple(list_key)

        # Compute what the new orders should contain

        new_orders = {}

        for porder in [order for order in self.browse(cr, uid, ids, context=context) if order.state == 'draft']:
            order_key = make_key(porder, ('partner_id', 'location_id', 'pricelist_id'))
            new_order = new_orders.setdefault(order_key, ({}, []))
            new_order[1].append(porder.id)
            order_infos = new_order[0]
            if not order_infos:
                order_infos.update({
                    'origin': porder.origin,
                    'date_order': porder.date_order,
                    'partner_id': porder.partner_id.id,
                    'dest_address_id': porder.dest_address_id.id,
                    'warehouse_id': porder.warehouse_id.id,
                    'location_id': porder.location_id.id,
                    'pricelist_id': porder.pricelist_id.id,
                    'state': 'draft',
                    'order_line': {},
                    'notes': '%s' % (porder.notes or '',),
                    'fiscal_position': porder.fiscal_position and porder.fiscal_position.id or False,
                })
            else:
                if porder.date_order < order_infos['date_order']:
                    order_infos['date_order'] = porder.date_order
                if porder.notes:
                    order_infos['notes'] = (order_infos['notes'] or '') + ('\n%s' % (porder.notes,))
                if porder.origin:
                    new_origin = get_new_origin((order_infos['origin'] or ''),porder.origin)
                    if new_origin: order_infos['origin'] = new_origin

            for order_line in porder.order_line:
                line_key = make_key(order_line, ('name', 'date_planned', 'taxes_id', 'price_unit', 'product_id', 'move_dest_id', 'account_analytic_id', 'procurement_id'))
                o_line = order_infos['order_line'].setdefault(line_key, {})
                if o_line:
                    # merge the line with an existing line
                    o_line['product_qty'] += order_line.product_qty * order_line.product_uom.factor / o_line['uom_factor']
                else:
                    # append a new "standalone" line
                    for field in ('product_qty', 'product_uom'):
                        field_val = getattr(order_line, field)
                        if isinstance(field_val, browse_record):
                            field_val = field_val.id
                        o_line[field] = field_val
                    o_line['uom_factor'] = order_line.product_uom and order_line.product_uom.factor or 1.0



        allorders = []
        orders_info = {}
        for order_key, (order_data, old_ids) in new_orders.iteritems():
            # skip merges with only one order
            if len(old_ids) < 2:
                allorders += (old_ids or [])
                continue

            # cleanup order line data
            for key, value in order_data['order_line'].iteritems():
                del value['uom_factor']
                value.update(dict(key))
            order_data['order_line'] = [(0, 0, value) for value in order_data['order_line'].itervalues()]

            # create the new order
            neworder_id = self.create(cr, uid, order_data)
            orders_info.update({neworder_id: old_ids})
            allorders.append(neworder_id)

            # make triggers pointing to the old orders point to the new order
            for old_id in old_ids:
                wf_service.trg_redirect(uid, 'purchase.order', old_id, neworder_id, cr)
                wf_service.trg_validate(uid, 'purchase.order', old_id, 'purchase_cancel', cr)
        return orders_info
    #empty the purchase_order_detail.procurement_id when do cancel    
    def action_cancel(self, cr, uid, ids, context=None):
        val = super(purchase_order,self).action_cancel(cr, uid, ids, context)
        if val:
            cr.execute("""update purchase_order_line set procurement_id = null
                    where order_id in %s""",(tuple(ids),))
        return val


class purchase_order_group(osv.osv_memory):
    _inherit = "purchase.order.group"
    def merge_orders(self, cr, uid, ids, context=None):
        """
             To merge similar type of purchase orders.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs
             @param context: A standard dictionary

             @return: purchase order view

        """
        order_obj = self.pool.get('purchase.order')
        proc_obj = self.pool.get('procurement.order')
        mod_obj =self.pool.get('ir.model.data')
        if context is None:
            context = {}
        result = mod_obj._get_id(cr, uid, 'purchase', 'view_purchase_order_filter')
        id = mod_obj.read(cr, uid, result, ['res_id'])

        allorders = order_obj.do_merge(cr, uid, context.get('active_ids',[]), context)
        for new_order in allorders:
            proc_ids = proc_obj.search(cr, uid, [('purchase_id', 'in', allorders[new_order])], context=context)
            for proc in proc_obj.browse(cr, uid, proc_ids, context=context):
                if proc.purchase_id:
                    proc_obj.write(cr, uid, [proc.id], {'purchase_id': new_order}, context)
        
            cr.execute("""update purchase_order_line set procurement_id = null
                    where order_id in %s""",(tuple(allorders[new_order]),))

        return {
            'domain': "[('id','in', [" + ','.join(map(str, allorders.keys())) + "])]",
            'name': _('Purchase Orders'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'search_view_id': id['res_id']
        }    
    
class purchase_order_line(osv.osv):  
    _inherit = "purchase.order.line"
    _columns = {'procurement_id': fields.many2one('procurement.order', 'Procurement'),
                'so_name':fields.related('procurement_id','origin',type='char',string='SO#'),
                'so_line_id':fields.related('procurement_id','so_ids',type='one2many',relation='sale.order.line',string='Sale Order Line'),
                }  
    def copy_data(self, cr, uid, id, default=None, context=None):
        res = super(purchase_order_line,self).copy_data(cr,uid,id,default,context)
        if(res['procurement_id']): res.pop('procurement_id')
        return res
class sale_order_line(osv.osv):  
    _inherit = "sale.order.line"
    _columns = {'procurement_id': fields.many2one('procurement.order', 'Procurement'),
                'po_name':fields.related('procurement_id','purchase_id',type='many2one',relation='purchase.order',string='PO#'),
                'po_line_id':fields.related('procurement_id','po_ids',type='one2many',relation='purchase.order.line',domain=[('state','=','cancel')],string='Purchase Order Line'),
                } 
    def copy_data(self, cr, uid, id, default=None, context=None):
        res = super(sale_order_line,self).copy_data(cr,uid,id,default,context)
        if(res['procurement_id']): res.pop('procurement_id')
        return res                   
class procurement_order(osv.osv):  
    _inherit = "procurement.order"
    _columns = {'so_ids': fields.one2many('sale.order.line', 'procurement_id','POLine'),
                'po_ids': fields.one2many('purchase.order.line', 'procurement_id','POLine'),
                }    
    def write(self, cr, user, ids, vals, context=None):
        resu = super(procurement_order,self).write(cr, user, ids, vals, context);
        return resu
             
    def make_po(self, cr, uid, ids, context=None):
        """ Make purchase order from procurement
        inherited from purchase.py.procurement_order.make_po()
        add the logic to add new line to old PO when there are POs with same partner/locaion/pricelist
        By johnw@DMEMS
        @return: New created Purchase Orders procurement wise
        """
        def get_new_origin(old_origin, so_name):
            if not so_name or old_origin.find(so_name) >= 0: return False
            return old_origin + ' '+ so_name
        def get_new_date_order(old_date_order, new_date_order):
            if old_date_order <= new_date_order : return False
            return new_date_order.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    
        res = {}
        if context is None:
            context = {}
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        partner_obj = self.pool.get('res.partner')
        uom_obj = self.pool.get('product.uom')
        pricelist_obj = self.pool.get('product.pricelist')
        prod_obj = self.pool.get('product.product')
        acc_pos_obj = self.pool.get('account.fiscal.position')
        seq_obj = self.pool.get('ir.sequence')
        warehouse_obj = self.pool.get('stock.warehouse')
        po_obj = self.pool.get('purchase.order')
        po_line_obj = self.pool.get('purchase.order.line')
        upt_po_id = ''
        for procurement in self.browse(cr, uid, ids, context=context):
            res_id = procurement.move_id.id
            partner = procurement.product_id.seller_id # Taken Main Supplier of Product of Procurement.
            seller_qty = procurement.product_id.seller_qty
            partner_id = partner.id
            address_id = partner_obj.address_get(cr, uid, [partner_id], ['delivery'])['delivery']
            pricelist_id = partner.property_product_pricelist_purchase.id
            warehouse_id = warehouse_obj.search(cr, uid, [('company_id', '=', procurement.company_id.id or company.id)], context=context)
            uom_id = procurement.product_id.uom_po_id.id

            qty = uom_obj._compute_qty(cr, uid, procurement.product_uom.id, procurement.product_qty, uom_id)
            if seller_qty:
                qty = max(qty,seller_qty)

            price = pricelist_obj.price_get(cr, uid, [pricelist_id], procurement.product_id.id, qty, partner_id, {'uom': uom_id})[pricelist_id]

            schedule_date = self._get_purchase_schedule_date(cr, uid, procurement, company, context=context)
            purchase_date = self._get_purchase_order_date(cr, uid, procurement, company, schedule_date, context=context)

            #Passing partner_id to context for purchase order line integrity of Line name
            new_context = context.copy()
            new_context.update({'lang': partner.lang, 'partner_id': partner_id})

            product = prod_obj.browse(cr, uid, procurement.product_id.id, context=new_context)
            taxes_ids = procurement.product_id.supplier_taxes_id
            taxes = acc_pos_obj.map_tax(cr, uid, partner.property_account_position, taxes_ids)

            name = product.partner_ref
            if product.description_purchase:
                name += '\n'+ product.description_purchase
                
            line_vals = {
                'name': name,
                'product_qty': qty,
                'product_id': procurement.product_id.id,
                'product_uom': uom_id,
                'price_unit': price or 0.0,
                'date_planned': schedule_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'move_dest_id': res_id,
                'taxes_id': [(6,0,taxes)],
                'procurement_id':procurement.id,
            }

            po_vals={
                'partner_id': partner_id,
                'location_id': procurement.location_id.id,
                'pricelist_id': pricelist_id,}       
            
            #find the old pos with active workflow instance, johnw@20130930
            cr.execute("select max(a.id) \
                        from purchase_order a \
                        join wkf_instance b on a.id = b.res_id and b.res_type = 'purchase.order' and b.state = 'active' \
                        where a.state = 'draft' \
                        and a.partner_id = %s \
                        and a.location_id = %s \
                        and a.pricelist_id = %s",
                        (po_vals.get('partner_id'),po_vals.get('location_id'),po_vals.get('pricelist_id')))
            old_po_id = 0
            po_ids = cr.fetchone();
            if po_ids and len(po_ids) > 0:
                old_po_id = po_ids[0]
            if old_po_id > 0:
                old_po = po_obj.browse(cr,uid,old_po_id)
                origin = get_new_origin(old_po.origin, procurement.origin)
                if origin: po_vals.update({'origin':origin})
                date_order = get_new_date_order(datetime.date(datetime.strptime(old_po.date_order,DEFAULT_SERVER_DATE_FORMAT)), datetime.date(purchase_date))
                if date_order: po_vals.update({'date_order':date_order})
                #update the old PO
                po_obj.write(cr, uid, old_po_id, po_vals, context=new_context)
                #create new PO line
                line_vals.update({'order_id':old_po_id})
                po_line_obj.create(cr, uid, line_vals, context=new_context)
                res[procurement.id] =  old_po_id                                
            else:
                #create new PO and PO line
                name = seq_obj.get(cr, uid, 'purchase.order') or _('PO: %s') % procurement.name
                po_vals.update({
                    'name': name,
                    'origin': procurement.origin,
                    'warehouse_id': warehouse_id and warehouse_id[0] or False,
                    'date_order': purchase_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'company_id': procurement.company_id.id,
                    'fiscal_position': partner.property_account_position and partner.property_account_position.id or False,
                    'payment_term_id': partner.property_supplier_payment_term.id or False,
                    })
                res[procurement.id] = self.create_procurement_purchase_order(cr, uid, procurement, po_vals, line_vals, context=new_context)
            self.write(cr, uid, [procurement.id], {'state': 'running', 'purchase_id': res[procurement.id]})
        self.message_post(cr, uid, ids, body=_("Draft Purchase Order created"), context=context)
        return res  
