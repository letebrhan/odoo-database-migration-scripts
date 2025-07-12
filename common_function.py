"""
Module: common_function
Description: Cleaned and documented version of common_function.py
"""

import odoo
import json
import os

db_name = 'informa_eportfolio_prod'
registry = odoo.registry(db_name)
cr = registry.cursor()
uid = int(odoo.tools.config.get('console_uid', odoo.SUPERUSER_ID))
odoo.api.Environment.reset()
ctx = odoo.api.Environment(cr, uid, {})['res.users'].context_get()
env = odoo.api.Environment(cr, uid, ctx)
self = env.user

def load_global_data():
    #get current working directory
    current_directory = os.getcwd()
    # add your current working directory to sys.path, 
    final_directory = os.path.join(current_directory, 'import_export_eportfolio')
    temp = open(final_directory+'/'+('all_exported_data')+'.json', 'r')
    global_data = json.load(temp)
    
    return global_data

# check if the given model contains active field
def check_active_field_exists(model_name):
    check_active = self.env[model_name]._fields.get('active', False)
    base_domain = check_active and [('active', 'in', [True, False])] or []
    
    return base_domain

# obtain if model or comodel_name has SQL unique constrains
def get_sql_contrains_domain(model, data):
    base_domain = []

    co_model_sql_constraints = [x for x in self.env[model]._sql_constraints]    
    if co_model_sql_constraints and co_model_sql_constraints[0][1] and ('unique' in co_model_sql_constraints[0][1] or 'UNIQUE' in co_model_sql_constraints[0][1]):
        co_model_constraints = co_model_sql_constraints[0][1]
        co_model_constraints = co_model_constraints.find('UNIQUE')!=-1 and co_model_constraints.replace('UNIQUE', 'unique') or co_model_constraints
        lst_to_be_replaced = {'unique ':'', 'unique': '', '(':'', ')': '', ' ':''}
        for key in lst_to_be_replaced.keys():
            co_model_constraints = co_model_constraints.replace(key, lst_to_be_replaced[key])
        co_model_constraints = co_model_constraints.split(',')
        if model == 'slide.quiz.score.range' and 'slide_id' in data.keys():
            print('model...', model, '..constrain slide_id.')
            # check if the slide created first or if not create it
            global_data = load_global_data()
            slide_id_data = {}
            if data and type(data)==tuple:
                data = data[0]
            for vals in global_data['slide.slide']:
                if 'id' in vals.keys() and vals['id']==data['slide_id']:
                    slide_id_data = vals
            if slide_id_data:
                slide_id = check_if_record_exists_or_create('slide.slide', slide_id_data)
                slide_id = slide_id and slide_id.id
            else:
                slide_id = data['slide_id']
            base_domain = [('range_upto', '=', data['range_upto']), ('slide_id', '=', slide_id)]
        else:
            for tup in co_model_constraints:
                base_domain.append((tup, '=', data[tup]))
            
    return base_domain


# get all fields excluding field types in ['many2one', 'one2many', 'many2many', 'binary'] or
# field values not [Null, False] or fields not automatically created
def get_normal_fields_data(model, data):
    if model in ['res.users', 'res.partner']:
        data = {name:value for name, value in data.items() 
            if (value not in [False, []] and
                self.env[model]._fields.get(name) is not None and
                self.env[model]._fields.get(name).automatic is False and
                len(self.env[model]._fields.get(name).depends)==0 and 
                self.env[model]._fields.get(name).type not in ['many2one', 'one2many', 'many2many', 'binary'])}
    else:
        data = {name:value for name, value in data.items() 
                if (value not in [False, [], ''] and
                    self.env[model]._fields.get(name) is not None and
                    self.env[model]._fields.get(name).required and 
                    self.env[model]._fields.get(name).automatic is False and
                    self.env[model]._fields.get(name).type not in ['many2one', 'one2many', 'many2many', 'binary'])} \
                or {name:value for name, value in data.items() 
                    if (value not in [False, [], ''] and
                        self.env[model]._fields.get(name) is not None and
                        self.env[model]._fields.get(name).store and
                        self.env[model]._fields.get(name).automatic is False and
                        self.env[model]._fields.get(name).type not in ['many2one', 'one2many', 'many2many', 'binary'])}
    return data

def get_normal_fields_data_old(model, data):
    data = {name:value for name, value in data.items() 
            if (value not in [False, []] and
                self.env[model]._fields.get(name) is not None and
                self.env[model]._fields.get(name).automatic is False and
                len(self.env[model]._fields.get(name).depends)==0 and  # odoo field attribute depends=
                self.env[model]._fields.get(name).type not in ['many2one', 'one2many', 'many2many', 'binary'])}
    return data

# obtain if model or comodel_name has SQL unique constrains for res_users/res_partner
def get_res_users_res_partner_constrains(model, data):
    data = get_normal_fields_data(model, data)
    base_domain = check_active_field_exists(model)
    if data:
        if model == 'res.partner' and 'fiscalcode' in data.keys():
            fiscalcode = data['fiscalcode']
            # user's fiscalcode in production db are in upper case, 
            # check if fiscalcode in elearning are in lower case and convert them to upper, 
            # then look if this fiscalcode user already present in production db, 
            # if it is not present create it
            if fiscalcode.islower():
                base_domain.append(('fiscalcode', 'in', [fiscalcode, fiscalcode.upper()]))
            else:
                base_domain.append(('fiscalcode', '=', fiscalcode))
        if model == 'res.users' and 'login' in data.keys():
                base_domain.append(('login', '=', data['login']))                
    return base_domain

# get nomal fields/m2o and m2m domain as tuple
def get_normal_fields_domain(model, values):
    base_domain = check_active_field_exists(model)
    data = get_normal_fields_data(model, values)
    
    record_vals = {}
    # if data empty(means domain going to be empty) 
    # or if the model is in the ff groups,  get domains as m2one and m2m fields if available
    if not data or model in ['experience.type.details', 'summary.slide.mapping', 
                             'tag.instrument', 'rating.rating', 'skill.level.mapping']:
        ftr_data = fields_to_update_records(model, values)
        data = ftr_data
        record_vals.update(data)
        clean_data = {}
        clean_data.update(data)
        if model !='rating.rating':
            for key in data.keys():
                if self.env[model]._fields.get(key) is not None and len(self.env[model]._fields.get(key).depends)>0:
                    del clean_data[key]
        data = clean_data
    if data:  
        for key in data.keys():
            # check if field values are tuple or not and set subtable keys and values for domain
            key_value = (data[key] and type(data[key])== list and type(data[key][0]) == tuple) and data[key][0][2] or data[key]
            if data[key] and type(data[key])==list and type(data[key][0]) == tuple:
                base_domain.append((key, 'in', key_value))
            else:
                base_domain.append((key, '=', key_value))

    return base_domain, record_vals

# fn: filter all fields including field types in ['many2one', 'one2many', 'many2many', 'binary'] and
# field values not Null or fields not automatically created
def get_m2one_m2m_relational_field_vals(model, vals):
    rel_field_vals = {name:value for name, value in vals.items() 
                        if (value not in [False, []] and
                            self.env[model]._fields.get(name) is not None and 
                            self.env[model]._fields.get(name).store and 
                            self.env[model]._fields.get(name).automatic is False and
                        self.env[model]._fields.get(name).type in ['many2one', 'many2many'])}
    if model == 'res.partner' and 'commercial_partner_id' in rel_field_vals.keys(): # technical field used for managing commercial fields fields.Many2one('res.partner') is computed and stored field
        rel_field_vals['commercial_partner_id'] = False
    if rel_field_vals:
        vals = create_m2one_m2m_relational_fields(model, vals, rel_field_vals)
        
    return vals

#fn: create relational fields (many2one and many2many)
def create_m2one_m2m_relational_fields(model, f_vals, rel_field_vals):
    for rel_key in rel_field_vals.keys(): 
        global_data = load_global_data()
        comodel_name = self.env[model]._fields.get(rel_key).comodel_name
        co_model_data = comodel_name in global_data.keys() and global_data[comodel_name] or []
        many2one = self.env[model]._fields.get(rel_key).type == 'many2one'
        many2many = self.env[model]._fields.get(rel_key).type == 'many2many'
        if co_model_data:
            if many2one:           
                # create many2one comodels     
                if rel_key in ['write_uid', 'create_uid'] and rel_field_vals[rel_key] in [1, 2, False]:
                    f_vals[rel_key] = rel_field_vals[rel_key]
                if rel_key in ['write_uid', 'create_uid'] and rel_field_vals[rel_key] not in [1, 2, False]:
                    f_vals[rel_key] = False
                else:
                    record_id = False
                    if rel_field_vals[rel_key]:
                        record_id = create_many2one_comodel(comodel_name, rel_field_vals[rel_key])
                    f_vals[rel_key] = record_id and record_id.id or False
            if many2many:   
                # create many2many comodels  res.partner
                elearning_res_partner_m2m_ids = ['slide_channel_ids', 'formative_experience', 'working_experience', 'extra_experience', 
				'flipcard_slide_mapping_ids', 'skill_ids', 'tag_ids', 'summary_ids'] # remove recursive looping
                many2many_ids = False
                if model =='res.partner' and rel_key in elearning_res_partner_m2m_ids:
                     f_vals[rel_key] = many2many_ids
                else:
                    if rel_field_vals[rel_key] not in [False, []]:
                        # check co_model_values already created
                        many2many_ids = create_many2many_comodel(comodel_name, rel_field_vals[rel_key])
                        f_vals[rel_key] = many2many_ids not in [False, []] and [(6, 0, many2many_ids)] or False
        else:
            if many2one:
                if comodel_name=='ir.model' and model == 'rating.rating':
                    res_model_id = self.env[comodel_name].search([('model', '=', f_vals['res_model'])])
                    f_vals[rel_key] = res_model_id and res_model_id.id or False
                    res_id = self.env[f_vals['res_model']].search([('name', '=', f_vals['res_name'])])
                    if res_id:
                        f_vals['res_id'] = res_id and res_id.id                        
                    else:
                        #if res_model was not created, then filter its data from json and create it
                        co_model_data = f_vals['res_model'] in global_data.keys() and global_data[f_vals['res_model']] or []
                        co_model_values = get_co_model_values_by_name(co_model_data, f_vals['res_name'])
                        record_id = check_if_record_exists_or_create(f_vals['res_model'], co_model_values)
                        f_vals['res_id'] = record_id and record_id.id 
                else:
                    f_vals[rel_key] = rel_field_vals[rel_key]
            if many2many:
                many2many_vals = False
                if rel_field_vals[rel_key] not in [False, []]:
                    many2many_vals = type(rel_field_vals[rel_key][0])==tuple and rel_field_vals[rel_key] or [(6, 0, rel_field_vals[rel_key])]
                f_vals[rel_key] = many2many_vals
        
    return f_vals

# get dictionary by record name
def get_co_model_values_by_name(co_model_data, name):
    co_model_values = {}
    if co_model_data:
        for v in co_model_data:
            if 'name' in v.keys() and v['name']==name:
                co_model_values.update(v)
    return co_model_values

# obtain dictionary filtering by record id
def get_co_model_values(co_model_data, rel_field_vals):
    co_model_values = {}
    if co_model_data:
        for v in co_model_data:
            if 'id' in v.keys() and v['id']==rel_field_vals:
                co_model_values.update(v)
    return co_model_values
   
#fn: create many2one comodels
def create_many2one_comodel(comodel_name, rel_field_vals):
    global_data = load_global_data()
    co_model_data = comodel_name in global_data.keys() and global_data[comodel_name] or []
    record_id = False
    co_model_values = get_co_model_values(co_model_data, rel_field_vals)
    if co_model_values:
        record_id = check_if_record_exists_or_create(comodel_name, co_model_values)
    else:
        base_domain = check_active_field_exists(comodel_name)
        record_id = self.env[comodel_name].search(base_domain + [('id', '=', rel_field_vals)], limit=1)
        if not record_id and comodel_name =='res.users':
            base_domain = base_domain + [('login', '=', 'admin')]
            record_id = self.env['res.users'].search(base_domain, limit=1)
            
    return record_id
            
#fn: create many2many comodels
def create_many2many_comodel(comodel_name, m2m_ids):
    global_data = load_global_data()
    co_model_data = comodel_name in global_data.keys() and global_data[comodel_name] or []
    new_m2m_ids = []
    many2many_ids = (m2m_ids and type(m2m_ids)== list and type(m2m_ids[0]) == tuple) and m2m_ids[0][2] or m2m_ids
    if comodel_name in global_data.keys() and not (m2m_ids and type(m2m_ids)== list and type(m2m_ids[0]) == tuple):
        for m2m in m2m_ids:
            co_model_values = get_co_model_values(co_model_data, m2m) 
            if co_model_values:
                record_id = check_if_record_exists_or_create(comodel_name, co_model_values)
                if record_id:
                    new_m2m_ids.append(record_id.id)
            else:
                base_domain = check_active_field_exists(comodel_name)
                record_id = self.env[comodel_name].search(base_domain + [('id', '=', m2m)], limit=1)
                if record_id:
                    new_m2m_ids.append(record_id.id)
                if not record_id and comodel_name =='res.users':
                    base_domain = base_domain + [('login', '=', 'admin')]
                    record_id = self.env['res.users'].search(base_domain, limit=1)
                    if record_id:
                        new_m2m_ids.append(record_id.id)                    
            self.env.cr.commit()
    else:
        new_m2m_ids = many2many_ids
    return new_m2m_ids

# fn: obtain one2many relational fields data
def get_one2m_relational_field_vals(model, vals):
    
    vals = {name:value for name, value in vals.items() 
                        if (value not in [False, []] and
                            self.env[model]._fields.get(name) is not None and 
                            self.env[model]._fields.get(name).automatic is False and
                            self.env[model]._fields.get(name).type =='one2many')}
    return vals

#fn: create one2many relational fields
def create_one2m_relational_field_vals(model, filter_one2m_fields, record_id):
    global_data = load_global_data()
    for key in filter_one2m_fields.keys():
        comodel_name = self.env[model]._fields.get(key).comodel_name
        inverse_name = self.env[model]._fields.get(key).inverse_name
        co_model_data = comodel_name in global_data.keys() and global_data[comodel_name] or [] 
        if comodel_name in global_data.keys():
            create_one2many_comodel(co_model_data, comodel_name, inverse_name, record_id, filter_one2m_fields[key])
            self.env.cr.commit()
        self.env.cr.commit()

#fn: create one2many_comodels
def create_one2many_comodel(co_model_data, comodel_name, inverse_name, record_id, old_one2many_ids):

    for one2m in old_one2many_ids:
        co_model_values = get_co_model_values(co_model_data, one2m)
        if co_model_values:
            co_model_values[inverse_name] = record_id.id
            inverse_record_id = check_if_record_exists_or_create(comodel_name, co_model_values)
            # Update inverse_record_id[inverse_name] value to record_id.id it was not updated.   
            if comodel_name not in ['res.users', 'res.partner']:
                filter_vals = fields_to_update_records(comodel_name, co_model_values)
                if comodel_name=='slide.slide': # 'website_published' is handled by mixin in  backend, but here managed as follow
                    filter_vals['website_published'] = ('is_published' in filter_vals.keys() and filter_vals['is_published']) and filter_vals['is_published'] or False
                inverse_record_id.write(filter_vals)
                self.env.cr.commit()
        else:
            base_domain = check_active_field_exists(comodel_name)
            inverse_record_id = self.env[comodel_name].search(base_domain + [('id', '=', one2m)], limit=1)
            if inverse_record_id:
                inverse_record_id[inverse_name] = record_id.id
            if not inverse_record_id and comodel_name =='res.users':
                base_domain = base_domain + [('login', '=', 'admin')]
                inverse_record_id = self.env['res.users'].search(base_domain, limit=1)
                if inverse_record_id:
                    inverse_record_id[inverse_name] = record_id.id

        self.env.cr.commit()
            
#fn: main function create records
def main_create_records(model, vals):
    vals = get_m2one_m2m_relational_field_vals(model, vals)
    if model == 'slide.quiz.score.range':
        filter_vals = clean_automatice_fields(vals)
    else:
        # also cleaned automatic created fields during filtering with this ff function
        filter_vals = filter_all_field_without_one2m_relational(model, vals)
    if filter_vals and not(len(filter_vals)==1 and list(filter_vals.values())[0] in [False, '']):
        if model=='slide.slide':
            filter_vals['website_published'] = ('is_published' in filter_vals.keys() and filter_vals['is_published']) and filter_vals['is_published'] or False
        record_id = self.env[model].create(filter_vals)      
        self.env.cr.commit()
        
        return record_id
    
#fn: update records fields or create if not exists
def fields_to_update_records(model, record_vals):
    apt_data = get_m2one_m2m_relational_field_vals(model, record_vals)
    clean_data =  clean_automatice_fields(apt_data)
    filter_vals = filter_all_field_without_one2m_relational(model, clean_data)
         
    return filter_vals
#fn: Check if records already exists
def check_if_records_exists(comodel_name, co_model_values):
    if comodel_name in ['res.partner', 'res.users']:
        base_domain =  get_res_users_res_partner_constrains(comodel_name, co_model_values)
    else:
        # First check if model has unique sql constrains defined
        sql_contrains_domain = get_sql_contrains_domain(comodel_name, co_model_values)
        if sql_contrains_domain:
            base_domain = check_active_field_exists(comodel_name)
            base_domain += sql_contrains_domain
        else:
            # else check if model has other constrains defined
            if 'date_published' in co_model_values.keys():
                del co_model_values['date_published']
            base_domain, record_vals = get_normal_fields_domain(comodel_name, co_model_values)
    record_id = base_domain and self.env[comodel_name].search(base_domain, limit=1) or False
    
    return record_id
    
#fn: check if record created based on domain, if it is not created create it
def check_if_record_exists_or_create(comodel_name, co_model_values):
    record_vals = {}
    record_id=False
    if comodel_name in ['res.partner', 'res.users']:
        base_domain =  get_res_users_res_partner_constrains(comodel_name, co_model_values)
    else:
        # First check if model has unique sql constrains defined
        sql_contrains_domain = get_sql_contrains_domain(comodel_name, co_model_values)
        if sql_contrains_domain:
            base_domain = check_active_field_exists(comodel_name)
            base_domain += sql_contrains_domain
        else:
            # else check if model has other constrains defined
            if 'date_published' in co_model_values.keys():
                del co_model_values['date_published']
            base_domain, record_vals = get_normal_fields_domain(comodel_name, co_model_values)
    record_id = base_domain and self.env[comodel_name].search(base_domain, limit=1) or False
    
    if not record_id:
        print('record_id...not created...', record_id, 'model/comodel_name...', comodel_name)
        if comodel_name !='rating.rating' and record_vals:
            record_id = self.env[comodel_name].create(record_vals)
            self.env.cr.commit()
        else:
            #Check dict(single) if it keys contain value then call the create function
            if co_model_values and not(len(co_model_values)==1 and list(co_model_values.values())[0] in [False, '']):
                record_id = main_create_records(comodel_name, co_model_values)
    else:
        print('record_id already created ', record_id)

    return record_id

#fn: filter all fields excluding one2many relational fields
def filter_all_field_without_one2m_relational(model, vals):
    check_active = self.env[model]._fields.get('active', False)
    if check_active:
        active = vals['active'] # First Remove from dict, and filter fields having value, stored and not automatically created.
    
    vals = {name:value for name, value in vals.items() 
                if ((value not in [False, [], '']) and
                    self.env[model]._fields.get(name) is not None and 
                    self.env[model]._fields.get(name).store and 
                    self.env[model]._fields.get(name).automatic is False and
                    self.env[model]._fields.get(name).type not in ['one2many'])}
    if check_active:
        vals['active'] = active
        
    return vals

#fn: remove automatically created fields from domain fields
def clean_automatice_fields(vals):
        
    if 'create_date' in vals.keys():
        del vals['create_date']
    if 'write_date' in vals.keys():
        del vals['write_date']
    if 'id' in vals.keys():
        del vals['id']
    if 'date_published' in vals.keys():
        del vals['date_published']
    
    return vals 


#fn: general function to upload records data
def upload_record_data(model):
    global_data = load_global_data()
    for rec_vals in global_data[model]:
        record_id = check_if_record_exists_or_create(model, rec_vals)
        if record_id and model not in ['slide.channel']:
            filter_one2m_fields = get_one2m_relational_field_vals(model, rec_vals)
            if len(filter_one2m_fields) > 0:
                create_one2m_relational_field_vals(model, filter_one2m_fields, record_id)
                self.env.cr.commit()
                
#fn: filter specicif fields like (uid_keys, or elearning_res_partner_m2m_ids or other) to be updated for each records
def filter_creator_modifier_res_user(model, vals, filter_keys):
    rel_field_vals = {k:v for k,v in vals.items() if k in filter_keys and 
                      self.env[model]._fields.get(k) is not None and 
                      v not in [False, []]}
    apt_vals = {}
    if rel_field_vals:
        apt_vals = create_m2one_m2m_relational_fields(model, rel_field_vals, rel_field_vals)
        self.env.cr.commit()
    return apt_vals
   
# fn: update records fields like create_uid, write_uid using query
# Note: create_uid and write_uid fields are not rewritable using odoo ORM, hence I used SQL query to update them
def update_on_tables_key_uids_fields(model, vals, record_id):
    table_name = model.replace('.', '_')
    # keys to create or update users uid for res.partners and other records 
    uid_keys = ['write_uid', 'create_uid']
    # filter and check user creater or modifier (uid_keys vals) already exists or create
    uid_vals = filter_creator_modifier_res_user(model, vals, uid_keys)
    # user creator or modifiers already created, should be updated for each models record creator except res.users records
    print('model...', model, '....uid_vals...', uid_vals)
    if uid_vals:
        for key in uid_keys:
            if key in uid_vals.keys() and uid_vals[key]!= False:
                self.env.cr.execute("update "+table_name + " set "+ key +" = %(value)s WHERE id in %(user_id)s",
                    dict(value=uid_vals[key], user_id=tuple(record_id.ids, )))
                self.env.cr.commit()

#fn: update all records creator and modifiers fields(uid_keys create_uid and write_uid) 
# for all model records except res.users fields(create_uid and write_uid) xw
def update_records_key_uid_fields_xw(model):
    global_data = load_global_data()
    for apt_vals in global_data[model]:
        record_id = check_if_records_exists(model, apt_vals)
        if record_id:
            #fn: update uid_keys for each records
            update_on_tables_key_uids_fields(model, apt_vals, record_id)
        self.flush()
        

# fn: update records data except res.users data and uids fields(creator and modifier)
def update_general_record_fields(model):
    global_data = load_global_data()
    for vals in global_data[model]:
        record_id = check_if_records_exists(model, vals)
        if record_id and model!='slide.channel.partner':
            filter_vals = fields_to_update_records(model, vals)
            if model=='slide.slide': # 'website_published' is handled by mixin in  backend, but here managed as follow
                filter_vals['website_published'] = ('is_published' in filter_vals.keys() and filter_vals['is_published']) and filter_vals['is_published'] or False
            record_id.write(filter_vals)
            self.env.cr.commit()
        self.flush()
