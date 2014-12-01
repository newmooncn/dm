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
from openerp import tools
import os
import re
import logging

_logger = logging.getLogger(__name__)

'''
By original logic, once the 'ir_attachment.location' parameter' is set, then all the files
in ir_attachments, will be store to "openerp/%ir_attachment.location%/db_name/*"

Improve the file full path getting logic, to support user define their own storage root path
Usage:
Create system paramter "ir_attachment.location.root", set it to the full path that you want to store the attachment files
Then once the 'ir_attachment.location' parameter' is set, files will be store to:
"%ir_attachment.location.root%/%ir_attachment.location%/db_name/*"

'''
class ir_attachment(osv.osv):
    _inherit = "ir.attachment"
    '''
    get the attachments files root path
    tools.config['root_path'] is the %openerp% path, set by system
    user can set the parameter 'ir_attachment.location.root' to change the root path
    '''
    def _root_path(self, cr, uid):
        location = self.pool.get('ir.config_parameter').get_param(cr, uid, 'ir_attachment.location.root')
        if location:
            # location = 'file:filestore'
            assert location.startswith('file:'), "Unhandled filestore root location %s" % location
            location = location[5:]
    
            # sanitize location name and path
            location = re.sub('[.]','',location)
            location = location.strip('/\\')
            
            return location
        else:
            return tools.config['root_path']
    '''    
    Once 'ir_attachment.location' paramer is set,
    the the "_file_read(),_file_write(),_file_delte()" methods will call this method to get one file name's full path
    the file
    @param param: location, the value of 'ir_attachment.location' parameter
    @param path: the file name 
    '''
    def _full_path(self, cr, uid, location, path):
        # location = 'file:filestore'
        assert location.startswith('file:'), "Unhandled filestore location %s" % location
        location = location[5:]

        # sanitize location name and path
        location = re.sub('[.]','',location)
        location = location.strip('/\\')

        path = re.sub('[.]','',path)
        path = path.strip('/\\')
        #return os.path.join(tools.config['root_path'], location, cr.dbname, path)
        '''
        replace the original above logic, 
        call _root_path() to handle system config paramter 'ir_attachment.location.root' 
        that user defined as the attachment root path
        '''
        return os.path.join(self._root_path(cr, uid), location, cr.dbname, path)

    '''
    Utility method to get one ir_attachment record's file object
    @param param:id ir_attachment.id
    @return: the file object 
    '''
    def file_get(self, cr, uid, id,context=None):
        location = self.pool.get('ir.config_parameter').get_param(cr, uid, 'ir_attachment.location')
        fname = self.read(cr, uid, id, ['store_fname'],context=context)['store_fname']
        full_path = self._full_path(cr, uid, location, fname)
        r = ''
        try:
            r = open(full_path,'rb')
        except IOError:
            _logger.error("_read_file reading %s",full_path)
        return r
    '''
    Utility method to get one file name's full path 
    by "ir_attachment.location" and "ir_attachment.location.root"(if no then use %openerp% path) configuration
    @param param:id ir_attachment.id
    @return: the file full path including the file name 
    '''
    def full_path(self, cr, uid, fname):
        location = self.pool.get('ir.config_parameter').get_param(cr, uid, 'ir_attachment.location')
        return self._full_path(cr, uid, location, fname)