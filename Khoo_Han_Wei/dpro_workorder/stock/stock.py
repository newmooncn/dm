# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
from openerp.osv import fields, osv
import time
from openerp.tools.translate import _


class prod_lot_modification(osv.osv):
    _name = 'prod.lot.modification'
    _columns = {
        'name': fields.char('Name', size=256),
        'date': fields.date('Date'),
        'user_id': fields.many2one('res.users', 'Author'),
        'lot_id': fields.many2one('stock.production.lot', 'Serial No'),
    }
prod_lot_modification()


class stock_production_lot(osv.osv):
    _inherit = 'stock.production.lot'
    _columns = {
        'warranty_id': fields.many2one('base.warranty', 'Warranty ID'),
        'modify_ids': fields.one2many('prod.lot.modification', 'lot_id', 'Modification'),
    }
stock_production_lot()
