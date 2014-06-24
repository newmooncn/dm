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
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _


class project_task(osv.Model):
    _inherit = 'project.task'
    _columns = {
        'sale_id': fields.many2one('sale.order', 'Sale'),
    }

    def open_map(self, cr, uid, ids, context=None):
        task = self.browse(cr, uid, ids[0], context=context)
        url="http://maps.google.com/maps?oi=map&q="
        if task.partner_id:
            partner = task.partner_id
            if partner.street:
                url += partner.street.replace(' ','+')
            if partner.city:
                url += '+' + partner.city.replace(' ','+')
            if partner.state_id:
                url += '+' + partner.state_id.name.replace(' ','+')
            if partner.country_id:
                url += '+' + partner.country_id.name.replace(' ','+')
            if partner.zip:
                url += '+' + partner.zip.replace(' ','+')
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'new',
            }
        return True

project_task()
