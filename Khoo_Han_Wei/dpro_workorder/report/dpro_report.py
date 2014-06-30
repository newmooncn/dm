# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from openerp import tools
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

class dpro_report(osv.osv):
    _name = "dpro.report"
    _description = "Work Orders Statistics"
    _auto = False
    
    def _get_info(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res_row = {
                'proj_name': '-',
                'train_name': '-',
                'prod_name': '-',
                'pr_bom_complete_name': None,
                'oline_loc': None
            }
            #update the project info
            if order.project_id:
                idx = 1
                proj_fld_idxs = {1:'proj_name',2:'train_name',3:'prod_name'}
                for item in order.project_id.complete_name.split('/'):
                    res_row.update({proj_fld_idxs[idx]:item.strip()})
                    if idx >= 3:
                        break
                    idx += 1
            if order.pr_bom_id:
                res_row.update({'pr_bom_complete_name':self._get_bom_one_full_name(order.pr_bom_id)})
            #update oline loc info
            if order.oline_prod_id:
                oline_loc = '%s - %s - %s'%(order.oline_prod_id.loc_rack or '',  order.oline_prod_id.loc_row or '', order.oline_prod_id.loc_case or '')
                res_row.update({'oline_loc':oline_loc})
                
            res[order.id] = res_row
        return res

    def _get_bom_one_full_name(self, bom, level=10):
        if level<=0:
            return '...'
        if bom.bom_id:
            parent_path = self._get_bom_one_full_name(bom.bom_id, level-1) + " - "
        else:
            parent_path = ''
        return parent_path + bom.name    
    _columns = {
        'id': fields.integer('Work Order ID'),
        'name': fields.char('Work Order No', size=64, ),
        'project_id': fields.many2one('account.analytic.account','Project'),
        'proj_name': fields.function(_get_info, type='char', string='Proj ID', multi='_get_info', ),
        'train_name': fields.function(_get_info, type='char', string='Train ID', multi='_get_info', ),
        'prod_name': fields.function(_get_info, type='char', string='Prod ID', multi='_get_info', ),
        'status_id': fields.selection([('Pending', 'Pending Confirmation'), ('Confirmed', 'Confirmed'),
                                       ('In Progress', 'In Progress'), ('Completed', 'Completed'), ('QA', 'Quality Assurance'),
                                       ('Closed', 'Closed')], 'WO Status'),
        'work_type': fields.many2one('dpro.work.type', 'WO Type'),
        'date_in': fields.datetime('Issue Date', ),
        
        'pr_prod_id': fields.many2one('product.product','Part Replaced'),
        'pr_categ_name':fields.related('pr_prod_id','categ_id',type='many2one',relation='product.category',string='Sub.Group'),
        'partner_shipping_id': fields.many2one('res.partner', 'Work Loc. Code', ),
        'user_id': fields.many2one('res.users', 'Announcer', ),
        'pr_bom_id': fields.many2one('mrp.bom', 'Part Relaced BOM'),
        'pr_bom_complete_name': fields.function(_get_info, type='char', multi='_get_info', string='Asset ID'),
        'pr_name': fields.char('Part Description', size=128),
        'pr_sup_supplier' : fields.many2one('res.partner', 'Supplier'),
        'pr_sup_product_code': fields.char('Supp Part No', size=64),
        'pr_bt_part_no': fields.related('pr_prod_id','bt_part_number',type='char',string='BT Part No'),
        'pr_default_code': fields.related('pr_prod_id','default_code',type='char',string='Cust Part No'),
        'pr_serial_id': fields.many2one('stock.production.lot', 'Serial No'),
        'pr_serial_rev': fields.char('Part Revision', size=128),
        
        'work_requested': fields.text('Work Requested'),
        'wr_code_id': fields.many2one('work.request.code', 'WR Code'),
        'mod_test_id': fields.char('MOD/Test ID', size=64),
        'rev_test': fields.char('Rev. Test', size=64),
        'maintain_reason': fields.text('Maintenance Reason'), 
        'problem_code_id': fields.many2one('base.problem.code', 'Problem Code'),  
        'defect': fields.text('Defect/Cause'),
        'action_taken': fields.text('Action Taken'),
        'mode_test_result_id': fields.char('MOD/Result ID', size=256),
        'rev_test_result': fields.char('Rev. Results', size=256),
        'comment': fields.text('Comments'),
        
        'oline_prod_id': fields.many2one('product.product','Part Replaced'),
        'oline_warranty_id': fields.related('oline_serial_id', 'warranty_id', type='many2one', relation='base.warranty', string='Material warranty'),
        'oline_name': fields.text('Part Description(Material)', ),
        'oline_loc': fields.function(_get_info, type='char', multi='_get_info', string='Location(Material)', ),
        'oline_bt_part_no': fields.related('oline_prod_id','bt_part_number',type='char',string='BT Part No'),
        'oline_default_code': fields.related('oline_prod_id','default_code',type='char',string='Cust Part No'),
        'oline_sup_product_code': fields.char('Supp Part No', size=64),
        'oline_sup_supplier' : fields.many2one('res.partner', 'Vendor'),
        'pr_serial_id2': fields.many2one('stock.production.lot', 'S/N out'),
        'oline_serial_id': fields.many2one('stock.production.lot', 'S/N In'),
        'pr_serial_rev2': fields.char('Rev Out', size=128),
        'oline_serial_rev': fields.char('Rev In', size=128),
        'oline_qty': fields.float('Quantity', digits_compute= dp.get_precision('Qty'), ),
        'oline_uom': fields.many2one('product.uom', 'Unit', ),
        'relevancy': fields.selection([('true','True'),('false','False')],'Relevancy'), 
    }
#    _order = 'date desc'

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'dpro_report')
        cr.execute("""
            create or replace view dpro_report as (
select 
wo.id
,wo.name --1
,wo.project_id --2,3,4
,wo.status_id --5
,wo.work_type --6
,wo.date_in --7
,pr.product_id pr_prod_id --8
,wo.partner_shipping_id --9
,wo.user_id --10
,pr_bom.id pr_bom_id --11,13,16
,pr.name pr_name --12
--,pr.bt_part_no pr_bt_part_no --13, use OE's related field by pr_prod_id
,pr_sup.name pr_sup_supplier --14
,pr_sup.product_code pr_sup_product_code --15
,pr.serial_id pr_serial_id --17,30
,pr_ser_rev.name pr_serial_rev --18
,wo.work_requested --19
,wo.wr_code_id --20
,wo.mod_test_id --21
,wo.rev_test --22
,wo.maintain_reason --23
,wo.problem_code_id --24
,wo.defect --25
,wo.action_taken --26
,wo.mode_test_result_id --27
,wo.rev_test_result --28
,wo.comment --29
,oline.product_id oline_prod_id --32,33,34
,oline.name oline_name --31
,oline_sup.product_code oline_sup_product_code --35
,oline_sup.name oline_sup_supplier --36
,pr.serial_id pr_serial_id2 --37
,oline.prodlot_id oline_serial_id --38
,pr_ser_rev.name pr_serial_rev2 --39
,oline_ser_rev.name oline_serial_rev --40
,oline.product_uom_qty oline_qty --41
,oline.product_uom oline_uom --42
,wo.relevancy --43
from sale_order wo
left join (select a.*
    from workorder_part_replace a
    join (
        select workorder_id,min(id) as id 
        from workorder_part_replace 
        group by workorder_id
        ) b
    on a.id = b.id) pr on wo.id = pr.workorder_id
left join (select a.*
    from mrp_bom a
    join (
        select product_id,min(id) as id 
        from mrp_bom 
        group by product_id
        ) b
    on a.id = b.id) pr_bom on pr.product_id = pr_bom.product_id
left join (select c.id product_product_id,a.*
    from product_supplierinfo a
    join (
        select product_id,min(id) as id 
        from product_supplierinfo 
        group by product_id
        ) b
    on a.id = b.id
    join product_product c 
    on b.product_id = c.product_tmpl_id) pr_sup on pr.product_id = pr_sup.product_product_id
left join (select a.*
    from stock_production_lot_revision a
    join (
        select lot_id,max(id) as id 
        from stock_production_lot_revision 
        group by lot_id
        ) b
    on a.id = b.id) pr_ser_rev on pr.serial_id = pr_ser_rev.lot_id
left join (select a.*
    from sale_order_line a
    join (
        select order_id,min(id) as id 
        from sale_order_line 
        group by order_id
        ) b
    on a.id = b.id) oline on wo.id = oline.order_id    
left join (select c.id product_product_id,a.*
    from product_supplierinfo a
    join (
        select product_id,min(id) as id 
        from product_supplierinfo 
        group by product_id
        ) b
    on a.id = b.id
    join product_product c 
    on b.product_id = c.product_tmpl_id) oline_sup on oline.product_id = oline_sup.product_product_id    
left join (select a.*
    from stock_production_lot_revision a
    join (
        select lot_id,max(id) as id 
        from stock_production_lot_revision 
        group by lot_id
        ) b
    on a.id = b.id) oline_ser_rev on oline.prodlot_id = oline_ser_rev.lot_id    
            )
        """)
dpro_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
