
{
    'name': 'DM Base',
    'version': '1.0',
    'category': 'Customization',
    'sequence': 1000,
    'summary': 'DMEMS Base',
    'description': """
DM Base
==================================
1.Remove “Your OpenERP is not supported” on screen top
2.add the option package
------------------------------------------------------
    """,
    'author': 'DMEMS',
    'website': 'http://www.dmems.com',
    'images': [],
    'depends': ['base','product','sale','purchase','account'],
    'data': [
        'security/ir.model.access.csv',
        'option_view.xml',
        ],
    'demo': [],
    'test': [],
    'js': ['static/src/js/announcement.js'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
