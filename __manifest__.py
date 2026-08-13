# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Menu, Field & Warehouse Visibility Control',
    'version': '18.0.3.0.0',
    'category': 'Technical',
    'summary': 'Hide menus/fields and restrict warehouse operations per user.',
    'description': """
Menu, Field & Warehouse Visibility Control
===========================================
Control what each user can see across the whole system.

* Hide menu items per user (user form "Hidden Menus" page).
* Hide any field of any model per user (Settings > Field Visibility Rules).
* Restrict warehouse operations per user (Warehouse Visibility group):
  users in the group only see operations (receipts, deliveries, internal
  transfers) of the warehouses listed on their user record.
* Two-step inter-warehouse transfers produce one operation per warehouse,
  so each warehouse operator only sees their own step.
* System administrators always see everything.
""",
    'author': 'Flous Flow',
    'maintainer': 'Flous Flow',
    'depends': ['base', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/res_users_views.xml',
        'views/ir_ui_menu_views.xml',
        'views/field_hide_rule_views.xml',
        'views/stock_warehouse_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
