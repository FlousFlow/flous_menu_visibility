# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Menu, Field, Warehouse & Journal Visibility Control',
    'version': '18.0.4.0.0',
    'category': 'Technical',
    'summary': 'Hide menus, fields, warehouse operations and accounting journals per user.',
    'description': """
<section class="oe_container">
<div class="oe_row oe_spaced">
<h2 class="oe_slogan">Menu, Field, Warehouse &amp; Journal Visibility Control</h2>
<p class="oe_mt32">
Control what each user can see across the whole system:
hide menu items, hide any field of any model, restrict
warehouse operations per user, and hide accounting journals
per user. System administrators always see everything.
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

<section class="oe_container oe_dark">
<div class="oe_row oe_spaced">
<h3 class="oe_slogan">Hide accounting journals per user</h3>
<div class="oe_span6">
<img class="oe_picture oe_screenshot" src="screenshot_5_hidden_journals.png"/>
</div>
<div class="oe_span6">
<p class="oe_mt32">
Administrators pick the hidden journals on the user's
"Hidden Journals" page. A restricted user cannot read the
journal, its entries (account.move) or their lines
(account.move.line) — through menus, reports, exports or API.
</p>
</div>
</div>
</section>

<section class="oe_container">
<div class="oe_row oe_spaced">
<h3 class="oe_slogan">Or restrict users from the journal</h3>
<div class="oe_span6">
<img class="oe_picture oe_screenshot" src="screenshot_6_journal_restricted_users.png"/>
</div>
<div class="oe_span6">
<p class="oe_mt32">
Use the journal's "Restricted Users" tab. Both sides stay in
sync natively.
</p>
</div>
</div>
</section>
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
