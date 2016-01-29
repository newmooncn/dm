# -*- coding: utf-8 -*-
##############################################################################
# OpenERP Connector
# Copyright 2013 DMEMS <johnw@dmems.com>
##############################################################################

from openerp.osv import fields, orm
from openerp.addons.dm_base import utils
import os
import openerp.tools as tools
from openerp.tools.config import config
from openerp.tools.translate import _

from . import get_rublong_user_file_path, get_rublong_user_file_url

class ir_actions_report_xml(orm.Model):
    _inherit = 'ir.actions.report.xml'
    
    def _get_default_rubylong_template(self, cr, uid, ids, field_names, args, context):
        cur_path = os.path.split(os.path.realpath(__file__))[0] + "/wizard"
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = None
            if not order.default_excel_template_file_name:
                continue
            path = os.path.join(cur_path,order.default_excel_template_file_name)
            data = open(path,'rb').read().encode('base64')
            res[order.id] = data
        return res
    def write(self, cr, uid, ids, vals, context=None):
        if 'user_rubylong_file_name' in vals:
            if vals['user_rubylong_file_name'] and not vals['user_rubylong_file_name'].endswith('.grf'):
                raise orm.except_orm(_('Error!'),_('Only .grf files can be upload as template for Rubylong report!'))
        return super(ir_actions_report_xml, self).write(cr, uid, ids, vals, context=context)
    
    def _rubylong_info(self, cr, uid, ids, field_names, args, context):
        res = {}
        for id in ids:
            res[id] = {}
            for field_name in field_names:
                res[id][field_name] = None
        file_path_user = get_rublong_user_file_path(cr.dbname)
        for rpt in self.browse(cr, uid, ids, context=context):
            if not rpt.is_rubylong:
                continue
            #get default file data and name
            if rpt.default_rubylong_file_path:
                #remove the first '/' or '\'
                file_path = rpt.default_rubylong_file_path[1:]
                report_file = tools.file_open(file_path, 'rb')
                res[rpt.id]['default_rubylong_file'] = report_file.read().encode('base64')                
                file_paths = rpt.default_rubylong_file_path.split('/')
                res[rpt.id]['default_rubylong_file_name'] = file_paths[len(file_paths)-1]
                
            #get default sample data file data and name
            if rpt.default_rubylong_data_file_path:
                #remove the first '/' or '\'
                file_path = rpt.default_rubylong_data_file_path[1:]
                report_file = tools.file_open(file_path, 'rb')
                res[rpt.id]['default_rubylong_data_file'] = report_file.read().encode('base64')                
                file_paths = rpt.default_rubylong_data_file_path.split('/')
                res[rpt.id]['default_rubylong_data_file_name'] = file_paths[len(file_paths)-1]
            
            #user file is first, then system file
            rubylong_file_path = None
            if rpt.user_rubylong_file_name:
                rubylong_file_path = os.path.join(file_path_user, rpt.user_rubylong_file_name)
                if os.path.exists(rubylong_file_path):
                    rubylong_file_path = get_rublong_user_file_url(rpt.user_rubylong_file_name, cr.dbname)
                else:
                    rubylong_file_path = rpt.default_rubylong_file_path
            else:
                rubylong_file_path = rpt.default_rubylong_file_path
            res[rpt.id]['rubylong_file_path'] = rubylong_file_path
            
        return res

    def _get_user_rubylong_file(self, cr, uid, ids, field_names, args, context=None):
        res = {}
        for id in ids:
            res[id] = {}
            for field_name in field_names:
                res[id][field_name] = None
        file_path_user = get_rublong_user_file_path(cr.dbname)
        for order in self.browse(cr, uid, ids, context=context):
            for field_name in field_names:
                file_name = None
                if field_name == 'user_rubylong_file' and order.user_rubylong_file_name:
                    file_name = os.path.join(file_path_user, order.user_rubylong_file_name)
                if field_name == 'user_rubylong_data_file' and order.user_rubylong_data_file_name:
                    file_name = os.path.join(file_path_user, order.user_rubylong_data_file_name)
                if file_name:
                    try:
                        file_obj = open(file_name, 'rb')
                        res[order.id][field_name] = file_obj.read().encode('base64')
                        file_obj.close() 
                    except IOError, e:
                        continue
        return res        
    
    def _set_user_rubylong_file(self, cr, uid, id, field_name, value, args, context=None):
        user_rubylong_file_name = None
        if field_name == 'user_rubylong_file':
            user_rubylong_file_name = self.read(cr, uid, id, ['user_rubylong_file_name'],context=context)['user_rubylong_file_name']
        if field_name == 'user_rubylong_data_file':
            user_rubylong_file_name = self.read(cr, uid, id, ['user_rubylong_data_file_name'],context=context)['user_rubylong_data_file_name']
        if not user_rubylong_file_name:
            return  
        #find the file full path to write
        file_path_user = get_rublong_user_file_path(cr.dbname)
        file_name = os.path.join(file_path_user, user_rubylong_file_name)
        #write data
        file_obj = open(file_name, 'wb')
        bin_value = value.decode('base64')
        file_obj.write(bin_value)
        file_obj.close() 
    
    _columns = {
        #defined in xml
        'is_rubylong': fields.boolean('Rubylong Report'),        
        'default_rubylong_file_path': fields.char('Default report template file path'),
        'default_rubylong_data_file_path': fields.char('Default report data file path'),
        
        #default file data and file name by default_rubylong_file_path
        'default_rubylong_file': fields.function(_rubylong_info, type='binary',  string = 'Default template file', multi='rubylong'),
        'default_rubylong_file_name': fields.function(_rubylong_info,  type='char', size=128, string='Default template file name', multi='rubylong'),
        
        #default file data and file name by default_rubylong_data_file_path
        'default_rubylong_data_file': fields.function(_rubylong_info, type='binary',  string = 'Default data sample file', multi='rubylong'),
        'default_rubylong_data_file_name': fields.function(_rubylong_info,  type='char', size=128, string='Default data sample file name', multi='rubylong'),
        
        #user uploaded defined template files by self
        'user_rubylong_file': fields.function(_get_user_rubylong_file, fnct_inv=_set_user_rubylong_file,  type='binary',  string = 'User template file', multi='userfile'),
        'user_rubylong_file_name': fields.char('User template file name'),
        
        #user uploaded defined data files by self
        'user_rubylong_data_file': fields.function(_get_user_rubylong_file, fnct_inv=_set_user_rubylong_file,  type='binary',  string = 'User data file', multi='userfile'),
        'user_rubylong_data_file_name': fields.char('User data file name'),        
        
        #the report file used to render report 
        'rubylong_file_path': fields.function(_rubylong_info,  type='char', size=128, string='Report template file path', multi='rubylong'),
        
        #user defined report downlod file name, if not defined then use report name as the download file name
        'download_file_name': fields.char('Report file name', help='If not set then use report name as download file name'),
        'export_direct': fields.boolean('Export direct'),
        'export_direct_type': fields.selection([('1','Excel'),('2','Txt'),('3','Html'),('4','RTF'),('5','PDF'),('6','CSV'),('7','Image')], string = 'Export Type'),
    }
    
    def default_get(self, cr, uid, fields_list, context=None):
        vals = super(ir_actions_report_xml,self).default_get(cr, uid, fields_list, context)
        vals['export_direct_type'] = '5'
        return vals
        
class Report(orm.Model):
    _inherit = 'report'        
    def render(self, cr, uid, ids, template, values=None, context=None):
        #add report rubylong file path
        report = self._get_report_from_name(cr, uid, template)
        if report.is_rubylong:
            values.update({'rubylong_file_path':report.rubylong_file_path})    
        values.update({'report_title':report.download_file_name or report.name})
        #update export parameter
        values.update({'export_direct':report.export_direct and 1 or 0, 'export_direct_type':report.export_direct_type or '5'})
        return super(Report, self).render(cr, uid, ids, template, values=values, context=context)
        
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
