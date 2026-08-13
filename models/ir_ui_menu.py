# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class IrUiMenu(models.Model):
    """Extend ir.ui.menu with per-user menu restrictions.

    The relation is stored in the shared table
    ``flous_menu_visibility_rel`` (see ``res.users.hidden_menu_ids``).
    """

    _inherit = 'ir.ui.menu'

    restricted_user_ids = fields.Many2many(
        'res.users',
        relation='flous_menu_visibility_rel',
        column1='menu_id',
        column2='user_id',
        string='Restricted Users',
        help='Users for whom this menu will be hidden.',
    )

    @api.returns('self')
    def _filter_visible_menus(self):
        """Hide restricted menus for the current user.

        The base implementation already removes menus the user has no rights
        for; here we additionally remove menus the user explicitly marked as
        hidden on their user record. System administrators always see the
        full menu tree.
        """
        menus = super()._filter_visible_menus()
        if not menus or self.env.user.has_group('base.group_system'):
            return menus
        hidden = self.env.user.hidden_menu_ids
        if not hidden:
            return menus
        return menus.filtered(lambda menu: menu not in hidden)
