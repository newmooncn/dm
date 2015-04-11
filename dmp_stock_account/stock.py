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
          
class stock_picking(osv.osv):
    _inherit = "stock.picking" 
    _columns = {   
        'account_move_ids': fields.one2many('account.move', 'picking_id',string = 'Stock Accout Move', readonly=False),
    } 
    
class stock_picking_out(osv.osv):
    _inherit = "stock.picking.out"   
    _columns = {   
        'account_move_ids': fields.one2many('account.move', 'picking_id',string = 'Stock Accout Move', readonly=False),
    }
            
class stock_picking_in(osv.osv):
    _inherit = "stock.picking.in"
    _columns = {   
        #fields added to stock_picking_in/out also need add to stock_picking, since the read() method to the 2 classes are using stock_picking class, see addons/stock/stock.py.stock_picking_in
        'account_move_ids': fields.one2many('account.move', 'picking_id',string = 'Stock Accout Move', readonly=False),
    }
