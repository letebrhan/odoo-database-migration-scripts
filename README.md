# odoo-database-migration-scripts

Scripts for exporting and importing eLearning data between Odoo databases, including user credentials, courses, and frontend content.

# 📦 Odoo eLearning Migration Scripts

This repository contains Python scripts for exporting and importing eLearning data across Odoo databases. It supports structured migration of `res.users`, `res.partner`, course content, configurations, and frontend mappings — with password integrity and relational field preservation.

---

## 🚀 Features

- 🔄 **Export/Import**: Users, partners, courses, frontend objects
- 🔐 **Passwords migration** using raw SQL (for `res.users`)
- 🔁 **Handles m2o/m2m/o2m** relational links automatically
- ⚙️ **SQL constraint-based deduplication**
- 🧠 **Dynamic field filtering and type handling**
- ✅ Compatible with Odoo 13+

---

## 📂 Structure

```
import_export_eportfolio/
├── common_function.py                # Shared helper methods
├── data_export_shell.py             # Full export script (portal & eLearning)
├── data_export_shell_portal.py      # Limited portal-only export
├── importer_res_users_partner.py    # Import users and partners
├── importer_course_config_data.py   # Import courses and configuration models
├── importer_frontend_others.py      # Import frontend-related models
├── __init__.py                      # Central entrypoint (optional use)
└── README.md                        # Project documentation
```

---

## 🛠️ Usage

### Export Data
```bash
odoo shell -c informa.conf --no-http -d informa_eportfolio
>>> exec(open('data_export_shell.py').read())
```

### Import Data
Make sure to update the database name in each script (`db_name = 'your_target_db'`).

```bash
# Step-by-step or centralized execution
python3 importer_res_users_partner.py
python3 importer_course_config_data.py
python3 importer_frontend_others.py
```

---

## 🔐 Password Handling

Passwords are stored in `res_users_psw_data.json` and re-applied using raw SQL (since Odoo ORM cannot reassign the same hash). 

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙋 Support

Feel free to open issues or contribute improvements. This tool is tailored for reliable migrations during production upgrades and module changes.
