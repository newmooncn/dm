# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
from dateutil.relativedelta import relativedelta
import time
import datetime
from openerp import netsvc
from openerp.osv import fields,osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT          
class stock_move(osv.osv):
    _inherit = "stock.move" 
    _columns = {
        'create_uid': fields.many2one('res.users', 'Creator',readonly=True),        
        #make the price's decimal precision as the 'Product Price'
        'price_unit': fields.float('Unit Price', digits_compute= dp.get_precision('Product Price'), help="Technical field used to record the product cost set by the user during a picking confirmation (when average price costing method is used)"),
        'product_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product Price'),
            required=True,states={'done': [('readonly', True)]},
            help="This is the quantity of products from an inventory "
                "point of view. For moves in the state 'done', this is the "
                "quantity of products that were actually moved. For other "
                "moves, this is the quantity of product that is planned to "
                "be moved. Lowering this quantity does not generate a "
                "backorder. Changing this quantity on assigned moves affects "
                "the product reservation, and should be done with care."
        ),
    }

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        #deal the 'date' datetime field query
        new_args = deal_args(self,args)
        return super(stock_move,self).search(cr, user, new_args, offset, limit, order, context, count)  

    def action_done(self, cr, uid, ids, context=None):
        resu = super(stock_move,self).action_done(cr, uid, ids, context) 
        move_ids = []
        for move in self.browse(cr, uid, ids, context=context):
            if move.state == 'done':
                move_ids.append(move.id)     
        self.write(cr, uid, move_ids, {'date': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}, context=context)
        return resu

def _set_minimum_date(self, cr, uid, ids, name, value, arg, context=None):
    """ Calculates planned date if it is less than 'value'.
    @param name: Name of field
    @param value: Value of field
    @param arg: User defined argument
    @return: True or False
    """
    if not value:
        return False
    if isinstance(ids, (int, long)):
        ids = [ids]
    for pick in self.browse(cr, uid, ids, context=context):
        sql_str = """update stock_move set
                date_expected='%s'
            where
                picking_id=%s """ % (value, pick.id)
        if pick.min_date:
            sql_str += " and (date_expected='" + pick.min_date + "' or date_expected<'" + value + "')"
        cr.execute(sql_str)
    return True

def _set_maximum_date(self, cr, uid, ids, name, value, arg, context=None):
    """ Calculates planned date if it is greater than 'value'.
    @param name: Name of field
    @param value: Value of field
    @param arg: User defined argument
    @return: True or False
    """
    if not value:
        return False
    if isinstance(ids, (int, long)):
        ids = [ids]
    for pick in self.browse(cr, uid, ids, context=context):
        sql_str = """update stock_move set
                date_expected='%s'
            where
                picking_id=%d """ % (value, pick.id)
        if pick.max_date:
            sql_str += " and (date_expected='" + pick.max_date + "' or date_expected>'" + value + "')"
        cr.execute(sql_str)
    return True   

from openerp.addons.stock.stock import stock_picking as stock_picking_super     
     
class stock_picking(osv.osv):
    _inherit = "stock.picking" 
    _order = 'name desc'  
        
    _columns = {   
        'create_uid': fields.many2one('res.users', 'Creator',readonly=True),
        'create_date': fields.datetime('Creation Date', readonly=True, select=True), 
    }      
    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        #deal the 'date' datetime field query
        new_args = deal_args(self,args)
        return super(stock_picking,self).search(cr, user, new_args, offset, limit, order, context, count)

    def action_done(self, cr, uid, ids, context=None):
        """Changes picking state to done.
        
        This method is called at the end of the workflow by the activity "done".
        @return: True
        """
        resu = super(stock_picking,self).action_done(cr,uid,ids,context)
        #fix the time issue to use utc now, by johnw
        self.write(cr, uid, ids, {'date_done': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')})
        return resu

    def action_confirm(self, cr, uid, ids, context=None):
        """ Add the lines assignment checking
        """
        resu = super(stock_picking,self).action_confirm(cr, uid, ids, context=context)
        if resu:
            pickings = self.browse(cr, uid, ids, context=context)
            todo = []
            for picking in pickings:
#                if picking.type in('mr','mrr'):
                for r in picking.move_lines:
                    if r.state == 'confirmed':
                        todo.append(r.id)
            if len(todo):
                self.pool.get('stock.move').check_assign(cr, uid, todo, context=context)
        return resu
    
class stock_picking_out(osv.osv):
    _inherit = "stock.picking.out"  
    _order = 'name desc'   
    _columns = {
        'create_uid': fields.many2one('res.users', 'Creator',readonly=True),
        'create_date': fields.datetime('Creation Date', readonly=True, select=True),
        'min_date': fields.function(stock_picking_super.get_min_max_date, fnct_inv=_set_minimum_date, multi="min_max_date",
                 store=True, type='datetime', string='Scheduled Time', select=1, help="Scheduled time for the shipment to be processed"), 
        'max_date': fields.function(stock_picking_super.get_min_max_date, fnct_inv=_set_maximum_date, multi="min_max_date",
                 store=True, type='datetime', string='Max. Expected Date', select=2),
        'message_ids': fields.one2many('mail.message', 'res_id',
            domain=lambda self: [('model', '=', 'stock.picking')],
            auto_join=True,
            string='Messages',
            help="Messages and communication history"), 
    }
    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        #deal the 'date' datetime field query
        new_args = deal_args(self,args)
        return super(stock_picking_out,self).search(cr, user, new_args, offset, limit, order, context, count)            
            
class stock_picking_in(osv.osv):
    _inherit = "stock.picking.in"
    _order = 'name desc'  
    _columns = {
        'create_uid': fields.many2one('res.users', 'Creator',readonly=True),
        'create_date': fields.datetime('Creation Date', readonly=True, select=True),
        'min_date': fields.function(stock_picking_super.get_min_max_date, fnct_inv=_set_minimum_date, multi="min_max_date",
                 store=True, type='datetime', string='Scheduled Time', select=1, help="Scheduled time for the shipment to be processed"), 
        'max_date': fields.function(stock_picking_super.get_min_max_date, fnct_inv=_set_maximum_date, multi="min_max_date",
                 store=True, type='datetime', string='Max. Expected Date', select=2),
        'message_ids': fields.one2many('mail.message', 'res_id',
            domain=lambda self: [('model', '=', 'stock.picking')],
            auto_join=True,
            string='Messages',
            help="Messages and communication history"),                
    }     
    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        #deal the 'date' datetime field query
        new_args = deal_args(self,args)
        return super(stock_picking_in,self).search(cr, user, new_args, offset, limit, order, context, count)  
      
def deal_args(obj,args):  
    new_args = []
    for arg in args:
        fld_name = arg[0]
        if fld_name in ('date', 'date_done'):
            fld_operator = arg[1]
            fld_val = arg[2]
            fld = obj._columns.get(fld_name)
            #['date','=','2013-12-12 16:00:00'] the '16' was generated for the timezone
            if fld._type == 'datetime' and fld_operator == "=" and fld_val.endswith('00:00'):
                time_start = [fld_name,'>=',fld_val]
                time_obj = datetime.datetime.strptime(fld_val,DEFAULT_SERVER_DATETIME_FORMAT)
                time_obj += relativedelta(days=1)
                time_end = [fld_name,'<=',time_obj.strftime(DEFAULT_SERVER_DATETIME_FORMAT)]
                new_args.append(time_start)
                new_args.append(time_end)
            else:
                new_args.append(arg)
        else:
            new_args.append(arg)    
    return new_args