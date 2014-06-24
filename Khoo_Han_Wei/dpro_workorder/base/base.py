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
import re


class base_sla(osv.Model):
    _name = 'base.sla'
    _description = 'Service Level Agreement'
    _columns = {
        'name': fields.char('Name', size=128),
        'active': fields.boolean('Active'),
        'description': fields.text('Description'),
        'due_date_opt': fields.selection([('no_due', 'No Due Date/Time Set'),
                                          ('due_hour', 'Due In'),
                                          ('due_time', 'Due Next Day At'),
                                          ('due_day_time', 'Due In Day/Time')], string='Due Date Options'),
        'due_hour': fields.char('Hours', size=5),
        'due_day': fields.integer('Day(s)'),
    }
    _defaults = {
        'active': True,
        'due_date_opt': 'no_due',
        'due_hour': '00:00',
    }

    def onchange_hour(self, cr, uid, ids, due_hour, context=None):
        result = {'value': {'due_hour': False}}
        if not due_hour:
            return result
        match = re.search('\d\d\:\d\d', due_hour)
        if not match:
            warning = {
               'title': _('Input Error!'),
               'message' : _('Please enter hour in HH:MM format')
            }
            result.update({'warning': warning})
        else:
            result['value']['due_hour'] = due_hour
        return result

base_sla()


class work_request_code(osv.Model):
    _name = 'work.request.code'
    _columns = {
        'name': fields.char('Name', size=256),
        'code': fields.char('Code', size=128),
    }
work_request_code()


class base_problem_code(osv.Model):
    _name = 'base.problem.code'
    _columns = {
        'name': fields.char('Name', size=128),
        'code': fields.char('Code', size=128),
    }
base_problem_code()


class base_action_code(osv.Model):
    _name = 'base.action.code'
    _columns = {
        'name': fields.char('Name', size=128),
        'code': fields.char('Code', size=128),
    }
base_action_code()


class base_warranty(osv.Model):
    _name = 'base.warranty'
    _columns = {
        'warranty_id': fields.char('Warranty ID', size=128),
        'name': fields.char('Name', size=128),
        'warranty_start': fields.date('Warranty Start'),
        'warranty_period': fields.integer('Warranty Period (Months)'),
    }

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        vals['warranty_id'] = self.pool.get('ir.sequence').get(cr, uid, 'base.warranty') or '/'
        return super(base_warranty, self).create(cr, uid, vals, context=context)

base_warranty()


class workorder_part_replace(osv.Model):
    _name = 'workorder.part.replace'
    _columns = {
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'name': fields.char('Description', size=128),
        'quantity': fields.integer('Quantity'),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure ',),
        'serial_id': fields.many2one('stock.production.lot', 'Serial No'),
        'workorder_id': fields.many2one('sale.order', 'Work Order'),
    }
    def onchange_product_id(self, cr, uid, ids,  product_id, context=None):
        context = context or {}
        if not product_id:
            return {'value': {'product_uom': None,}}
        product_obj = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
        return {'value': {'product_uom': product_obj.uom_id.id,}}
    
workorder_part_replace()


class base_inspection_type(osv.Model):
    _name = 'base.inspection.type'
    _columns = {
        'name': fields.char('Name', size=128),
        'code': fields.char('Code', size=128),
    }
base_inspection_type()


class workorder_quality_control(osv.Model):
    _name = 'workorder.quality.control'
    _columns = {
        'inspect_type_id': fields.many2one('base.inspection.type', 'Inspection Type'),
        'remark': fields.text('Remarks'),
        'workorder_id': fields.many2one('sale.order', 'Work Order'),
    }
workorder_quality_control()
