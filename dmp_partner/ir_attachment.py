# -*- coding: utf-8 -*-
'''
Add attachments to res_partner form view
Based on the dmp_base.ir_attachment
'''
from openerp.osv import fields, osv

class res_partner(osv.osv):
    _inherit = "res.partner"
    _columns = {
        'attachment_lines': fields.one2many('ir.attachment', 'partner_id','Attachment'),
    }
res_partner()

class ir_attachment(osv.osv):
    _inherit = "ir.attachment"
    _columns = {
        #Add the fields related to your table
        'partner_id': fields.many2one('res.partner', 'Partner'),
    }
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        #Add the field that your table
        if vals.get('partner_id'):
            vals['res_id'] = vals['partner_id']
            vals['res_model'] = 'product.product'        
            
        return super(ir_attachment, self).create(cr, uid, vals, context)

ir_attachment()        