# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP S.A. <http://www.openerp.com>
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

import re
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.addons.dm_base.utils import deal_args_dt
import openerp.addons.decimal_precision as dp

class product_product(osv.osv):
	_inherit = "product.product"
	
	def button_approve(self, cr, uid, ids, context=None):
		#state will be changed to 'sellable', purchase_ok=1, sale_ok=1, active=1
		self.write(cr,uid,ids,{'state':'sellable','purchase_ok':1,'sale_ok':1,'active':1},context=context)
	def button_eol(self, cr, uid, ids, context=None):
		#state will be changed to 'end', purchase_ok=0, sale_ok=0
		self.write(cr,uid,ids,{'state':'end','purchase_ok':0,'sale_ok':0},context=context)
	def button_obsolete(self, cr, uid, ids, context=None):
		#state will be changed to 'obsolete', purchase_ok=0, sale_ok=0, active=0
		self.write(cr,uid,ids,{'state':'obsolete','purchase_ok':0,'sale_ok':0,'active':0},context=context)
	def button_draft(self, cr, uid, ids, context=None):
		#state will be changed to 'draft', purchase_ok=0, sale_ok=0, active=1
		self.write(cr,uid,ids,{'state':'draft','purchase_ok':0,'sale_ok':0,'active':1},context=context)
				
product_product()

class product_template(osv.osv):
	_inherit = "product.template"

	_columns = {
		#add track_visibility
		'state': fields.selection([('draft', 'In Development'),
			('sellable','Normal'),
			('end','End of Lifecycle'),
			('obsolete','Obsolete')], 'Status', track_visibility='onchange'),
        }

	_defaults = {
		'state':'draft',
		'purchase_ok':False,
		'sale_ok':False,
    }