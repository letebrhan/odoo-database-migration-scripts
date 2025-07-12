"""
Module: data_export_shell_portal
Description: Cleaned and documented version of data_export_shell_portal.py
"""

#  odoo shell -c informa.conf --no-http
# odoo shell -c informa.conf --no-http -d informa_eportfolio

import odoo
import json
import os
from odoo import api, tools
from odoo.tools import date_utils # datetime objects are not json serializable. Fortunately, Odoo provides a utility method.
db_name = 'informa_eportfolio_381'
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
#portal_group_ids = self.env.ref('base.group_portal').ids
#groups_ids = portal_group_ids + self.env.ref('ciofs_eLearning.eLearning_operator_access').ids

# filter users who have eportfolio security groups
#user_ids = self.env['res.users'].search([('active', 'in', [True, False]), ('groups_id', 'in', groups_ids)])
# get admin users
admin_users = self.env['res.users'].search([('active', 'in', [True, False]), ('login', 'in', ['admin', 'sradmin'])])
# eportfolio users
eport_users = self.env['res.users'].search([('active', 'in', [True, False]), ('login', 'in', ['m.bertinelli@ekogrid.com'])])


# filter users who have only portal security groups
portal_user_ids = self.env['res.users'].search([('active', 'in', [True, False]), ('login', 'in', ['bertinellimattia83@gmail.com'])])
user_ids = portal_user_ids + admin_users + eport_users
model_name = 'res.users'
out_data[model_name] = export_data_to_dict(model_name, [('id', 'in', user_ids.ids)])


# filter res.partner whose user's have portal access, and admin users who have course
partner_ids = self.env['res.partner'].search([('active', 'in', [True, False]), ('user_ids', 'in', (admin_users+portal_user_ids).ids)])

# filter res.partners data who have both eportfolio and portal access right
model_name = 'res.partner'
#all_res_partner = self.env['res.partner'].search([('active', 'in', [True, False]), ('user_ids', 'in', user_ids.ids)])
out_data[model_name] = export_data_to_dict(model_name, [('id', 'in', partner_ids.ids)])

# query to obtain res.users password data, b/c password fields are not readable field using Odod ORM
def read_password(user_ids):
    self.env.cr.execute("SELECT id, login, password FROM res_users WHERE id in %(user_ids)s",
                        dict(user_ids=tuple(user_ids.ids, )))
    res_users_psw_data = self.env.cr.dictfetchall()
    self.env.cr.commit()
    return res_users_psw_data

res_users_psw_data = read_password(user_ids)
if res_users_psw_data:
    with open(final_directory+'/'+('res_users_psw_data')+'.json', 'w') as f:
        json.dump(res_users_psw_data, f, default=date_utils.json_default, indent=4)


# models defined in configuration
models_name_fully = ['skill.master', 'skill.type', 'skill.master','value.master', 'experience.master',
                     'experience.frequency', 'tag.master', 'rating.values', 'ciofs.elearning.ratings',
                     'slide.tag', 'formative.experience.level']
for m in models_name_fully:
    out_data[m] = export_data_to_dict(m)


# filtering data  the following courses
course_name = ['test', 'Processing and Production of Pasta and Bakery Products', 'ePortfolio - Mi attivo',
               'ePortfolio - Esploro e Scelgo', 'ePortfolio Bil.Co', 'ePortfolio - Mi preparo', 'ePortfolio - Mi presento']
model_name = 'slide.channel'
out_data[model_name] = export_data_to_dict(model_name, [('name', 'in', course_name),
                                                        ('partner_ids', 'in',  partner_ids.ids)])
base_domain = check_active_field_exists(model_name)
channel_ids = self.env['slide.channel'].search(base_domain+[('name', 'in', course_name),
                                                            ('partner_ids', 'in',  partner_ids.ids)])

model_name = 'slide.channel.invite'
out_data[model_name] = export_data_to_dict(model_name, [('channel_id', 'in', channel_ids.ids)])


# filtering slide.channel.partner based on course and attendee
channel_partner_ids = self.env['slide.channel.partner'].search([('channel_id', 'in', channel_ids.ids),
                                                                ('partner_id', 'in', partner_ids.ids)])
model_name = 'slide.channel.partner'
out_data[model_name] = export_data_to_dict(model_name, [('id', 'in', channel_partner_ids.ids)])


# filtering slide.slide.partner based on slide.slide content
slide_partner_ids = self.env['slide.slide.partner'].search([('channel_id', 'in', channel_ids.ids),
                                                            ('partner_id', 'in', partner_ids.ids)])
model_name = 'slide.slide.partner'
out_data[model_name] = export_data_to_dict(model_name, [('id', 'in', slide_partner_ids.ids)])

# filtering contents of courses
base_domain = check_active_field_exists('slide.slide')
slide_partner_ids = slide_partner_ids.mapped('slide_id')
slide_ids = self.env['slide.slide'].search(base_domain + [('channel_id', 'in', channel_ids.ids),
                                                          ('id', 'in', slide_partner_ids.ids)])
model_name = 'slide.slide'
out_data[model_name] = export_data_to_dict(model_name, [('id', 'in', slide_ids.ids)])

# filtering sub course content slide.slide related data
models_name_based_on_course_content = ['slide.slide.link', 'slide.embed', 'experience.type.details',
                                       'summary.slide.mapping', 'experience.details.child',
                                       'skill.level.mapping', 'tag.section.mapping', 'skill.details',
                                       'slide.question',  'tag.instrument', 'slide.quiz.score.range',
                                       'flipcard.slide.mapping']

for m in models_name_based_on_course_content:
    out_data[m] = export_data_to_dict(m, [('slide_id', 'in', slide_ids.ids)])


# for model 'ciofs.flipcard' the slide.slide field defined as 'slide_slide_ids', so, we separate it
out_data['ciofs.flipcard'] = export_data_to_dict('ciofs.flipcard', [('slide_slide_ids', 'in', slide_ids.ids)])

base_domain = check_active_field_exists(model_name)

# filtering section.value.mapping
model_name = 'section.value.mapping'
tag_master_ids = self.env['tag.master'].search([])
out_data[model_name] = export_data_to_dict(model_name, [('value', 'in', tag_master_ids.ids)])


# filtering 'ciofs.partner.curriculum'
model_name = 'ciofs.partner.curriculum'
out_data[model_name] = export_data_to_dict(model_name, [('partner_id', 'in', partner_ids.ids)])


# filtering answers for questions in the course contents
model_name = 'slide.answer'
question_ids = self.env['slide.question'].search([('slide_id', 'in', slide_ids.ids)])
out_data[model_name] = export_data_to_dict(model_name, [('question_id', 'in', question_ids.ids)])


# filtering 'slide.partner.open.question'
model_name = 'slide.partner.open.question'
out_data[model_name] = export_data_to_dict(model_name, [('partner_id', 'in', partner_ids.ids),
                                                        ('slide_id', 'in', slide_ids.ids),
                                                        ('question_id', 'in', question_ids.ids)])
model_name = 'ciofs.slide.partner.quiz.response'
out_data[model_name] = export_data_to_dict(model_name)

if out_data:
    with open(final_directory+'/'+('all_exported_data')+'.json', 'w') as f:
        json.dump(out_data, f, default=date_utils.json_default, indent=4)

eport_groups_id = self.env.ref('ciofs_eLearning.eLearning_operator_access').ids
eport_users_ids = self.env['res.users'].search([('active', 'in', [True, False]), ('id', 'in', eport_users.ids)])
eport_users_login = eport_users_ids.mapped('login')

if eport_users_login:
    with open(final_directory + '/'+('eport_users_login')+'.json', 'w') as f:
        json.dump(eport_users_login, f, default=date_utils.json_default, indent=4)