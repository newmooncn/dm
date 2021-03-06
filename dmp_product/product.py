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
		
	_columns = {
		'create_uid':  fields.many2one('res.users', 'Creator', readonly=True),
		'create_date': fields.datetime('Creation Date', readonly=True, select=True),
		#add 'select' to create index
		'default_code' : fields.char('Internal Reference', size=64, select=True, required=True),
		#Chinese name
		'cn_name': fields.char(string=u'Chinese Name', size=128, track_visibility='onchange'),
		#the external part#, for example from engineering
        'part_no_external': fields.char(string=u'External Part#', size=32, help="The external part#, may be from engineering, purchase..."),
        'material': fields.char(string=u'Material', size=32, help="The material of the product"),
	}
	_defaults = {
		'default_code': '/',
	}
	
	def _check_write_vals(self,cr,uid,vals,ids=None,context=None):
		if vals.get('default_code') and vals['default_code']:
			vals['default_code'] = vals['default_code'].strip()
			if ids:
				product_id = self.search(cr, uid, [('default_code', '=', vals['default_code']),('id','not in',ids)])
			else:
				product_id = self.search(cr, uid, [('default_code', '=', vals['default_code'])])
			if product_id:
				raise osv.except_osv(_('Error!'), _('Product code must be unique!'))
		if vals.get('cn_name'):
			vals['cn_name'] = vals['cn_name'].strip()
			if ids:
				product_id = self.search(cr, uid, [('cn_name', '=', vals['cn_name']),('id','not in',ids)])
			else:
				product_id = self.search(cr, uid, [('cn_name', '=', vals['cn_name'])])
			if product_id:
				raise osv.except_osv(_('Error!'), _('Product Chinese Name must be unique!'))
		if vals.get('name'):
			vals['name'] = vals['name'].strip()
			if ids:
				product_id = self.search(cr, uid, [('name', '=', vals['name']),('id','not in',ids)])
			else:
				product_id = self.search(cr, uid, [('name', '=', vals['name'])])
			if product_id:
				raise osv.except_osv(_('Error!'), _('Product Name must be unique!'))	
		return True
		
	
	def create(self, cr, uid, vals, context=None):
		if context is None:
			context = {}
		if vals.get('default_code','/')=='/':
			vals['default_code'] = self.pool.get('ir.sequence').get(cr, uid, 'product') or '/'
		self._check_write_vals(cr,uid,vals,context=context)
		new_id = super(product_product, self).create(cr, uid, vals, context)
		return new_id
	
	def write(self, cr, uid, ids, vals, context=None):
		if context is None:
			context = {}
		self._check_write_vals(cr,uid,vals,ids=ids,context=context)
		resu = super(product_product, self).write(cr, uid, ids, vals, context=context)
		return resu
	
	def gen_default_code(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		code = self.generate_seq(cr, uid)
		self.write(cr, uid, ids, {'default_code': code})
		return True
	
	#Add cn_name search
	def _name_search_domain(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
		name_domain = [('default_code',operator,name),('name',operator,name),('ean13',operator,name),\
					('cn_name',operator,name),('cn_name',operator,name)]
		return name_domain
		
	def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		if name:
			#get domain by name
			name_domain = self._name_search_domain(cr, user, name, args, operator, context, limit)
			#add '|' operator
			field_cnt = len(name_domain) 
			for i in range(1, field_cnt):
				idx = field_cnt-i-1
				name_domain.insert(idx, '|')
			domain_search = name_domain + args
			if name_domain:
				ids = self.search(cr, user, domain_search, limit=limit, context=context)
			if not ids:
				ptrn = re.compile('(\[(.*?)\])')
				res = ptrn.search(name)
				if res:
					ids = self.search(cr, user, [('default_code','=', res.group(2))] + args, limit=limit, context=context)
		else:
			ids = self.search(cr, user, args, limit=limit, context=context)
		result = self.name_get(cr, user, ids, context=context)
		return result
	
	#Add cn_name
	def name_get(self, cr, user, ids, context=None):
		if context is None:
			context = {}
		if isinstance(ids, (int, long)):
			ids = [ids]
		if not len(ids):
			return []
		def _name_get(d):
			name = d.get('name','')
			code = d.get('default_code',False)
			if code:
				name = '[%s] %s' % (code,name)
			cn_name = d.get('cn_name',False)
			if cn_name:
				name = '%s, %s' % (name,cn_name)
			if d.get('variants'):
				name = name + ' - %s' % (d['variants'],)
				
			return (d['id'], name)

		partner_id = context.get('partner_id', False)

		result = []
		for product in self.browse(cr, user, ids, context=context):
			if product.id <= 0:
				result.append((product.id,''))
				continue
			sellers = filter(lambda x: x.name.id == partner_id, product.seller_ids)
			if sellers:
				for s in sellers:
					mydict = {
							  'id': product.id,
							  'name': s.product_name or product.name,
							  'cn_name': product.cn_name,
							  'default_code': s.product_code or product.default_code,
							  'variants': product.variants
							  }
					result.append(_name_get(mydict))
			else:
				mydict = {
						  'id': product.id,
						  'name': product.name,
						  'cn_name': product.cn_name,
						  'default_code': product.default_code,
						  'variants': product.variants
						  }
				result.append(_name_get(mydict))
		return result	
		
	def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
		#deal the datetime field query
		new_args = deal_args_dt(cr, user, self, args, ['create_date','write_date'], context)
		for arg in new_args:
			#add the category improving, search all child categories
			if arg[0] == 'categ_id' and arg[1] == '=' and isinstance(arg[2], (int,long)):
				idx = new_args.index(arg)
				new_args.remove(arg)
				new_args.insert(idx, [arg[0],'child_of',arg[2]])

			#add the multi part# query, user can enter default_code like: %code1%,%code2%...%coden%
			if arg[0] == 'default_code' and arg[1] == 'in' and isinstance(arg[2], type(u' ')):
				part_nos = []
				for part_no in arg[2].split(','):
					part_nos.append(part_no.strip())
				idx = new_args.index(arg)
				new_args.remove(arg)
				new_args.insert(idx, [arg[0],arg[1],part_nos])
							
		#get the search result		
		ids = super(product_product,self).search(cr, user, new_args, offset, limit, order, context, count)

		return ids
	
	def copy(self, cr, uid, id, default=None, context=None):
		if not default:
			default = {}
		cn_name = self.read(cr,uid,id,['cn_name'])['cn_name']
		if cn_name:
			cn_name = '%s(%s)'%(cn_name,u'副本')
		default.update({
			'default_code':self.pool.get('ir.sequence').get(cr, uid, 'product') or '/',
			'cn_name':cn_name,
		})
		return super(product_product, self).copy(cr, uid, id, default, context)		
				
product_product()

class product_template(osv.osv):
	_inherit = "product.template"

	_columns = {
		#add track_visibility
        'name': fields.char('Name', size=128, required=True, translate=False, select=True, track_visibility='onchange'),    
		'list_price': fields.float('Sale Price', digits_compute=dp.get_precision('Product Price'), track_visibility='onchange', help="Base price to compute the customer price. Sometimes called the catalog price."),
		'standard_price': fields.float('Cost', digits_compute=dp.get_precision('Product Price'), track_visibility='onchange', help="Cost price of the product used for standard stock valuation in accounting and used as a base price on purchase orders.", groups="base.group_user"),
		
		#Change the procure_method/supply_method to property field
		'procure_method': fields.property(False, type='selection', view_load=True, string="Procurement Method", required=True, 
			selection = [('make_to_stock','Make to Stock'),('make_to_order','Make to Order')],
			help="Make to Stock: When needed, the product is taken from the stock or we wait for replenishment. \nMake to Order: When needed, the product is purchased or produced.", 
			),
		'supply_method': fields.property(False, type='selection', view_load=True, string="Supply Method", required=True, 
			selection = [('produce','Manufacture'),('buy','Buy')],
			help="Manufacture: When procuring the product, a manufacturing order or a task will be generated, depending on the product type. \nBuy: When procuring the product, a purchase order will be generated.", 
			),								     
        }

	_defaults = {
        'type' : 'product',
    }