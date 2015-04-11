# -*- coding: utf-8 -*-
from openerp.osv import fields, osv

class account_move(osv.osv):
    _inherit = "account.move"
    '''
            列表中显示的partner来自account.move.line.partner_id,但是查询的时候使用的是account.move.partner_id作为查询条件,
            当partner_id没有存储到account.move中的时候就会出现问题,显示此行的partner正确,但是增加partner查询条件反而查询不到的情况
            为了兼容显示查询以前的数据(partner_id为空的),增加line_partner_id
    '''  
    _columns = {
        'line_partner_id': fields.related('line_id', 'partner_id', type="many2one", relation="res.partner", string="Move Partner"),
    }    
    #batch post
    def button_validate(self, cr, uid, ids, context=None):
        unpost_ids = self.search(cr, uid, [('id','in',ids),('state','=','draft')], context=context)
        return super(account_move,self).button_validate(cr, uid, unpost_ids, context=context)
    
class account_move_line(osv.osv):
    _inherit = "account.move.line"
    _columns = {
        'date_biz': fields.date('Biz Date', select=True, help="the business date for this entry, default is the account entry date, used when accountant input one account entry for many items at the end of the month."),
    }
    def default_get(self, cr, uid, field_names, context=None):
        res = super(account_move_line, self).default_get(cr, uid, field_names, context=context)
        date_biz = context.get('move_date',False) or fields.date.context_today(self,cr,uid)
        res['date_biz'] = date_biz
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: