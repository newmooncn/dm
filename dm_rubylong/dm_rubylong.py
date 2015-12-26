# -*- coding: utf-8 -*-
##############################################################################
# OpenERP Connector
# Copyright 2013 DMEMS <johnw@dmems.com>
##############################################################################

from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import fields, osv

class ReportXML(osv.osv):
    _inherit = 'ir.actions.report.xml'
    _defaults = {
        'webkit_debug': True,
        'precise_mode': True,
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
