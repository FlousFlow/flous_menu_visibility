# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Menu, Field & Warehouse Visibility Control',
    'version': '18.0.3.0.0',
    'category': 'Technical',
    'summary': 'Hide menus/fields and restrict warehouse operations per user.',
    'description': """
<section class="oe_container">
<div class="oe_row oe_spaced">
<h2 class="oe_slogan">Menu, Field &amp; Warehouse Visibility Control</h2>
<p class="oe_mt32">
Control what each user can see across the whole system:
hide menu items, hide any field of any model, and restrict
warehouse operations per user. System administrators always
see everything.
</p>
</div>
</section>

<section class="oe_container oe_dark">
<div class="oe_row oe_spaced">
<h3 class="oe_slogan">Hide menus per user</h3>
<div class="oe_span6">
<img class="oe_picture oe_screenshot" src="screenshot_1_hidden_menus.png"/>
</div>
<div class="oe_span6">
<p class="oe_mt32">
Configure from the user form ("Hidden Menus" page) or from the
menu itself ("Restricted Users"). Both stay in sync natively.
</p>
</div>
</div>
</section>

<section class="oe_container">
<div class="oe_row oe_spaced">
<h3 class="oe_slogan">Restrict warehouse operations per user</h3>
<div class="oe_span6">
<img class="oe_picture oe_screenshot" src="screenshot_2_visible_warehouses.png"/>
</div>
<div class="oe_span6">
<p class="oe_mt32">
Users in the "Warehouse Visibility" group only see operations
(receipts, deliveries, internal transfers) of the warehouses
listed on their user record. An empty list means no operations
are visible.
</p>
</div>
</div>
</section>

<section class="oe_container oe_dark">
<div class="oe_row oe_spaced">
<h3 class="oe_slogan">Hide any field of any model</h3>
<div class="oe_span6">
<img class="oe_picture oe_screenshot" src="screenshot_3_field_hide_rules.png"/>
</div>
<div class="oe_span6">
<p class="oe_mt32">
Create rules under Settings &gt; Field Visibility Rules. A rule
hides one field of one model for the selected users. Hiding
sets invisible="1" on the view node, so the value stays loaded
and the view is never broken.
</p>
</div>
</div>
</section>

<section class="oe_container">
<div class="oe_row oe_spaced">
<h3 class="oe_slogan">Assign warehouses from the warehouse form</h3>
<div class="oe_span12">
<img class="oe_picture oe_screenshot" src="screenshot_4_warehouse_visible_users.png"/>
</div>
</div>
</section>
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
