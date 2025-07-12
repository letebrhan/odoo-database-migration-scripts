"""
Module: data_export_shell
Description: Cleaned and documented version of data_export_shell.py
"""

#  odoo shell -c informa.conf --no-http 
# odoo shell -c informa.conf --no-http -d informa_eportfolio

import odoo
import json
import os
from odoo import api, tools
from odoo.tools import date_utils # datetime objects are not json serializable. Fortunately, Odoo provides a utility method.
db_name = 'informa_eportfolio'
registry = odoo.registry(db_name)
cr = registry.cursor()
uid = int(odoo.tools.config.get('console_uid', odoo.SUPERUSER_ID))
odoo.api.Environment.reset()
ctx = odoo.api.Environment(cr, uid, {})['res.users'].context_get()
env = odoo.api.Environment(cr, uid, ctx)
self = env.user

current_directory = os.getcwd()
import sys
#get current working directory
current_directory = os.getcwd()
# add your current working directory to sys.path, 
final_directory = os.path.join(current_directory, 'import_export_eportfolio')

if not os.path.exists(final_directory):
   os.makedirs(final_directory)
   
# Fuction which filter only stored fields   
def get_stored_fields_attribute(model_name):
    all_model_fields = self.env[model_name].fields_get()
    stored_fields = {key:v for key,v in all_model_fields.items() if 'store' in v  and v['store'] ==True}
    stored_fields = list(stored_fields.keys())
    
    return stored_fields and stored_fields or None
    
# check if the given model contains active field
def check_active_field_exists(model_name):
    check_active = self.env[model_name]._fields.get('active', False)
    base_domain = check_active and [('active', 'in', [True, False])] or []
    
    return base_domain
    
def export_data_to_dict(model_name, domain=[]):
    stored_fields = get_stored_fields_attribute(model_name)
    base_domain = check_active_field_exists(model_name)
    data = self.env[model_name].sudo().search_read(domain+base_domain, fields=stored_fields)
    record_data = []
    if not data:
        return record_data    
    for vals in data:
        many2one_fields = [(name, value) for (name, value) in vals.items() if (self.env[model_name]._fields.get(name) is not None and
                                                                                self.env[model_name]._fields.get(name).type =='many2one')]
        for name in many2one_fields:
            name = list(name)
            # ex: name [('field_name_title', (1, 'rec_name')]
            # ex: name [('field_name_title', False]
            vals[name[0]] = type(name[1]) is tuple and name[1][0] or name[1]
        record_data.append(vals)
    return record_data

out_data = dict()
groups_id = self.env.ref('base.group_portal').ids

portal_user_ids = self.env['res.users'].search([('active', 'in', [True, False]), ('groups_id', 'in', groups_id)])


model_name = 'res.users'
out_data[model_name] = export_data_to_dict(model_name, [('id', 'in', portal_user_ids.ids)])
#related res.partner portal data
model_name = 'res.partner'
#out_data[model_name] = export_data_to_dict(model_name, [('user_ids', 'in', portal_user_ids.ids)])

partner_ids = self.env['res.partner'].search([('active', 'in', [True, False]), ('user_ids', 'in', portal_user_ids.ids)])

out_data[model_name] = export_data_to_dict(model_name, [('user_ids', 'in', portal_user_ids.ids)]) #+ export_data_to_dict(model_name, [('parent_id', 'in', partner_ids.ids)])


# related res.users.log portal data
#model_name = 'res.users.log' # Currenly only uses the magical fields: create_uid, create_date,
#out_data[model_name] = export_data_to_dict(model_name, [('create_uid', 'in', portal_user_ids.ids)])

# query to obtain res.users password data, b/c password fields are not readable field using Odod ORM
def read_password(portal_user_ids):
    self.env.cr.execute("SELECT id, login, password FROM res_users WHERE id in %(user_ids)s", 
                        dict(user_ids=tuple(portal_user_ids.ids, )))
    res_users_psw_data = self.env.cr.dictfetchall()
    self.env.cr.commit()
    return res_users_psw_data

res_users_psw_data = read_password(portal_user_ids)
if res_users_psw_data:
    with open(final_directory+'/'+('res_users_psw_data')+'.json', 'w') as f:
        json.dump(res_users_psw_data, f, default=date_utils.json_default, indent=4)  
            

# models defined in configuration
models_name_fully = ['skill.master', 'skill.type', 'skill.master','value.master', 'experience.master', 'experience.frequency', 
                     'tag.master', 'rating.values', 'ciofs.elearning.ratings', 'rating.rating', 'slide.tag',
                     'experience.type.details', 'formative.experience.level', 
                    ]
for m in models_name_fully:
    out_data[m] = export_data_to_dict(m)


# filtering the following courses
course_name = ['test', 'Processing and Production of Pasta and Bakery Products', 'ePortfolio - Mi attivo', 
               'ePortfolio - Esploro e Scelgo', 'ePortfolio Bil.Co', 'ePortfolio - Mi preparo']
model_name = 'slide.channel'
out_data[model_name] = export_data_to_dict(model_name, [('name', 'in', course_name)])
base_domain = check_active_field_exists(model_name)
channel_ids = self.env['slide.channel'].search(base_domain+[('name', 'in', course_name)])

# filtering contents of courses
models_name_based_on_courses = ['slide.slide', 'slide.channel.partner', 'slide.channel.invite']
for m in models_name_based_on_courses:
    out_data[m] = export_data_to_dict(m, [('channel_id', 'in', channel_ids.ids)])


# filtering frontend user data
models_name_based_on_course_content = ['skill.level.mapping', 'tag.section.mapping',
                                        'flipcard.slide.mapping', 'tag.instrument', 
                                        'summary.slide.mapping', 'slide.slide.link', 
                                        'slide.embed', 'slide.quiz.score.range', 'slide.question', 
                                        'experience.details.child', 'skill.details']
base_domain = check_active_field_exists('slide.slide')
slide_ids = self.env['slide.slide'].search(base_domain+[('channel_id', 'in', channel_ids.ids)])
for m in models_name_based_on_course_content:
    out_data[m] = export_data_to_dict(m, [('slide_id', 'in', slide_ids.ids)])
# for model 'ciofs.flipcard' the slide.slide field defined as 'slide_slide_ids', so, we separate it 
out_data['ciofs.flipcard'] = export_data_to_dict('ciofs.flipcard', [('slide_slide_ids', 'in', slide_ids.ids)])

# filtering answers for questions in the course contents
model_name = 'slide.answer'
base_domain = check_active_field_exists(model_name)
question_ids = self.env['slide.question'].search(base_domain+[('slide_id', 'in', slide_ids.ids)])
out_data[model_name] = export_data_to_dict(model_name, [('question_id', 'in', question_ids.ids)])

model_name = 'slide.partner.open.question'
out_data[model_name] = export_data_to_dict(model_name, [('partner_id', 'in', partner_ids.ids), 
                                                        ('slide_id', 'in', slide_ids.ids), ('question_id', 'in', question_ids.ids)])

if out_data:
    with open(final_directory+'/'+('all_exported_data')+'.json', 'w') as f:
        json.dump(out_data, f, default=date_utils.json_default, indent=4)    
