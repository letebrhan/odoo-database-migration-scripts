"""
Module: importer_course_config_data
Description: Cleaned and documented version of importer_course_config_data.py
"""

#   odoo shell -c informa.conf --no-http -d informa_eportfolio_prod

# python3.7 odoo-bin shell -d informa_eportfolio_prod

# python3.7 -c informa.conf --no-http -d informa_eportfolio_prod
# OCB13/odoo-bin shell -c ciofs-fp.informa/informa.conf --no-http -d informa_eportfolio

import odoo
import json
import os
import sys
#get current working directory
current_directory = os.getcwd()
# add your current working directory to sys.path, 
sys.path.insert(0, current_directory)

from import_export_eportfolio.common_function import upload_record_data, update_general_record_fields, update_records_key_uid_fields_xw
db_name = 'informa_eportfolio_prod'
registry = odoo.registry(db_name)
cr = registry.cursor()
uid = int(odoo.tools.config.get('console_uid', odoo.SUPERUSER_ID))
odoo.api.Environment.reset()
ctx = odoo.api.Environment(cr, uid, {})['res.users'].context_get()
env = odoo.api.Environment(cr, uid, ctx)
self = env.user
    
# create configuration models and others
config_model_names = ['value.master', 'rating.values', 'slide.tag', 
                      'formative.experience.level', 'experience.frequency', 
                      'experience.master', 'tag.master', 'ciofs.elearning.ratings',
                      'experience.type.details', 'rating.rating']
for config_mod in config_model_names:
    upload_record_data(config_mod)

sub_config_model_names = ['skill.master', 'skill.type']
for mod in sub_config_model_names:
    upload_record_data(mod)
    
# First create sub course contents data record models
sub_course_contents = ['slide.channel', 'slide.slide', 'slide.channel.invite'] # 'slide.channel.partner', 
for sub_course_mod in sub_course_contents:
    upload_record_data(sub_course_mod)

# filter models to update all config_model_names + sub_course_contents models data
# also to update create_uid and write_uid xw 
all_sub_models = config_model_names + sub_config_model_names + sub_course_contents
for apt_uid_mod in all_sub_models:
    update_general_record_fields(apt_uid_mod)
    update_records_key_uid_fields_xw(apt_uid_mod)