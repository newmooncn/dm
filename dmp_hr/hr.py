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

class hr_employee(osv.osv):
	_inherit = "hr.employee"
	_order='emp_code'
	_columns = {
		'employment_start':fields.date('Employment Started'),
        'employment_resigned':fields.date('Employment Resigned'),
		'employment_finish':fields.date('Employment Finished'),
        'multi_images': fields.text("Multi Images"),
        'room_no': fields.char("Room#",size=16),
        'bunk_no': fields.char('Bunk#',size=16),
        'emergency_contacter': fields.char("Emergency Contacter",size=32),
        'emergency_phone': fields.char("Emergency Phone",size=32),
        
        'known_allergies': fields.text("Known Allergies"),
        'recruit_source_id': fields.many2one('hr.recruitment.source', 'Recruitment Source'),
        'degree_id': fields.many2one('hr.recruitment.degree', 'Degree'),
        'computer_id': fields.char('Computer ID',size=128),
	}
	
hr_employee()
	