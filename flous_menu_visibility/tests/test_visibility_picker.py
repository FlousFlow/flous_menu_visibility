# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo.tests.common import TransactionCase


class TestVisibilityPicker(TransactionCase):
    def setUp(self):
        super().setUp()
        self.internal_user = self.env['res.users'].create({
            'name': 'Visibility Picker Test User',
            'login': 'visibility_picker_test_user',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        self.admin = self.env.ref('base.user_admin')
        self.wizard = self.env['flous.visibility.picker'].create({
            'target_type': 'field',
        })

    def test_select_all_excludes_system_administrators(self):
        self.wizard.action_select_all_users()

        self.assertIn(self.internal_user, self.wizard.user_ids)
        self.assertNotIn(self.admin, self.wizard.user_ids)
        self.assertEqual(self.wizard.selected_user_count, len(self.wizard.user_ids))

    def test_clear_selection(self):
        self.wizard.user_ids = [(6, 0, [self.internal_user.id])]

        self.wizard.action_clear_users()

        self.assertFalse(self.wizard.user_ids)
        self.assertEqual(self.wizard.selected_user_count, 0)
