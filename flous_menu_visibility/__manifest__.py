# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Menu, Field, Warehouse & Journal Visibility Control',
    'version': '19.0.2.0.0',
    'category': 'Technical',
    'summary': 'Hide menus, fields, warehouse operations and accounting journals per user.',
    'description': """
Hide menus, fields, view buttons, warehouse operations and accounting journals per user.

Features:
- Configure all visibility controls globally from Settings > Visibility Control.
- Hide menu items per user from the central Hidden Menus list.
- Hide any field of any model per user from the central Field Visibility Rules list.
- Hide form/list action buttons and embedded list create controls per user.
- Restrict warehouse operations per user (Warehouse Visibility group): users in the
  group only see operations of the warehouses listed in Visibility Control.
- Hide accounting journals per user with real record rules: a restricted user cannot
  read the journal, its entries (account.move) or their lines (account.move.line).
- System administrators always see everything.
""",
    'author': 'Flous Flow',
    'website': 'https://flousflow.com/',
    'maintainer': 'Flous Flow',
    'depends': ['base', 'stock', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'security/journal_rules.xml',
        'views/visibility_control_views.xml',
        'views/ir_ui_menu_views.xml',
        'views/field_hide_rule_views.xml',
        'views/button_hide_rule_views.xml',
        'views/stock_warehouse_views.xml',
        'views/account_journal_views.xml',
        'wizard/visibility_picker_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'flous_menu_visibility/static/src/visibility_picker/visibility_picker.js',
            'flous_menu_visibility/static/src/visibility_picker/visibility_picker.xml',
            'flous_menu_visibility/static/src/visibility_picker/visibility_picker.scss',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
