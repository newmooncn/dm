# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
from openerp.osv import fields,osv
from openerp.addons.base_status.base_stage import base_stage
from openerp.tools.translate import _
from lxml import etree
from openerp import netsvc
class project_project(osv.osv):
    _inherit = 'project.project'
    _columns = {
        'single_mrp_prod_order': fields.boolean('Single Manufacture Order',),
        'bom_id': fields.many2one('mrp.bom', string='Bill of Material',),
        'product_id': fields.related('bom_id', 'product_id', type='many2one', relation='product.product', string='Product', readonly=True),
        'bom_components': fields.related('bom_id', 'bom_lines', type='one2many', relation='mrp.bom', fields_id='bom_id', string='Components', readonly=True),
    }
    
    _defaults = {'single_mrp_prod_order':True}
    
    def set_done(self, cr, uid, ids, context=None):        
        if isinstance(ids, (int,long)):
            ids = [ids]
        if context == None:
            context = {}
        #the BOM is required when do project done
        for proj in self.browse(cr, uid, ids, context=context):
            if proj.project_type == 'engineer' and not proj.bom_id:
                raise osv.except_osv(_('Error!'), _('Project "%s", BOM is required to close to engineering Project.'%(proj.name,)))
        resu = super(project_project,self).set_done(cr, uid, ids, context)
        '''
        after project is done, trigger the 'act_button_manufacture' of the project's sale product ID
        ''' 
        for proj in self.browse(cr, uid, ids):
            #Only the engineering project need to do this action
            if proj.project_type != 'engineer':
                continue
            vals = {'bom_id':proj.bom_id.id, 'product_id':proj.bom_id.product_id.id}
            #the date_planned for the new manufacture
            date_planned = None
            new_mfg_prod_order_id = None
            if proj.single_mrp_prod_order:
                if new_mfg_prod_order_id:
                    vals.update({'mrp_prod_ids':[(4, new_mfg_prod_order_id)]})
            
            #the product quantity for the manufacture order.                        
            if new_mfg_prod_order_id:
                mrp_order_vals = {'origin':proj.name,'product_qty':1, 'date_planned':date_planned}
                self.pool.get('mrp.production').write(cr, uid, [new_mfg_prod_order_id], mrp_order_vals, context=context)                    
                                
        return resu
            
class project_task(base_stage, osv.osv):
    _inherit = "project.task"

    _columns = {
        'bom_id': fields.many2one('mrp.bom', string='Bill of Material'),
        'product_id': fields.related('bom_id', 'product_id', type='many2one', relation='product.product', string='Product', readonly=True),
        'components': fields.related('bom_id', 'bom_lines', type='one2many', relation='mrp.bom', fields_id='bom_id', string='Components', readonly=True)
    }

    def action_close(self, cr, uid, ids, context=None):
        if isinstance(ids, (int,long)):
            ids = [ids]
        if context == None:
            context = {}
        #the BOM is required when do project done
        for task in self.browse(cr, uid, ids, context=context):
            #Only the engineering project,  the bom_is is required
            if task.project_id.project_type == 'engineer' and not task.bom_id:
                raise osv.except_osv(_('Error!'), _('Task "%s", BOM is required for done.'%(task.name,)))
        return super(project_task,self).action_close(cr, uid, ids, context)