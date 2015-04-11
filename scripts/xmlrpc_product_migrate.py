#!/usr/bin/python
import sys, getopt
import xmlrpclib
'''
host = raw_input('Enter openerp host name : ')
port = raw_input('Enter openerp host port : ')
dbname = raw_input('Enter database name : ')

if dbname == 'metro_production':
    print('Can not perform operation on this database')
    sys.exit(0)

username = raw_input('Enter user name : ')
pwd = raw_input('Enter password : ')
'''
host = 'localhost'
port = '8069'
dbname_from = 'aotai_0411'
username = 'admin'
pwd_from = '155412_test'
sock_common = xmlrpclib.ServerProxy ('http://%s:%s/xmlrpc/common'%(host,port))
uid_from = sock_common.login(dbname_from, username, pwd_from)
sock_from = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/object'%(host,port))

host = 'localhost'
port = '9069'
dbname_to = 'dm70_new_aotai'
username = 'admin'
pwd_to = 'admin'
sock_common = xmlrpclib.ServerProxy ('http://%s:%s/xmlrpc/common'%(host,port))
uid_to = sock_common.login(dbname_to, username, pwd_to)
sock_to = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/object'%(host,port))

ids = sock_from.execute(dbname_from, uid_from, pwd_from, 'product.product', 'search', [])
cnt = len(ids)
cnt_done = 0
exist_ids = []
'''
Before do the transfer, the customre, supplier and product category should be finished setup
'''
for id in ids:
    if id in exist_ids:
        cnt_done += 1
        print '%s of %s, existing id:%s'%(cnt_done,  cnt, id)
        continue
    prod_from = sock_from.execute(dbname_from, uid_from, pwd_from, 'product.product', 'read', id)
    exist_prod_ids = sock_to.execute(dbname_to, uid_to, pwd_to, 'product.product', 'search', [('default_code','=',prod_from['default_code'])])
    if exist_prod_ids:
        cnt_done += 1
        print '%s    %s, %s of %s, existing id:%s'%(id, prod_from['code'], cnt_done,  cnt, exist_prod_ids[0])
        continue
    
    #get category_id
    categ_name = sock_from.execute(dbname_from, uid_from, pwd_from, 'product.category', 'read', prod_from['categ_id'][0], ['name'])['name']
    categ_id = sock_to.execute(dbname_to, uid_to, pwd_to, 'product.category', 'search', [('name','=',categ_name)])[0]
    #uom_categ_id
    uom_categ_ids = sock_to.execute(dbname_to, uid_to, pwd_to, 'product.uom.categ', 'search', [('name','=',prod_from['uom_categ_id'][1])])
    if not uom_categ_ids:
        uom_categ_data = sock_from.execute(dbname_from, uid_from, pwd_from, 'product.uom.categ', 'read', prod_from['uom_categ_id'][0])
        uom_categ_id = sock_to.execute(dbname_to, uid_to, pwd_to, 'product.uom.categ', 'create', uom_categ_data)
    else:
        uom_categ_id = uom_categ_ids[0]
    #uom_id
    uom_data = sock_from.execute(dbname_from, uid_from, pwd_from, 'product.uom', 'read', prod_from['uom_id'][0])
    uom_ids = sock_to.execute(dbname_to, uid_to, pwd_to, 'product.uom', 'search', [('name','=',prod_from['uom_id'][1]),('category_id','=',uom_categ_id)])
    if not uom_ids:
        uom_data['category_id'] = uom_categ_id
        uom_id = sock_to.execute(dbname_to, uid_to, pwd_to, 'product.uom', 'create', uom_data)
    else:
        uom_id = uom_ids[0]
    #uom_po_id
    if prod_from['uom_id'][0] == prod_from['uom_po_id'][0]:
        uom_po_id = uom_id
    else:
        uom_po_data = sock_from.execute(dbname_from, uid_from, pwd_from, 'product.uom', 'read', prod_from['uom_po_id'][0])
        uom_po_ids = sock_to.execute(dbname_to, uid_to, pwd_to, 'product.uom', 'search', [('name','=',prod_from['uom_po_id'][1]),('category_id','=',uom_categ_id)])
        if uom_po_ids:
            uom_po_id = uom_po_ids[0]
        else:
            uom_po_data['category_id'] = uom_categ_id
            uom_po_id = sock_to.execute(dbname_to, uid_to, pwd_to, 'product.uom', 'create', uom_po_data)
    
    #create product
    prod_to = {'categ_id':categ_id, 
               'default_code':prod_from['default_code'],
               'name':prod_from['name'],
               'part_no_external':prod_from['part_no_external'],
               'supply_method':prod_from['supply_method'],
               'purchase_ok':prod_from['purchase_ok'],
               'sale_ok':prod_from['sale_ok'],
               'description':prod_from['description'],
               'measure_type':prod_from['measure_type'],
               'uom_categ_id':uom_categ_id,
               'uom_id':uom_id,
               'uom_po_id':uom_po_id,}
    new_prod_id = uom_id = sock_to.execute(dbname_to, uid_to, pwd_to, 'product.product', 'create', prod_to)
    #create product supplier info
    if prod_from.get('seller_ids'):
        for prodseller_id in prod_from.get('seller_ids'):
            prodseller_data = sock_from.execute(dbname_from, uid_from, pwd_from, 'product.supplierinfo', 'read', prodseller_id, ['name','product_code','product_name'])
            if prodseller_data['name']:
                prodseller_code = sock_from.execute(dbname_from, uid_from, pwd_from, 'res.partner', 'read', prodseller_data['name'][0], ['code'])['code']
                seller_id = sock_to.execute(dbname_to, uid_to, pwd_to, 'res.partner', 'search', [('code','=',prodseller_code)])[0]
                prodseller_data={'name':seller_id, 'product_product_id':new_prod_id,
                                    'product_code': prodseller_data['product_code'],
                                    'product_name': prodseller_data['product_name']}
                sock_to.execute(dbname_to, uid_to, pwd_to, 'product.supplierinfo', 'create', prodseller_data)        
    #create product customer info
    if prod_from.get('customer_ids'):
        for prodcustomer_id in prod_from.get('customer_ids'):
            prodcustomer_data = sock_from.execute(dbname_from, uid_from, pwd_from, 'product.customerinfo', 'read', prodcustomer_id, ['name','product_code','product_name'])
            if prodcustomer_data['name']:
                prodcustomer_code = sock_from.execute(dbname_from, uid_from, pwd_from, 'res.partner', 'read', prodcustomer_data['name'][0], ['code'])['code']
                customer_id = sock_to.execute(dbname_to, uid_to, pwd_to, 'res.partner', 'search', [('code','=',prodcustomer_code)])[0]
                prodcustomer_data={'name':customer_id, 'product_product_id':new_prod_id,
                                    'product_code': prodcustomer_data['product_code'],
                                    'product_name': prodcustomer_data['product_name']}
                sock_to.execute(dbname_to, uid_to, pwd_to, 'product.customerinfo', 'create', prodcustomer_data)
    cnt_done += 1
    print '%s    %s, %s of %s, new id:%s'%(id, prod_from['code'], cnt_done,  cnt, new_prod_id)

print 'done...'