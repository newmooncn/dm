'''
Created on 2015-7-23

@author: johnw
'''
    #view monthly report
    def view_payroll(self, cr, uid, ids, context=None):
        rpt_id = ids[0]
        #read daily report data, create new monthly report based on it.
        rpt = self.read(cr, uid, rpt_id, ['emppay_sheet_ids'], context=context)
        payroll_ids = rpt['emppay_sheet_ids']
        if not payroll_ids:
            raise osv.except_osv(_('Error!'),_('No payroll generated!'))
        if len(payroll_ids) > 1:
            #got to list page
            act_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'metro_hr', 'action_hr_emppay_sheet')
            act_id = act_id and act_id[1] or False            
            act_win = self.pool.get('ir.actions.act_window').read(cr, uid, act_id, [], context=context)
            act_win['context'] = {'search_default_attend_month_id': rpt['id']}
            return act_win
        else:
            #go to form page
            form_view = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'metro_hr', 'hr_emppay_sheet_form')
            form_view_id = form_view and form_view[1] or False
            return {
                'name': _('Payroll'),
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': [form_view_id],
                'res_model': 'hr.emppay.sheet',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': payroll_ids[0],
            }