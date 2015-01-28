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


class res_partner(osv.Model):
    _inherit = 'res.partner'
    _columns = {
        'code': fields.char('Code', size=16),
    }
    _defaults = {
        'code': '/',
    }    
    def _check_write_vals(self,cr,uid,vals,ids=None,context=None):
        if vals.get('code') and vals['code']:
            vals['code'] = vals['code'].strip()
            if ids:
                partner_id = self.search(cr, uid, [('code', '=', vals['code']),('id','not in',ids)])
            else:
                partner_id = self.search(cr, uid, [('code', '=', vals['code'])])
            if partner_id:
                raise osv.except_osv(_('Error!'), _('Partner code must be unique!'))
        return True    
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if vals.get('code','/')=='/':
            vals['code'] = self.pool.get('ir.sequence').get(cr, uid, 'partner') or '/'
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
            if context.get('show_address'):
                name = name + "\n" + self._display_address(cr, uid, record, without_company=True, context=context)
                name = name.replace('\n\n','\n')
                name = name.replace('\n\n','\n')
            if context.get('show_email') and record.email:
                name = "%s <%s>" % (name, record.email)
            if record.code:
                name = "[%s]%s" % (record.code, name)
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

            #unaccent = get_unaccent_wrapper(cr)
            unaccent = openerp.addons.base.res.res_partner.res_partner.get_unaccent_wrapper(cr)

            # TODO: simplify this in trunk with `display_name`, once it is stored
            # Perf note: a CTE expression (WITH ...) seems to have an even higher cost
            #            than this query with duplicated CASE expressions. The bulk of
            #            the cost is the ORDER BY, and it is inevitable if we want
            #            relevant results for the next step, otherwise we'd return
            #            a random selection of `limit` results.

            display_name = """CASE WHEN company.id IS NULL OR res_partner.is_company
                                   THEN {partner_name}
                                   ELSE {company_name} || ', ' || {partner_name}
                               END""".format(partner_name=unaccent('res_partner.name'),
                                             company_name=unaccent('company.name'))
            '''
            query = """SELECT res_partner.id
                         FROM res_partner
                    LEFT JOIN res_partner company
                           ON res_partner.parent_id = company.id
                      {where} ({email} {operator} {percent}
                           OR {display_name} {operator} {percent})
                     ORDER BY {display_name}
                    """.format(where=where_str, operator=operator,
                               email=unaccent('res_partner.email'),
                               percent=unaccent('%s'),
                               display_name=display_name)
            '''
            #johnw, 01/27/2015, add new column 'code' searching
            query = """SELECT res_partner.id
                         FROM res_partner
                    LEFT JOIN res_partner company
                           ON res_partner.parent_id = company.id
                      {where} ({email} {operator} {percent}
                           OR {display_name} {operator} {percent})
                           OR {code} {operator} {percent})
                     ORDER BY {display_name}
                    """.format(where=where_str, operator=operator,
                               email=unaccent('res_partner.email'),
                               percent=unaccent('%s'),
                               display_name=display_name,
                               code=unaccent('res_partner.code'),)

            where_clause_params += [search_name, search_name, search_name]
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
