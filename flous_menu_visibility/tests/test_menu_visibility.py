# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo.tests.common import TransactionCase


class TestMenuVisibility(TransactionCase):
    """Verify that hidden menus are filtered out per user."""

    def setUp(self):
        super().setUp()
        self.internal_group = self.env.ref('base.group_user')
        # A test menu + action visible to every internal user
        # (res.partner is readable by group_user in the base module).
        self.action = self.env['ir.actions.act_window'].create({
            'name': 'Flous Test Partner Action',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
        })
        self.menu = self.env['ir.ui.menu'].create({
            'name': 'Flous Test Menu',
            # Top-level menu (no parent) whose action targets res.partner,
            # which group_user can read -> the menu is visible by default.
            'action': 'ir.actions.act_window,%s' % self.action.id,
            'group_ids': [(6, 0, [self.internal_group.id])],
        })
        self.test_user = self.env['res.users'].create({
            'name': 'Flous Menu Test User',
            'login': 'flous_menu_test_user',
            'group_ids': [(6, 0, [self.internal_group.id])],
        })

    def _new_internal_user(self, login):
        return self.env['res.users'].create({
            'name': 'Flous Menu ' + login,
            'login': login,
            'group_ids': [(6, 0, [self.internal_group.id])],
        })

    def test_menu_visible_by_default(self):
        """An unrestricted internal user must see the menu."""
        env = self.env(user=self.test_user)
        visible = self.menu.with_env(env)._filter_visible_menus()
        self.assertIn(self.menu, visible)

    def test_menu_hidden_for_restricted_user(self):
        """A user that marked the menu as hidden must not see it."""
        self.test_user.hidden_menu_ids = [(4, self.menu.id)]
        env = self.env(user=self.test_user)
        visible = self.menu.with_env(env)._filter_visible_menus()
        self.assertNotIn(self.menu, visible)

    def test_menu_visible_for_other_internal_user(self):
        """Restricting one user must not hide the menu for other users."""
        other = self._new_internal_user('flous_menu_other_user')
        self.test_user.hidden_menu_ids = [(4, self.menu.id)]
        env = self.env(user=other)
        visible = self.menu.with_env(env)._filter_visible_menus()
        self.assertIn(self.menu, visible)

    def test_admin_sees_everything(self):
        """System administrators always see restricted menus."""
        admin = self.env.ref('base.user_admin')
        self.test_user.hidden_menu_ids = [(4, self.menu.id)]
        env = self.env(user=admin)
        visible = self.menu.with_env(env)._filter_visible_menus()
        self.assertIn(self.menu, visible)

    def test_restriction_removed_when_unselected(self):
        """Removing the menu from the user must restore visibility."""
        self.test_user.hidden_menu_ids = [(4, self.menu.id)]
        self.test_user.hidden_menu_ids = [(3, self.menu.id)]
        env = self.env(user=self.test_user)
        visible = self.menu.with_env(env)._filter_visible_menus()
        self.assertIn(self.menu, visible)

    def test_sync_from_menu_side_to_user_side(self):
        """Selecting a user on the menu form reflects on the user record."""
        self.menu.restricted_user_ids = [(4, self.test_user.id)]
        self.assertIn(self.menu, self.test_user.hidden_menu_ids)

    def test_sync_from_user_side_to_menu_side(self):
        """Selecting a menu on the user form reflects on the menu record."""
        self.test_user.hidden_menu_ids = [(4, self.menu.id)]
        self.assertIn(self.test_user, self.menu.restricted_user_ids)
