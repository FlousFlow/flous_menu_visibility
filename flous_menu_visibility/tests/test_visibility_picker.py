# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError


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

    def test_action_apply_saves_show_mode_for_journal(self):
        journal = self.env['account.journal'].create({
            'name': 'Visibility Picker Show Journal', 'type': 'general', 'code': 'VPSJ',
        })
        action = self.env['flous.visibility.picker'].action_open_for_journal(journal.id)
        wizard = self.env['flous.visibility.picker'].browse(action['res_id'])
        wizard.write({
            'visibility_mode': 'show',
            'user_ids': [(6, 0, [self.internal_user.id])],
        })
        wizard.action_apply()

        journal.invalidate_recordset()
        self.assertEqual(journal.visibility_mode, 'show')
        self.assertEqual(journal.restricted_user_ids, self.internal_user)
        self.assertEqual(
            self.env['flous.visibility.picker'].action_open_for_journal(journal.id)['res_model'],
            'flous.visibility.picker',
        )

    def test_action_apply_updates_existing_rule_instead_of_duplicating(self):
        journal = self.env['account.journal'].create({
            'name': 'Visibility Picker Update Journal', 'type': 'general', 'code': 'VPUJ',
        })
        journal.write({
            'visibility_mode': 'show',
            'restricted_user_ids': [(6, 0, [self.internal_user.id])],
        })
        action = self.env['flous.visibility.picker'].action_open_for_journal(journal.id)
        wizard = self.env['flous.visibility.picker'].browse(action['res_id'])
        wizard.write({
            'visibility_mode': 'hide',
            'user_ids': [(5, 0, 0)],
        })
        wizard.action_apply()

        self.assertEqual(journal.visibility_mode, 'hide')
        self.assertFalse(journal.restricted_user_ids)

    def test_non_admin_cannot_apply_visibility_rule(self):
        with self.assertRaises(AccessError):
            self.wizard.with_user(self.internal_user).action_apply()

    def test_action_apply_never_restricts_system_administrators(self):
        journal = self.env['account.journal'].create({
            'name': 'Visibility Picker Admin Guard Journal',
            'type': 'general',
            'code': 'VPAG',
        })
        action = self.env['flous.visibility.picker'].action_open_for_journal(journal.id)
        wizard = self.env['flous.visibility.picker'].browse(action['res_id'])
        wizard.user_ids = [(6, 0, [self.internal_user.id, self.admin.id])]
        wizard.action_apply()

        self.assertIn(self.internal_user, journal.restricted_user_ids)
        self.assertNotIn(self.admin, journal.restricted_user_ids)
        self.assertIn(
            journal,
            self.env['account.journal'].with_user(self.admin).search([('id', '=', journal.id)]),
        )
