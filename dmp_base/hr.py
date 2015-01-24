# -*- encoding: utf-8 -*-
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

from openerp.osv import fields, osv

import logging

_logger = logging.getLogger(__name__)

class hr_department(osv.osv):
	_description = "Department"
	_inherit = 'hr.department'
	_order = 'sequence,id'
	_columns = {
		#with the sequence field, then on the kanban view by department, user can change the sequence of departments.
        'sequence': fields.integer('Sequence'),
    }

class hr_employee(osv.osv):
	_inherit = "hr.employee"
	_order='emp_code'

	_columns = {'emp_code': fields.char('Employee Code', size=16),
			'emp_card_id': fields.char('Employee Card ID', size=16),
	}
	_sql_constraints = [
		('emp_code_uniq', 'unique(emp_code)', 'Employee Code must be unique!'),
	]	
	def default_get(self, cr, uid, fields_list, context=None):
		values = super(hr_employee,self).default_get(cr, uid, fields_list, context)
		cr.execute("SELECT max(id) from hr_employee")
		emp_id = cr.fetchone()
		emp_code = '%03d'%(emp_id[0] + 1,)
		values.update({'emp_code':emp_code})
		return values

	#add the emp_code return in the name
	def name_get(self, cr, user, ids, context=None):
		if context is None:
			context = {}
		if isinstance(ids, (int, long)):
			ids = [ids]
		if not len(ids):
			return []
		result = []
		for data in self.browse(cr, user, ids, context=context):
			if data.id <= 0:
				result.append((data.id,''))
				continue
			result.append((data.id,'[%s]%s'%(data.emp_code or '',data.name)))
						  
		return result
	#add the emp_code search in the searching
	def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		if name:
			ids = self.search(cr, user, [('emp_code','=',name)]+ args, limit=limit, context=context)
			if not ids:
				ids = self.search(cr, user, [('name','=',name)]+ args, limit=limit, context=context)
			if not ids:
				ids = set()
				ids.update(self.search(cr, user, args + [('emp_code',operator,name)], limit=limit, context=context))
				if not limit or len(ids) < limit:
					# we may underrun the limit because of dupes in the results, that's fine
					ids.update(self.search(cr, user, args + [('name',operator,name)], limit=(limit and (limit-len(ids)) or False) , context=context))
				ids = list(ids)
		else:
			ids = self.search(cr, user, args, limit=limit, context=context)
		result = self.name_get(cr, user, ids, context=context)
		return result 	
	
	def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
		for arg in args:
			#add the category improving
			if arg[0] == 'department_id' and arg[1] == '=' and isinstance(arg[2], (int,long)):
				idx = args.index(arg)
				args.remove(arg)
				args.insert(idx, [arg[0],'child_of',arg[2]])
							
		#get the search result		
		ids = super(hr_employee,self).search(cr, user, args, offset, limit, order, context, count)
		return ids	
	
	#update user related employee_id
	def update_user_emp(self, cr, uid, user_id, emp_id, context=None):
		if user_id and emp_id:
			#use sql to update, avoie the dead looping calling with res_user.update_emp_user()
			cr.execute('update res_users set employee_id = %s where id = %s',(emp_id, user_id))
	def write(self, cr, uid, ids, vals, context=None):
		resu = super(hr_employee, self).write(cr, uid, ids, vals, context=context)
		if 	'user_id' in vals:
			self.update_user_emp(cr, uid, vals['user_id'], ids[0], context)
		return resu
	def create(self, cr, uid, vals, context=None):
		new_id = super(hr_employee, self).create(cr, uid, vals, context=context)
		if 	'user_id' in vals:
			self.update_user_emp(cr, uid, vals['user_id'], new_id, context)
		return new_id	
	
hr_employee()

'''
Add 'employee_id' to res_users, to manage the rules convention
--update by the employee's user setting
update res_users c
set employee_id = a.id
from hr_employee a,
resource_resource b 
where a.resource_id = b.id
and b.user_id = c.id

--Record rule on hr.holiday using the employee_id
[('employee_id','child_of', [user.employee_id.id])]
and below is also working
[('employee_id','in', user.employee_id and [emp.id for emp in user.employee_id.child_ids] or [])]

'''
class res_users(osv.osv):
	_name = 'res.users'
	_inherit = 'res.users'
	def _get_emp_image(self, cr, uid, ids, names, args, context=None):
		result = dict.fromkeys(ids,{'img_emp':False, 'img_emp_medium':False, 'img_emp_small':False})
		#get the images from employee
		for user in self.browse(cr, uid, ids, context=context):
#			if user.employee_ids:
#				result[user.id] = {'img_emp':user.employee_ids[0].image, 'img_emp_medium':user.employee_ids[0].image_medium, 'img_emp_small':user.employee_ids[0].image_small}
			if user.employee_id:
				result[user.id] = {'img_emp':user.employee_id.image, 
								'img_emp_medium':user.employee_id.image_medium, 
								'img_emp_small':user.employee_id.image_small}
		return result
	_columns = {
		'img_emp': fields.function(_get_emp_image, string="Image", type="binary", multi="_get_image",),  
		'img_emp_medium': fields.function(_get_emp_image, string="Medium-sized image", type="binary", multi="_get_image",),  
		'img_emp_small': fields.function(_get_emp_image, string="Small-sized image", type="binary", multi="_get_image",),
		'employee_id': fields.many2one('hr.employee', 'Employee'),
	}			  
	def copy(self, cr, uid, id, default=None, context=None):
		default.update({'employee_ids':[], 'employee_id':None})
		return super(res_users,self).copy(cr, uid, id, default, context)
	
	#update employee related user_id
	def update_emp_user(self, cr, uid, user_id, emp_id, context=None):
		if user_id and emp_id:
			#use sql to update, avoie the dead looping calling with hr_employee.update_user_emp()
			resource_id = self.pool.get('hr.employee').browse(cr, uid, emp_id, context=context).resource_id.id
			cr.execute('update resource_resource set user_id = %s where id = %s',(user_id, resource_id))
	def write(self, cr, uid, ids, vals, context=None):
		resu = super(res_users, self).write(cr, uid, ids, vals, context=context)
		if 	'employee_id' in vals:
			self.update_emp_user(cr, uid, ids[0], vals['employee_id'], context)
		return resu
	def create(self, cr, uid, vals, context=None):
		new_id = super(res_users, self).create(cr, uid, vals, context=context)
		if 	'employee_id' in vals:
			self.update_emp_user(cr, uid, new_id, vals['employee_id'], context)
		return new_id		