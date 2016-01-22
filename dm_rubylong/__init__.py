# -*- coding: utf-8 -*-
##############################################################################
# OpenERP Connector
# Copyright 2015 DMEMS <johnw@dmems.com>
##############################################################################
#import main    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

from openerp.tools import resolve_attr, config
from xml.sax.saxutils import escape
import os
from openerp.osv import osv

'''
fix below isuee in code: file_obj.write('<xml>'+data_xml+'</xml>')
'ascii' codec can't encode characters in position 1714-1734: ordinal not in range(128)
'''
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import logging
_logger = logging.getLogger(__name__)

def get_rubylong_fields_xml_body(obj, field_list):
    data_xml = ''
    for field_name in field_list:
        field_value = None
        if isinstance(field_name, tuple):
            #use another xml field name
            xml_name = field_name[1] or field_name[0].replace('.', '_')
            new_field_name = field_name[0]
            field_value = resolve_attr(obj, new_field_name)
            if field_value and len(field_name) == 3 and callable(field_name[2]):
                #need transfer field value
                field_value = field_name[2](field_value)
        else:
            xml_name = field_name.replace('.', '_')
            field_value = resolve_attr(obj, field_name)
        #change the false field to '', otherwise the 'false' string will be generated to xml        #change the false field to '', otherwise the 'false' string will be generated to xml
        if isinstance(field_value,bool) and not field_value:
            field_value = ''
        #xml escape
        if isinstance(field_value,(type(u' '),type(' '))):
            field_value = escape(field_value)        
            field_value = field_value.strip()
        data_xml += '<%s>%s</%s>'%(xml_name, field_value, xml_name)
    return data_xml

def get_rubylong_fields_xml(obj, tag_name, field_list):    
    data_xml = "<%s>"%(tag_name, )
    data_xml += get_rubylong_fields_xml_body(obj, field_list)            
    data_xml += "</%s>"%(tag_name, )
    return data_xml

def get_rublong_data_file_name(obj, data_xml, dbname='db_none'):
    #cur_path = os.path.split(os.path.realpath(__file__))[0] + "/wizard"
    file_path = get_rubylong_temp_file_path(dbname)
    file_path = os.path.join(file_path, 'data')
    if not os.path.exists(file_path):
        os.makedirs(file_path)
        
    file_name = '%s_%s.xml'%(obj._name.replace('.','_'),obj.id)
    file_name_full = os.path.join(file_path, file_name)
    file_obj = open(file_name_full,'w')
    _logger.debug('@@@@@@@@@@@: %s', file_name_full)
    file_obj.write('<xml>'+data_xml+'</xml>')
    _logger.debug('@@@@@@@@@@@: writed file')
    file_obj.close()
    _logger.debug('@@@@@@@@@@@: closed file')
    return file_name, file_name_full

def get_rublong_data_url(obj, data_xml, dbname='db_none'):
    file_name = get_rublong_data_file_name(obj, data_xml, dbname)[0]
    return '%s/%s/data/%s'%('/web/static/rubylong', dbname, file_name)

def get_rublong_user_file_path(dbname='db_none'):
    file_path = get_rubylong_temp_file_path(dbname)
    file_path = os.path.join(file_path, 'templates')
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    return file_path
        
def get_rublong_user_file_url(file_name, dbname='db_none'):
    return '%s/%s/templates/%s'%('/web/static/rubylong', dbname, file_name)
        
def get_rubylong_temp_file_path(dbname='db_none'):
    #find /web/static path in the addons path
    path_find = None
    import openerp.modules as addons    
    adps = addons.module.ad_paths
    for adp in adps:
        path = os.path.join(adp,'web/static')
        if os.path.exists(path):
            path_find = path
            break
    #find /web/static path in the openerp root path
    if not path_find:
        rtp = os.path.normcase(os.path.abspath(config['root_path']))
        path = os.path.join(rtp,'addons','web/static')
        if os.path.exists(path):
            path_find = path
    if not path_find:
        raise osv.except_osv(_('Error'),_('Can not find web/static path to store the Rubylong temp files!'))
    
    file_path = os.path.join(path_find, 'rubylong', dbname)
    if not os.path.exists(file_path):
        os.makedirs(file_path)
                
    return file_path
    
import dm_rubylong