# -*- coding: utf-8 -*-


#add the object name to the download PDF file name, by johnw, 2013/12/29

import simplejson
import base64
from openerp.addons.web.http import httprequest
from openerp.addons.web.controllers.main import content_disposition


'''
Fix the download binary file name issue
'''
from openerp.addons.web.controllers.main import Binary as WebBinary

@httprequest
def saveas_ajax(self, req, data, token):
    jdata = simplejson.loads(data)
    model = jdata['model']
    field = jdata['field']
    data = jdata['data']
    id = jdata.get('id', None)
    filename_field = jdata.get('filename_field', None)
    context = jdata.get('context', {})

    Model = req.session.model(model)
    fields = [field]
    if filename_field:
        fields.append(filename_field)
    if data:
        res = { field: data }
        #add the file name getting by johnw, 06/27/2014
        #begin
        if filename_field:
            res_filename = {}
            if id:
                res_filename = Model.read(int(id), [filename_field], context)
            else:
                res_filename = Model.default_get([filename_field], context)  
            if len(res_filename) > 0:
                res.update({filename_field:res_filename[filename_field]})          
        #end
    elif id:
        res = Model.read([int(id)], fields, context)[0]
    else:
        res = Model.default_get(fields, context)
    filecontent = base64.b64decode(res.get(field, ''))
    if not filecontent:
        raise ValueError(_("No content found for field '%s' on '%s:%s'") %
            (field, model, id))
    else:
        filename = '%s_%s' % (model.replace('.', '_'), id)
        if filename_field:
            filename = res.get(filename_field, '') or filename
        return req.make_response(filecontent,
            headers=[('Content-Type', 'application/octet-stream'),
                    ('Content-Disposition', content_disposition(filename, req))],
            cookies={'fileToken': token})
WebBinary.saveas_ajax = saveas_ajax
