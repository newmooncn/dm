# -*- coding: utf-8 -*-
from openerp.osv import osv

'''
Entry move source:
出纳-存取款,银行转账,其他收款,其他付款: cash.bank.trans
出纳-员工借款:emp.borrow
出纳-员工报销:emp.reimburse
'''    
'''
出纳-存取款,银行转账,其他收款,其他付款
Add source_id for bank/cash transaction
'''        
class cash_bank_trans(osv.osv):
    _inherit = 'cash.bank.trans'
    def _prepare_payment_move(self, cr, uid, move_name, order, journal,period, context=None):
        res = super(cash_bank_trans,self)._prepare_payment_move(cr, uid, move_name, order, journal,period, context=context)
        res['source_id'] = '%s,%s'%('cash.bank.trans',order.id)
        return res
    
''': cash.bank.trans
出纳-员工借款:emp.borrow
Add source_id for employee borrow
'''        
class emp_borrow(osv.osv):
    _inherit = 'emp.borrow'
    def _prepare_move(self, cr, uid, move_name, order, journal,period, context=None):
        res = super(emp_borrow,self)._prepare_move(cr, uid, move_name, order, journal,period, context=context)
        res['source_id'] = '%s,%s'%('emp.borrow',order.id)
        return res  
    
'''
出纳-员工报销:emp.reimburse
Add source_id for employee reimburse
'''        
class emp_reimburse(osv.osv):
    _inherit = 'emp.reimburse'    
    def _prepare_move(self, cr, uid, move_name, order, journal,period, context=None):
        res = super(emp_reimburse,self)._prepare_move(cr, uid, move_name, order, journal,period, context=context)
        res['source_id'] = '%s,%s'%('emp.reimburse',order.id)
        return res  
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: