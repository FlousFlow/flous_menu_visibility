# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Menu, Field, Warehouse & Journal Visibility Control',
    'version': '18.0.4.0.0',
    'category': 'Technical',
    'summary': 'Hide menus, fields, warehouse operations and accounting journals per user.',
    'description': """
Hide menus, fields, warehouse operations and accounting journals per user.

Features:
- Hide menu items per user (user form "Hidden Menus" page, or from the menu itself).
- Hide any field of any model per user (Settings > Field Visibility Rules).
- Restrict warehouse operations per user (Warehouse Visibility group): users in the
  group only see operations of the warehouses listed on their user record.
- Hide accounting journals per user with real record rules: a restricted user cannot
  read the journal, its entries (account.move) or their lines (account.move.line).
- System administrators always see everything.
""",
    'author': 'Flous Flow',
    'maintainer': 'Flous Flow',
    'depends': ['base', 'stock', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'security/journal_rules.xml',
        'views/res_users_views.xml',
        'views/ir_ui_menu_views.xml',
        'views/field_hide_rule_views.xml',
        'views/stock_warehouse_views.xml',
        'views/account_journal_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
