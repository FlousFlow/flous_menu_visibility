# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Flous Flow POS Visibility',
    'version': '20.0.1.0.2',
    'category': 'Point of Sale',
    'summary': 'Hide selected points of sale from specific users.',
    'description': """
Optional integration for Menu, Field, Warehouse & Journal Visibility Control.
It installs automatically when both this module and Odoo Point of Sale are installed.

Administrators can restrict a POS configuration for selected internal users.
Restricted configurations are removed from the POS dashboard, and starting
one through its backend action or direct URL is blocked. Existing active POS
sessions must be closed before a restriction can be applied; the module does
not close sessions or interfere with orders.
""",
    'author': 'Flous Flow',
    'website': 'https://flousflow.com/',
    'maintainer': 'Flous Flow',
    'depends': ['flous_menu_visibility', 'point_of_sale'],
    'data': [
        'security/pos_visibility.xml',
        'views/visibility_views.xml',
        'views/pos_config_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': True,
    'application': False,
}
