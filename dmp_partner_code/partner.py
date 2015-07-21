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
from openerp.addons.base.res import res_partner as res_partner_base

class res_partner(osv.Model):
    _inherit = 'res.partner'
    _columns = {
        'ref': fields.char('Reference', select=1)
    }
    #update res_partner set code = trim(to_char(id,'00009'))
    _defaults = {
        'ref': '/',
    }    
    def _check_write_vals(self,cr,uid,vals,ids=None,context=None):
        if vals.get('ref') and vals['ref']:
            vals['ref'] = vals['ref'].strip()
            if ids:
                partner_id = self.search(cr, uid, [('ref', '=', vals['ref']),('id','not in',ids)])
            else:
                partner_id = self.search(cr, uid, [('ref', '=', vals['ref'])])
            if partner_id:
                raise osv.except_osv(_('Error!'), _('Partner code must be unique!'))
        return True    
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if vals.get('ref','/')=='/':
            vals['ref'] = self.pool.get('ir.sequence').get(cr, uid, 'partner') or '/'
        self._check_write_vals(cr,uid,vals,context=context)
        new_id = super(res_partner, self).create(cr, uid, vals, context)
        return new_id
    
    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        self._check_write_vals(cr,uid,vals,ids=ids,context=context)
        resu = super(res_partner, self).write(cr, uid, ids, vals, context=context)
        return resu
    
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = record.name
            if record.parent_id and not record.is_company:
                name = "%s, %s" % (record.parent_name, name)
            if context.get('show_address_only'):
                name = self._display_address(cr, uid, record, without_company=True, context=context)
            if context.get('show_address'):
                name = name + "\n" + self._display_address(cr, uid, record, without_company=True, context=context)
            name = name.replace('\n\n','\n')
            name = name.replace('\n\n','\n')
            if context.get('show_email') and record.email:
                name = "%s <%s>" % (name, record.email)
            #johnw, add ref
            if record.ref:
                name = "[%s]%s" % (record.ref,name)
            res.append((record.id, name))
        return res    

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):

            self.check_access_rights(cr, uid, 'read')
            where_query = self._where_calc(cr, uid, args, context=context)
            self._apply_ir_rules(cr, uid, where_query, 'read', context=context)
            from_clause, where_clause, where_clause_params = where_query.get_sql()
            where_str = where_clause and (" WHERE %s AND " % where_clause) or ' WHERE '

            # search on the name of the contacts and of its company
            search_name = name
            if operator in ('ilike', 'like'):
                search_name = '%%%s%%' % name
            if operator in ('=ilike', '=like'):
                operator = operator[1:]

            unaccent = res_partner_base.get_unaccent_wrapper(cr)
            '''
            query = """SELECT id
                         FROM res_partner
                      {where} ({email} {operator} {percent}
                           OR {display_name} {operator} {percent})
                     ORDER BY {display_name}
                    """.format(where=where_str, operator=operator,
                               email=unaccent('email'),
                               display_name=unaccent('display_name'),
                               percent=unaccent('%s'))
            '''
            #johnw, 01/27/2015, add column 'ref'/'name' searching
            query = """SELECT id
                         FROM res_partner
                      {where} ({email} {operator} {percent}
                           OR {display_name} {operator} {percent}
                           OR {ref} {operator} {percent}
                           OR {name} {operator} {percent})
                     ORDER BY {display_name}
                    """.format(where=where_str, operator=operator,
                               email=unaccent('email'),
                               display_name=unaccent('display_name'),
                               ref=unaccent('ref'),
                               name=unaccent('name'),
                               percent=unaccent('%s'))
                    
            where_clause_params += [search_name, search_name, search_name, search_name]
            if limit:
                query += ' limit %s'
                where_clause_params.append(limit)
            cr.execute(query, where_clause_params)
            ids = map(lambda x: x[0], cr.fetchall())

            if ids:
                return self.name_get(cr, uid, ids, context)
            else:
                return []
        return super(res_partner,self).name_search(cr, uid, name, args, operator=operator, context=context, limit=limit)
        
res_partner()

class res_partner_name(osv.Model):
    _inherit = 'res.partner'
    _order = 'display_name'

    def _display_name_compute(self, cr, uid, ids, name, args, context=None):
        context = dict(context or {})
        context.pop('show_address', None)
        context.pop('show_address_only', None)
        context.pop('show_email', None)
        return dict(self.name_get(cr, uid, ids, context=context))

    _display_name_store_triggers = {
        'res.partner': (lambda self,cr,uid,ids,context=None: self.search(cr, uid, [('id','child_of',ids)], context=dict(active_test=False)),
                        ['parent_id', 'is_company', 'name', 'ref'], 10)
    }

    _display_name = lambda self, *args, **kwargs: self._display_name_compute(*args, **kwargs)

    _columns = {
        'display_name': fields.function(_display_name, type='char', string='Name', store=_display_name_store_triggers, select=True),
    }