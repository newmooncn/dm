'''
Created on 2013-8-21

@author: johnw
'''
from openerp.osv import osv, fields
class option_list(osv.osv):
    _name = 'option.list'
    _description = "Option List"
    _columns = {
        'option_name': fields.char('Option Name', size=64, required=True, select=True, copy=False),                
        'seq': fields.integer('Sequence'),
        'key': fields.char('Key', size=16, required=True),
        'name': fields.char('Name', size=64, required=True, select=True, translate=True),
        'memo': fields.char('Description', size=64),
    }
    _order = "option_name,seq"
    _sql_constraints = [
        ('opt_name_key_uniq', 'unique(option_name, key)', 'option name and key must be unique!'),
        ('opt_name_name_uniq', 'unique(option_name, name)', 'option name and name must be unique!'),
    ]
    def default_get(self, cr, uid, fields_list, context=None):
        vals = super(option_list,self).default_get(cr, uid, fields_list, context)
        if not vals.get('option_name'): return vals
        #if there is 'option_name' default value then set the default key and sequence
        cr.execute("select max(seq) from option_list where option_name = %s",(vals.get('option_name'),))
        data = cr.fetchone();
        key = 'key_1'
        seq = 1
        if data and len(data) > 0:
            seq = (data[0] or 0) +1
            key = 'key_' + str(seq)
        vals.update({
                     'key':key,
                     'seq':seq,
                     })
        return vals
        
