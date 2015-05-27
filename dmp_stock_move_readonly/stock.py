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
from openerp.osv import fields,osv
     
class stock_picking(osv.osv):
    _inherit = "stock.move"
    def _have_order(self, cr, uid, ids, field_names, args, context=None):
        res = {}
        for move in self.browse(cr, uid, ids ,context=context):
            res[move.id] = False
            if move.picking_id and (move.picking_id.purchase_id or move.picking_id.sale_id or move.picking_id.production_id):
                res[move.id] = True
        return res
    _columns = {   
        'have_order': fields.function(_have_order, type='boolean', string='Having Order',readonly=True),
    }