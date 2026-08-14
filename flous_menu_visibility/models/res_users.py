# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class ResUsers(models.Model):
    """Extend res.users so administrators can hide specific menus per user.

    ``hidden_menu_ids`` and ``ir.ui.menu.restricted_user_ids`` point to the
    same relation table (``flous_menu_visibility_rel``) with swapped columns.
    Odoo therefore keeps both sides in sync natively: adding a menu on the
    user form automatically shows the user on the menu form and vice versa.
    """

    _inherit = 'res.users'

    hidden_menu_ids = fields.Many2many(
        'ir.ui.menu',
        relation='flous_menu_visibility_rel',
        column1='user_id',
        column2='menu_id',
        string='Hidden Menus',
        help="Menus that will be hidden for this user. Selecting a menu here "
             "removes it from the user's application menu.",
    )

    hidden_journal_ids = fields.Many2many(
        'account.journal',
        relation='flous_journal_visibility_rel',
        column1='user_id',
        column2='journal_id',
        string='Hidden Journals',
        groups='base.group_system',
        help="Journals hidden from this user. An empty list means the user "
             "sees every journal. System administrators always see all "
             "journals.",
    )

    visible_warehouse_ids = fields.Many2many(
        'stock.warehouse',
        relation='flous_warehouse_visibility_rel',
        column1='user_id',
        column2='warehouse_id',
        string='Visible Warehouses',
        help="Warehouses whose operations (receipts, deliveries, internal "
             "transfers) this user can see. Only applies to users in the "
             "'Warehouse Visibility' group: they see operations of these "
             "warehouses only. An empty list means no operations are visible "
             "for group members. Users outside that group (and system "
             "administrators) always see everything.",
    )

    def write(self, vals):
        res = super().write(vals)
        if 'visible_warehouse_ids' in vals or 'hidden_journal_ids' in vals:
            # ir.rule domains are cached per user (uid). Invalidate the
            # registry cache so the new restrictions apply immediately.
            self.env.registry.clear_cache()
        if 'hidden_journal_ids' in vals and not self.env.context.get('flous_skip_admin_guard'):
            # Defense in depth: the administrator is never restricted.
            admin = self.env.ref('base.user_admin')
            if admin in self:
                admin.with_context(flous_skip_admin_guard=True).sudo().write(
                    {'hidden_journal_ids': [(5, 0, 0)]})
        return res

    is_admin = fields.Boolean(
        string='Is Admin',
        compute='_compute_is_admin',
        help='Whether this user is the main administrator.',
    )

    is_internal_user = fields.Boolean(
        string='Is Internal User',
        compute='_compute_is_internal_user',
        help='Whether this user belongs to the internal user group.',
    )

    def _compute_is_admin(self):
        """Flag the main administrator so the menu page can be hidden for it.

        Non-stored compute without dependencies: evaluated on read.
        """
        admin = self.env.ref('base.user_admin')
        for user in self:
            user.is_admin = user.id == admin.id

    @api.depends('groups_id')
    def _compute_is_internal_user(self):
        """Only internal users are meant to have menu restrictions applied."""
        internal_group = self.env.ref('base.group_user')
        for user in self:
            user.is_internal_user = internal_group in user.groups_id
