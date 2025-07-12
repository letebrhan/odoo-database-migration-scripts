"""
Module: importer_frontend_others
Description: Cleaned and documented version of importer_frontend_others.py
"""

#   odoo shell -c informa.conf --no-http -d informa_eportfolio_prod

# python3.7 odoo-bin shell -d informa_elearning_prod

import odoo
import json
import os
import sys
#get current working directory
current_directory = os.getcwd()
# add your current working directory to sys.path, 
sys.path.insert(0, current_directory)
from import_export_eportfolio.common_function import upload_record_data, \
update_general_record_fields, update_records_key_uid_fields_xw, load_global_data,\
check_if_record_exists_or_create, filter_creator_modifier_res_user, check_active_field_exists, update_on_tables_key_uids_fields
db_name = 'informa_eportfolio_prod'
registry = odoo.registry(db_name)
cr = registry.cursor()
uid = int(odoo.tools.config.get('console_uid', odoo.SUPERUSER_ID))
odoo.api.Environment.reset()
ctx = odoo.api.Environment(cr, uid, {})['res.users'].context_get()
env = odoo.api.Environment(cr, uid, ctx)
self = env.user

global_data = load_global_data()
# lists of models to be created
config_model_names = ['value.master', 'rating.values', 'slide.tag', 
                      'formative.experience.level', 'experience.frequency', 
                      'experience.master', 'tag.master', 'skill.master', 'skill.type',
                      'ciofs.elearning.ratings', 'experience.type.details', 'rating.rating']

course_sub_course_models = ['slide.channel', 'slide.slide', 'slide.channel.partner', 'slide.channel.invite']
res_models = ['res.users', 'res.partner']

# filter front end record data
frontend_others_model_names = {k:v for k,v in global_data.items() 
                               if k not in config_model_names + course_sub_course_models + res_models}
                            
frontend_others_model_names = list(frontend_others_model_names.keys())
# create frontend models data
for frontend_mod in frontend_others_model_names:
    upload_record_data(frontend_mod)


# update many2many fields of elearning res.partner records
def update_res_partner_elearning_field():
    global_data = load_global_data()
    elearning_res_partner_m2m_ids = ['slide_channel_ids', 'formative_experience', 'working_experience', 'extra_experience', 
    'flipcard_slide_mapping_ids', 'skill_ids', 'tag_ids', 'summary_ids'] 
    model = 'res.partner'
    for f_vals in global_data[model]:
        record_id = check_if_record_exists_or_create(model, f_vals)
        if record_id:            
            #fn: filter elearning_res_partner_m2m_ids to be updated for each res.partner records
            el_vals = filter_creator_modifier_res_user(model, f_vals, elearning_res_partner_m2m_ids)
            if el_vals:
                record_id.write(el_vals)
                self.env.cr.commit()
update_res_partner_elearning_field()

# filter models to update all frontend_others_model_names models data + res.partner
# also to update create_uid and write_uid xw 
for apt_uid_mod in frontend_others_model_names + ['res.partner']:
    update_general_record_fields(apt_uid_mod)
    update_records_key_uid_fields_xw(apt_uid_mod)

# 21-08-2024: autoclean slide_channel_partner values 
def clean_slide_channel_partner(vals):
    if 'create_date' in vals.keys():
        del vals['create_date']
    if 'write_date' in vals.keys():
        del vals['write_date']
    if 'channel_id' in vals.keys():
        del vals['channel_id']
    if 'partner_id' in vals.keys():
        del vals['partner_id']
    if 'id' in vals.keys():
        del vals['id']
    
    return vals 
       
# 21-08-2024: update many2many relational table(slide.channel.partner()) records, 
# where the automatic fields (channel_id, and partner_id) added to this tabel during creating courses
# Note: this table is required to update because, 
# in addition to the automatic fields (channel_id, and partner_id) created during creating courses, 
# there are other fields(create_uid, write_uid, completed, completion) exported and need to be updated from file
def update_slide_channel_partner():
    global_data = load_global_data()
    channel_data = global_data['slide.channel']
    res_partner_data = global_data['res.partner']
    res_model_sc_partner = 'slide.channel.partner'
    global_data = load_global_data()
    for sc_partner_vals in global_data[res_model_sc_partner]:
        # filter channel_id record data and check if this channel_id exists or create it
        channel_vals = [val for val in channel_data if val['id']==sc_partner_vals['channel_id']][0]
        channel_record_id = check_if_record_exists_or_create('slide.channel', channel_vals)
        
        # filter partner_id record data and check if this partner_id exists or create it
        partner_vals = [val for val in res_partner_data if val['id']==sc_partner_vals['partner_id']]
        partner_record_id = False
        if not partner_vals:
            base_domain = check_active_field_exists('res.partner')
            base_domain = base_domain + [('id', '=', sc_partner_vals['partner_id'])]
            partner_record_id = self.env['res.partner'].search(base_domain, limit=1)
        else:
            partner_record_id = check_if_record_exists_or_create('res.partner', partner_vals[0])
        # update sc_partner_vals channel_id and  partner_id values 
        sc_partner_vals['channel_id']=channel_record_id.id 
        sc_partner_vals['partner_id']=partner_record_id.id 
        # check if sc_partner_vals record exists or create 
        record_id = self.env[res_model_sc_partner].search([('channel_id', '=', channel_record_id.id),
                                                        ('partner_id', '=', partner_record_id.id)])
        if not record_id:
            #fn: update uid_keys for each records
            record_id = self.env[res_model_sc_partner].create(sc_partner_vals)
            continue
        filter_sc_vals = clean_slide_channel_partner(sc_partner_vals)
        record_id.write(filter_sc_vals)
        self.flush()
        self.env.cr.commit()
        update_on_tables_key_uids_fields(res_model_sc_partner, sc_partner_vals, record_id)
        
update_slide_channel_partner()