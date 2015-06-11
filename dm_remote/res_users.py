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

import logging
from openerp import pooler
from openerp.osv import fields, osv
from openerp import SUPERUSER_ID
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

class res_users(osv.osv):
    _inherit = 'res.users'
    '''
    set the system config paramter 'remote_access' to only allow some users access ERP by some host
    remote_access format: {'address-1':['login1','login2'...], ..., 'address-n':[...]}
    sample: {'www.myerp.com:1021':['johnw','johnw1']}
    '''
    def authenticate(self, db, login, password, user_agent_env):
        cr = pooler.get_db(db).cursor()
        #check the remote access configuration parameter
        ICP = self.pool.get('ir.config_parameter')
        remote_access = ICP.get_param(cr, SUPERUSER_ID, 'remote_access')
        if remote_access:
            access_host = eval(remote_access)
            remote_host = user_agent_env.get('HTTP_HOST')
            if remote_host in access_host:
                logins = access_host.get(remote_host,[])
                if login not in logins:
                    raise osv.except_osv(_('Error!'), _("You are not allowed to access this site!"))
                    
        return super(res_users, self).authenticate(db, login, password, user_agent_env) 
res_users()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
