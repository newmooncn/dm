# -*- coding: utf-8 -*-

import simplejson
import time
import base64
import zlib
from openerp.addons.web.http import httprequest
from openerp.addons.web.controllers.main import content_disposition
from openerp.addons.web.controllers.main import Reports as WebReports

#add the object name to the download PDF file name, by johnw, 2013/12/29

@httprequest
def metro_rpt_index(self, req, action, token):
    action = simplejson.loads(action)

    report_srv = req.session.proxy("report")
    context = dict(req.context)
    context.update(action["context"])

    report_data = {}
    report_ids = context["active_ids"]
    if 'report_type' in action:
        report_data['report_type'] = action['report_type']
    if 'datas' in action:
        if 'ids' in action['datas']:
            report_ids = action['datas'].pop('ids')
        report_data.update(action['datas'])

    report_id = report_srv.report(
        req.session._db, req.session._uid, req.session._password,
        action["report_name"], report_ids,
        report_data, context)

    report_struct = None
    while True:
        report_struct = report_srv.report_get(
            req.session._db, req.session._uid, req.session._password, report_id)
        if report_struct["state"]:
            break

        time.sleep(self.POLLING_DELAY)

    report = base64.b64decode(report_struct['result'])
    if report_struct.get('code') == 'zlib':
        report = zlib.decompress(report)
    report_mimetype = self.TYPES_MAPPING.get(
        report_struct['format'], 'octet-stream')
    file_name = action.get('name', 'report')
    ''' comment by john 02/15/2014, to use new logic to get the file name
    if 'name' not in action:
        reports = req.session.model('ir.actions.report.xml')
        res_id = reports.search([('report_name', '=', action['report_name']),],
                                0, False, False, context)
        if len(res_id) > 0:
            #changed by johnw @02/15/2014, use the 'download_filename' field
            file_name = reports.read(res_id[0], ['name'], context)['name']
        else:
            file_name = action['report_name']
    '''     
    #new logic to get file name from ir_act_report_xml.download_filename
    #begin
    reports = req.session.model('ir.actions.report.xml')
    res_id = reports.search([('report_name', '=', action['report_name']),],
                            0, False, False, context)
    if len(res_id) > 0:
        names = reports.read(res_id[0], ['name','download_filename'], context)
        if names['download_filename']:
            file_name = names['download_filename']
        else:
            file_name = names['name']
    else:
        file_name = action['report_name']
    #end
                          
    #add the object name to the file name, by johnw, 2013/12/29
    try:
        #only print the name when print one record
        if context['active_ids']:
            model_obj = req.session.model(context['active_model'])
            #added by john, to call the object report name getting method to get the file name
            new_file_name = None
            try:
                new_file_name = model_obj.get_report_name(context['active_ids'][0],action['report_name'],context)  
            except AttributeError, e:
                pass
            except Exception, e:
                raise e
            if new_file_name:
                file_name = new_file_name
            if len(context['active_ids']) == 1:
                model_rec_name = model_obj.name_get(context['active_ids'],context)[0][1]            
                if model_rec_name:
                    #johnw, if the get_report_name returned full name then no need to add object name
                    file_name = '%s_%s' % (file_name, model_rec_name)
                
    except Exception:
        pass
    
    file_name = '%s.%s' % (file_name, report_struct['format'])

    return req.make_response(report,
         headers=[
             ('Content-Disposition', content_disposition(file_name, req)),
             ('Content-Type', report_mimetype),
             ('Content-Length', len(report))],
         cookies={'fileToken': token})
        
WebReports.index = metro_rpt_index

'''
Add the report download file name support
'''   
from osv import fields,osv,orm    
class ir_action_report_xml(osv.osv):
    _name="ir.actions.report.xml"
    _inherit ="ir.actions.report.xml"
    _columns={
        'download_filename' : fields.char('Download File Name',size=64),
    }
    