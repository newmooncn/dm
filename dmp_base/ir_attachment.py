# -*- coding: utf-8 -*-

from openerp.osv import fields, osv


class ir_attachment_type(osv.osv):
    _name = "ir.attachment.type"
    _columns = {
        'name': fields.char('Name', size=256),
    }
ir_attachment_type()


class ir_attachment(osv.osv):
    _inherit = "ir.attachment"
    _columns = {
        'attach_type_id': fields.many2one('ir.attachment.type','Attachment Type'),
    }

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        if context is None:
            context = {}
        if view_type == 'form' and context.get('o2m_attach'):
            view_id = self.pool.get('ir.ui.view').search(cr, uid,
                                    [('name', '=', 'acespritech.ir.attachment.form')])
            if view_id and isinstance(view_id, (list, tuple)):
                view_id = view_id[0]
        return super(ir_attachment, self).fields_view_get(cr, uid, view_id,
                                        view_type, context, toolbar=toolbar,
                                        submenu=submenu)

ir_attachment()
