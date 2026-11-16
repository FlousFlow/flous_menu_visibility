# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase


class TestPosConfigVisibility(TransactionCase):
    """Verify both POS visibility modes and guarded POS entry points."""

    def setUp(self):
        super().setUp()
        self.pos_group = self.env.ref('point_of_sale.group_pos_user')
        self.internal_group = self.env.ref('base.group_user')
        self.selected_user = self._new_pos_user('flous_pos_visibility_selected')
        self.other_user = self._new_pos_user('flous_pos_visibility_other')
        self.admin = self.env.ref('base.user_admin')
        self.config = self.env['pos.config'].create({
            'name': 'Flous POS Visibility Test',
        })

    def _new_pos_user(self, login):
        return self.env['res.users'].create({
            'name': 'Flous ' + login,
            'login': login,
            'groups_id': [(6, 0, [self.internal_group.id, self.pos_group.id])],
        })

    def _visible_configs(self, user):
        return self.env['pos.config'].with_user(user).search(
            [('id', '=', self.config.id)],
        )

    def test_hide_mode_blocks_selected_user_but_not_others_or_admin(self):
        self.config.write({
            'visibility_mode': 'hide',
            'restricted_user_ids': [(6, 0, [self.selected_user.id])],
        })

        self.assertFalse(self._visible_configs(self.selected_user))
        self.assertIn(self.config, self._visible_configs(self.other_user))
        self.assertIn(self.config, self._visible_configs(self.admin))
        with self.assertRaises(AccessError):
            self.config.with_user(self.selected_user).action_open_ui()
        with self.assertRaises(AccessError):
            self.config.with_user(self.selected_user).open_ui()
        with self.assertRaises(AccessError):
            self.config.with_user(self.selected_user).open_session_if_not_opened()

    def test_show_mode_only_allows_selected_user_and_admin(self):
        self.config.write({
            'visibility_mode': 'show',
            'restricted_user_ids': [(6, 0, [self.selected_user.id])],
        })

        self.assertIn(self.config, self._visible_configs(self.selected_user))
        self.assertFalse(self._visible_configs(self.other_user))
        self.assertIn(self.config, self._visible_configs(self.admin))
        self.config.with_user(self.selected_user)._check_visibility_access()
        with self.assertRaises(AccessError):
            self.config.with_user(self.other_user)._check_visibility_access()
        self.config.with_user(self.admin)._check_visibility_access()

    def test_show_mode_with_empty_selection_denies_all_regular_users(self):
        self.config.write({
            'visibility_mode': 'show',
            'restricted_user_ids': [(5, 0, 0)],
        })

        self.assertFalse(self._visible_configs(self.selected_user))
        self.assertFalse(self._visible_configs(self.other_user))
        self.assertIn(self.config, self._visible_configs(self.admin))

    def test_system_administrator_is_removed_from_restricted_users(self):
        self.config.write({
            'visibility_mode': 'show',
            'restricted_user_ids': [(6, 0, [self.selected_user.id, self.admin.id])],
        })

        self.assertIn(self.selected_user, self.config.restricted_user_ids)
        self.assertNotIn(self.admin, self.config.restricted_user_ids)
        self.config.with_user(self.admin)._check_visibility_access()

    def test_active_pos_session_prevents_new_visibility_restriction(self):
        self.env['pos.session'].create({
            'config_id': self.config.id,
            'user_id': self.selected_user.id,
        })

        with self.cr.savepoint():
            with self.assertRaises(ValidationError):
                self.config.write({
                    'visibility_mode': 'hide',
                    'restricted_user_ids': [(4, self.selected_user.id)],
                })
        self.assertNotIn(self.selected_user, self.config.restricted_user_ids)

    def test_hidden_config_blocks_pos_session_data_loading(self):
        self.config.write({
            'visibility_mode': 'hide',
            'restricted_user_ids': [(6, 0, [self.selected_user.id])],
        })
        session = self.env['pos.session'].create({
            'config_id': self.config.id,
            'user_id': self.selected_user.id,
        })

        with self.assertRaises(AccessError):
            session.with_user(self.selected_user).load_data([], only_data=True)

    def test_show_mode_session_data_is_available_only_to_selected_user(self):
        self.config.write({
            'visibility_mode': 'show',
            'restricted_user_ids': [(6, 0, [self.selected_user.id])],
        })
        session = self.env['pos.session'].create({
            'config_id': self.config.id,
            'user_id': self.selected_user.id,
        })

        data = session.with_user(self.selected_user).load_data([], only_data=True)
        self.assertIn('pos.config', data)
        with self.assertRaises(AccessError):
            session.with_user(self.other_user).load_data([], only_data=True)
