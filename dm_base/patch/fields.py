# -*- coding: utf-8 -*-


#add the object name to the download PDF file name, by johnw, 2013/12/29

           
'''
Add the 'domain_fnct' to one2many field's property, to handle the dynamic domain
'''
from openerp.osv import fields

def one2many_get(self, cr, obj, ids, name, user=None, offset=0, context=None, values=None):
    if context is None:
        context = {}
    if self._context:
        context = context.copy()
    context.update(self._context)
    if values is None:
        values = {}

    res = {}
    for id in ids:
        res[id] = []

    domain = self._domain(obj) if callable(self._domain) else self._domain
    '''
    Add the domain_fnct support for dynamic domain, used by mrp_bom.bom_routing_ids
    the original domain can accept function by code: "domain = self._domain(obj) if callable(self._domain) else self._domain"
    , but that domain method will only accept one 'self' parameter (self._domain(obj)) 
    For the new method signature, it wil accept parameters: self, cr, uid, ids, field_name, context
    Then we can use 'ids' to return the domain dynamically
    '''
    if hasattr(self,'domain_fnct') and self.domain_fnct:
        domain = domain + self.domain_fnct(obj,cr,user,ids,name,context=context)
            
    ids2 = obj.pool.get(self._obj).search(cr, user, domain + [(self._fields_id, 'in', ids)], limit=self._limit, context=context)
    for r in obj.pool.get(self._obj)._read_flat(cr, user, ids2, [self._fields_id], context=context, load='_classic_write'):
        if r[self._fields_id] in res:
            res[r[self._fields_id]].append(r['id'])
    return res
    
fields.one2many.get =  one2many_get
'''
Improve many2many field's 'domain' property, to handle the dynamic domain, can assign function name to it
'''
def many2many_get(self, cr, model, ids, name, user=None, offset=0, context=None, values=None):
    if not context:
        context = {}
    if not values:
        values = {}
    res = {}
    if not ids:
        return res
    for id in ids:
        res[id] = []
    if offset:
        _logger.warning(
            "Specifying offset at a many2many.get() is deprecated and may"
            " produce unpredictable results.")
    obj = model.pool.get(self._obj)
    rel, id1, id2 = self._sql_names(model)

    # static domains are lists, and are evaluated both here and on client-side, while string
    # domains supposed by dynamic and evaluated on client-side only (thus ignored here)
    # FIXME: make this distinction explicit in API!
    domain = isinstance(self._domain, list) and self._domain or []
    
    '''
    Add the domain function support for dynamic domain, used by mrp_bom.comp_routing_workcenter_ids
    the domain function can accept parameters: self, cr, uid, ids, field_name, context
    12/02/2014, johnw
    '''
    domain = self._domain(model,cr,user,ids,name,context=context) if callable(self._domain) else domain
    
    wquery = obj._where_calc(cr, user, domain, context=context)
    obj._apply_ir_rules(cr, user, wquery, 'read', context=context)
    from_c, where_c, where_params = wquery.get_sql()
    if where_c:
        where_c = ' AND ' + where_c

    order_by = ' ORDER BY "%s".%s' %(obj._table, obj._order.split(',')[0])

    limit_str = ''
    if self._limit is not None:
        limit_str = ' LIMIT %d' % self._limit

    query, where_params = self._get_query_and_where_params(cr, model, ids, {'rel': rel,
           'from_c': from_c,
           'tbl': obj._table,
           'id1': id1,
           'id2': id2,
           'where_c': where_c,
           'limit': limit_str,
           'order_by': order_by,
           'offset': offset,
            }, where_params)

    cr.execute(query, [tuple(ids),] + where_params)
    for r in cr.fetchall():
        res[r[1]].append(r[0])
    return res    

fields.many2many.get =  many2many_get


'''
Improve the read of related field, add the 'reference' type handling
'''
from openerp import SUPERUSER_ID
def related_fnct_read(self, obj, cr, uid, ids, field_name, args, context=None):
    res = {}
    for record in obj.browse(cr, SUPERUSER_ID, ids, context=context):
        value = record
        for field in self.arg:
            if isinstance(value, list):
                value = value[0]
            value = value[field] or False
            if not value:
                break
        res[record.id] = value

    if self._type == 'many2one':
        # res[id] is a browse_record or False; convert it to (id, name) or False.
        # Perform name_get as root, as seeing the name of a related object depends on
        # access right of source document, not target, so user may not have access.
        value_ids = list(set(value.id for value in res.itervalues() if value))
        value_name = dict(obj.pool.get(self._obj).name_get(cr, SUPERUSER_ID, value_ids, context=context))
        res = dict((id, value and (value.id, value_name[value.id])) for id, value in res.iteritems())

    elif self._type in ('one2many', 'many2many'):
        # res[id] is a list of browse_record or False; convert it to a list of ids
        res = dict((id, value and map(int, value) or []) for id, value in res.iteritems())
        
    #johnw, 01/08/2015, add 'reference' support
    elif self._type =='reference':
        # res[id] is a browse_record(browse_record: browse_record(emp.reimburse, 91)) or False; convert it to "obj_name,obj_id" string format
        res = dict((id, value and '%s,%s'%(value._model._name, value.id)) for id, value in res.iteritems())

    return res

fields.related._fnct_read =  related_fnct_read