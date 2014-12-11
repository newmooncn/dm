===================================
openerp/osv/orm.py
1)handle the message in Chinese for the db error
convert_pgerror_23505(),convert_pgerror_23502()

===================================
hr_evaluation/hr_evaluation_data.xml
1)Fix  the hr.employee creating issue using XML

===================================
hr_timesheet/hr_timesheet_data.xml
Remove the wrong data item in hr_timesheet_data.xml

===================================
web/static/src/js/view_list.js
Add the confirm dialog to the one2many list deletion

===================================
web/static/src/js/view_form.js
1)Remove the 'Create' and 'Create and Edit...' from many2one dropdown list
2)Add the 'select' check box on one2many field list view

===================================
mail/mail_mail.py
line#304, add 'raise e' to thow the exception to user

===================================
base/ir/ir_translation.py
1) Default is to overwrite the i18n
in ir_translation_import_cursor.__init__(), if no the 'overwrite' context parameter, change the default value to 'True'
And user need supply the 'overwrite_existing_translations = True' if want to change some old module's i18n, 
since the default value is False in openerp/tools/config.py
        group.add_option("--i18n-overwrite", dest="overwrite_existing_translations", action="store_true", my_default=False,
                         help="overwrites existing translation terms on updating a module or importing a CSV or a PO file.")

===================================
openerp.osv.expression.py
johnw, 12/10/2014, fix the searching under non-EN can not search the original name issue, 
like grouping searhing use group english name under CN GUI 
