# -*- coding: utf-8 -*-

from openerp.osv import osv
          
'''
fix the next_number updating issue for the standard sequence
'''
from openerp.addons.base.ir.ir_sequence import ir_sequence

def _next(self, cr, uid, seq_ids, context=None):
    if not seq_ids:
        return False
    if context is None:
        context = {}
    force_company = context.get('force_company')
    if not force_company:
        force_company = self.pool.get('res.users').browse(cr, uid, uid).company_id.id
    sequences = self.read(cr, uid, seq_ids, ['name','company_id','implementation','number_next','prefix','suffix','padding'])
    preferred_sequences = [s for s in sequences if s['company_id'] and s['company_id'][0] == force_company ]
    seq = preferred_sequences[0] if preferred_sequences else sequences[0]
    if seq['implementation'] == 'standard':
        cr.execute("SELECT nextval('ir_sequence_%03d')" % seq['id'])
#        seq['number_next'] = cr.fetchone()
    else:
        cr.execute("SELECT number_next FROM ir_sequence WHERE id=%s FOR UPDATE NOWAIT", (seq['id'],))
        #cr.execute("UPDATE ir_sequence SET number_next=number_next+number_increment WHERE id=%s ", (seq['id'],))
    #fixed by johnw, to update the number_next for all sequence type.
    seq['number_next'] = cr.fetchone()    
    cr.execute("UPDATE ir_sequence SET number_next=%s+1 WHERE id=%s ", (seq['number_next'], seq['id'],))
            
    d = self._interpolation_dict()
    try:
        interpolated_prefix = self._interpolate(seq['prefix'], d)
        interpolated_suffix = self._interpolate(seq['suffix'], d)
    except ValueError:
        raise osv.except_osv(_('Warning'), _('Invalid prefix or suffix for sequence \'%s\'') % (seq.get('name')))
    return interpolated_prefix + '%%0%sd' % seq['padding'] % seq['number_next'] + interpolated_suffix  
  
ir_sequence._next =  _next
    