# -*- coding: utf-8 -*-

import ast
import base64
import csv
import functools
import glob
import itertools
import jinja2
import logging
import operator
import datetime
import hashlib
import os
import re
import simplejson
import sys
import time
import urllib2
import zlib
from xml.etree import ElementTree
from cStringIO import StringIO

import babel.messages.pofile
import werkzeug.utils
import werkzeug.wrappers
try:
    import xlwt
except ImportError:
    xlwt = None

import openerp
import openerp.modules.registry
from openerp.addons.base.ir.ir_qweb import AssetsBundle, QWebTemplateNotFound
from openerp.modules import get_module_resource
from openerp.tools import topological_sort
from openerp.tools.translate import _
from openerp.tools import ustr
from openerp import http, tools

from openerp.http import request, serialize_exception as _serialize_exception

_logger = logging.getLogger(__name__)


# 1 week cache for asset bundles as advised by Google Page Speed
BUNDLE_MAXAGE = 60 * 60 * 24 * 7

class Rubylong(http.Controller):
    _cp_path = '/dm_rubylong'
    @http.route('/dm_rubylong/design/read', type='http', auth="public")
    def design_read(self, *args, **kw):        
        print tools.config['root_path']
        file_name = os.path.join('C:\0-code\oe80-dm\openerp', '/dmc_actin/static/dm_rubylong_po.grf')
        print file_name
#        uid = None
#
#        if not uid:
#            uid = openerp.SUPERUSER_ID
#
#        if not dbname:
#            response = http.send_file(placeholder(imgname))
#        else:
#            try:
#                # create an empty registry
#                registry = openerp.modules.registry.Registry(dbname)
#                with registry.cursor() as cr:
#                    cr.execute("""SELECT c.logo_web, c.write_date
#                                    FROM res_users u
#                               LEFT JOIN res_company c
#                                      ON c.id = u.company_id
#                                   WHERE u.id = %s
#                               """, (uid,))
#                    row = cr.fetchone()
#                    if row and row[0]:
#                        image_data = StringIO(str(row[0]).decode('base64'))
#                        response = http.send_file(image_data, filename=imgname, mtime=row[1])
#                    else:
#                        response = http.send_file(placeholder('nologo.png'))
#            except Exception:
#                response = http.send_file(placeholder(imgname))
        file_name = 'C:/0-code/customer/actin/dmc_actin/static/dm_rubylong_po.grf'
        response = http.send_file(file_name)
        return response
# vim:expandtab:tabstop=4:softtabstop=4:shiftwidth=4:
