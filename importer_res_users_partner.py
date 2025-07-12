"""
Module: importer_res_users_partner
Description: Cleaned and documented version of importer_res_users_partner.py
"""

#   odoo shell -c informa.conf --no-http -d informa_eportfolio_prod

# python3.7 odoo-bin shell -d informa_eportfolio_prod

import odoo
import json
import os
import sys
#get current working directory
current_directory = os.getcwd()
# add your current working directory to sys.path, 
sys.path.insert(0, current_directory)
from import_export_eportfolio.common_function import *


db_name = 'informa_eportfolio_prod'
registry = odoo.registry(db_name)
cr = registry.cursor()
uid = int(odoo.tools.config.get('console_uid', odoo.SUPERUSER_ID))
odoo.api.Environment.reset()
ctx = odoo.api.Environment(cr, uid, {})['res.users'].context_get()
env = odoo.api.Environment(cr, uid, ctx)
self = env.user

# check these key values(create_uid, write_uid) are present in json data if not, set values to admin(2), which serve as(XW)
# or check if its res.users exist alearedy in db then based on it update records' create_uid, write_uid)
def uid_keys_value_from_data(model, key_id):
    global_data = load_global_data()
    co_model_data = model in global_data.keys() and global_data[model] or []
    co_model_values = {}
    create_or_write_uid = False
    # check if comodel with value vals is created or not
    co_model_values = get_co_model_values(co_model_data, key_id)
    
    if co_model_values:
        record_id = check_if_record_exists_or_create(model, co_model_values)
        if record_id:
            create_or_write_uid = record_id.id
    else:
        # this return record id does not exist any more in db( this happen if it was created and deleted then trying to access it.)
        base_domain = check_active_field_exists(model)
        base_domain = base_domain + [('login', '=', 'admin')]
        record_id = self.env['res.users'].search(base_domain)
        create_or_write_uid = record_id and record_id.id or 2
    return create_or_write_uid
   
# update records fields like create_uid, write_uid.....
# Note: create_uid and write_uid fields are not rewritable using odoo ORM, hence I used SQL query to update them
def update_res_user_uid_keys_fields(model, vals, record_id):
    res_keys = ['write_uid', 'create_uid']
    for key in res_keys:
        create_or_write_uid = False 
        if vals[key] == vals['id']: # when creater and write are equal to the id of its record
            create_or_write_uid = record_id.id
        else:
            create_or_write_uid = uid_keys_value_from_data(model, vals[key])
        table_name = model.replace('.', '_')
        if create_or_write_uid:
            self.env.cr.execute("update "+table_name + " set "+ key +" = %(value)s WHERE id in %(user_id)s",
                dict(value=create_or_write_uid, user_id=tuple(record_id.ids, )))
            """ self.env.cr.execute("update %s set %s = %(value)s WHERE id in %(user_id)s", table_name, key,
                dict(value=create_or_write_uid, user_id=tuple(record_id.ids, ))) """
            self.env.cr.commit()

#fn: update res.users and res.partners for each records
def upload_res_users_partner_data(model):
    global_data = load_global_data()
    for vals in global_data[model]:
        record_id = check_if_record_exists_or_create(model, vals)
        print('record_id...', record_id)
        if record_id:
            # fn: update records fields
            filter_vals = fields_to_update_records(model, vals)
            if model=='res.users' and 'password' in filter_vals.keys():
                del filter_vals['password']            
                record_id.write(filter_vals)
            self.env.cr.commit()
            # update one2many fields for res.users and res.partners records
            filter_one2m_fields = get_one2m_relational_field_vals(model, vals)
            if len(filter_one2m_fields)>0:
                create_one2m_relational_field_vals(model, filter_one2m_fields, record_id)
                self.env.cr.commit()
            if model=='res.partner':
                # field : commercial_partner_id was set to False during res.partner creation and here computed from it.
                # technical field used for managing commercial fields
                record_id._compute_commercial_partner()
                self.env.cr.commit()

# create or update res.users and res.partners records
res_models = ['res.users','res.partner']
for res_m in res_models:
    upload_res_users_partner_data(res_m)
            
#fn: update password values for res users
res_model = 'res.users'       
def update_res_users_password(res_model, vals):
    base_domain = check_active_field_exists(res_model)
    base_domain += [('login', '=', vals['login'])]
    res_id = self.env[res_model].search(base_domain)
    if res_id:
        res_users_psw = check_stored_password(res_id)
        if res_users_psw['password']!=vals['password']:
            if vals['password']:
                res_id.reset_pwd=False
                self.flush()
                self.env.cr.execute("update res_users set password = %(password)s WHERE id in %(user_id)s and login = %(login)s", 
                            dict(password=vals['password'], user_id=tuple(res_id.ids, ), login=vals['login']))
                print('updated...res_id password', res_id)
                self.env.cr.commit()

#fn: check stored password for user, since it is not possible to overwrite password with the same values
def check_stored_password(user_id):
    self.env.cr.execute("SELECT password FROM res_users WHERE id in %(user_id)s", 
                        dict(user_id=tuple(user_id.ids, )))
    res_users_psw = self.env.cr.dictfetchone()
    return res_users_psw

current_directory = os.getcwd()
final_directory = os.path.join(current_directory, r'import_export_eportfolio')
# loading users password and update users password in db
temp_psw = open(final_directory+'/'+('res_users_psw_data')+'.json', 'r')
user_psw_data = json.load(temp_psw)
for vals in user_psw_data:
    update_res_users_password(res_model, vals)

 #fn: update uid_keys for each res.users records
global_data = load_global_data()
model = 'res.users'
for apt_vals in global_data[model]:
    record_id = check_if_records_exists(model, apt_vals)
    if record_id:
        update_res_user_uid_keys_fields(model, apt_vals, record_id)
        self.env.cr.commit()   