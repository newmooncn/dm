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
from osv import fields,osv,orm
from openerp import netsvc
from openerp.addons.dm_base.utils import set_seq_o2m
import openerp.addons.decimal_precision as dp

class sale_order(osv.osv):
    _inherit="sale.order"
    
    def _order_line_with_configs(self, cr, uid, ids, field_names, args, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            design_line_ids = [line.id for line in order.order_line if line.mto_design_id]
            res[order.id] = design_line_ids
        return res
            
    _columns={
        #used by PDF  
        'order_line_with_config': fields.function(_order_line_with_configs, type='one2many', relation='sale.order.line', fields_id='order_id', string='Lines with Configuration')
    }     
       
class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    _columns = {
        'mto_design_id': fields.many2one('mto.design', 'Configuration'),    
        #config changing dummy field
        'config_changed':fields.function(lambda *a,**k:{}, type='boolean',string="Config Changed",),        
    }
        
    def copy_data(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'mto_design_id': None,
        })         
        return super(sale_order_line, self).copy_data(cr, uid, id, default, context=context)     
           
    def onchange_config(self, cr, uid, ids, config_id, context=None):
        val= {}
        if config_id:
            config = self.pool.get('mto.design').browse(cr, uid, config_id, context=context)
            val = {'product_id':config.product_id.id,
                   'price_unit':config.list_price,
                   'th_weight':config.weight,
                   'name':'%s(%s)'%(config.product_id.name, config.name),
                   'config_changed':True}    
        return {'value':val}
    
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False,
            fiscal_position=False, flag=False, context=None):

        res=super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty,
            uom, qty_uos, uos, name, partner_id,
            lang, update_tax, date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)
        
        if context.get('config_changed'):
            #if the product changing is triggered by the config changing, then do not change the price and weight
            fields_remove = ['price_unit', 'th_weight', 'name']
            for field in fields_remove:
                if res['value'].has_key(field):
                    res['value'].pop(field)
            res['value']['config_changed'] = False
        
        return res
            
    def create(self, cr, uid, vals, context=None):
        new_id = super(sale_order_line, self).create(cr, uid, vals, context)
        #auto copy the common mto design to a new design
        line = self.browse(cr, uid, new_id, context=context)
        if line.mto_design_id and line.mto_design_id.type == 'common':
            config_obj = self.pool.get('mto.design')
            name = '%s-%s-%s'%(line.mto_design_id.name, line.order_id.name, line.sequence)
            config_new_id = config_obj.copy(cr, uid, line.mto_design_id.id, context=context)
            config_obj.write(cr, uid, config_new_id, {'name':name, 'type':'sale'}, context=context)
            self.write(cr, uid, line.id, {'mto_design_id': config_new_id}, context=context)
        return new_id
        
    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        config_old_datas = self.read(cr, uid, ids, ['mto_design_id'], context=context)            
        resu = super(sale_order_line, self).write(cr, uid, ids, vals, context=context)
        #deal the mto_design_id     
        if 'mto_design_id' in vals:
            lines = self.browse(cr, uid, ids, context)
            config_olds = {}
            for config in config_old_datas:
                config_old_id = config['mto_design_id'] and config['mto_design_id'][0] or None
                config_olds[config['id']] = config_old_id
            config_obj = self.pool.get('mto.design')
            for line in lines:
                config_old_id = config_olds[line.id]
                #clear config, #assign new config,  #change config
                if not line.mto_design_id or not config_old_id or line.mto_design_id.id != config_old_id:
                    if config_old_id:
                        #if old config is for sale, then delete it
                        config_old_type = config_obj.read(cr, uid, config_old_id, ['type'], context=context)                        
                        if config_old_type['type'] == 'sale':
                            config_obj.unlink(cr, uid, config_old_id, context=context)
                    #if new config is common, then do copy
                    if line.mto_design_id and line.mto_design_id.type == 'common':                        
                        context['default_type'] = 'sale'
                        config_new_id = config_obj.copy(cr, uid, line.mto_design_id.id, context=context)
                        name = '%s-%s-%s'%(line.mto_design_id.name, line.order_id.name, line.sequence)
                        config_obj.write(cr, uid, config_new_id, {'name':name, 'type':'sale'}, context=context)     
                        self.write(cr, uid, line.id, {'mto_design_id': config_new_id})
                
        return resu
    
    def edit_config(self, cr, uid, ids, context=None):
        if not context.get('config_id'):
            return False
        return self.pool.get('mto.design').open_designment(cr, uid, context.get('config_id'), context=context)             
    
class mto_design(osv.osv):
    _inherit = "mto.design"
    def _so_line_id(self, cr, uid, ids, field_names, args, context=None):
        res = dict.fromkeys(ids,None)
        for id in ids:
            so_ids = self.pool.get('sale.order.line').search(cr, uid, [('mto_design_id','=',id)])
            if so_ids:
                res[id] = so_ids[0]
        return res
    _columns = {'so_line_id': fields.function(_so_line_id, string='SO Line', type='many2one', relation='sale.order.line', store=True)}
    