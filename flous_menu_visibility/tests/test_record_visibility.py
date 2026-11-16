# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo.tests.common import TransactionCase


class TestRecordVisibility(TransactionCase):
    """Verify per-user Kanban card filtering and its presentation-only scope."""

    def setUp(self):
        super().setUp()
        self.internal_group = self.env.ref('base.group_user')
        self.model = self.env['ir.model']._get('res.partner')
        self.record = self.env['res.partner'].create({'name': 'Flous Kanban Visibility Record'})
        self.selected_user = self._new_user('flous_record_visibility_selected')
        self.other_user = self._new_user('flous_record_visibility_other')

    def _new_user(self, login):
        return self.env['res.users'].create({
            'name': 'Flous ' + login,
            'login': login,
            'groups_id': [(6, 0, [self.internal_group.id])],
        })

    def _create_rule(self, mode='hide', users=None, active=True):
        return self.env['flous.record.hide.rule'].create({
            'name': 'Kanban visibility test',
            'model_id': self.model.id,
            'record_id': self.record.id,
            'record_name': self.record.display_name,
            'visibility_mode': mode,
            'user_ids': [(6, 0, users or [])],
            'active': active,
        })

    def _hidden_ids(self, user, record_ids=None):
        return self.env['flous.visibility.service'].with_user(user).get_hidden_record_ids(
            'res.partner', record_ids if record_ids is not None else [self.record.id],
        )

    def test_hide_mode_returns_record_only_for_selected_user(self):
        self._create_rule('hide', [self.selected_user.id])

        self.assertEqual(self._hidden_ids(self.selected_user), [self.record.id])
        self.assertEqual(self._hidden_ids(self.other_user), [])
        self.assertEqual(self._hidden_ids(self.env.ref('base.user_admin')), [])

    def test_show_mode_returns_record_only_for_unselected_users(self):
        self._create_rule('show', [self.selected_user.id])

        self.assertEqual(self._hidden_ids(self.selected_user), [])
        self.assertEqual(self._hidden_ids(self.other_user), [self.record.id])
        self.assertEqual(self._hidden_ids(self.env.ref('base.user_admin')), [])

    def test_show_mode_with_empty_selection_hides_from_all_regular_users(self):
        self._create_rule('show')

        self.assertEqual(self._hidden_ids(self.selected_user), [self.record.id])
        self.assertEqual(self._hidden_ids(self.other_user), [self.record.id])
        self.assertEqual(self._hidden_ids(self.env.ref('base.user_admin')), [])

    def test_inactive_rule_has_no_effect_and_record_remains_backend_readable(self):
        self._create_rule('hide', [self.selected_user.id], active=False)

        self.assertEqual(self._hidden_ids(self.selected_user), [])
        # Kanban visibility rules filter presentation. They are not ACLs or record rules.
        self.assertEqual(
            self.env['res.partner'].with_user(self.selected_user).browse(self.record.id).name,
            'Flous Kanban Visibility Record',
        )

    def test_invalid_ids_and_other_model_do_not_leak_hidden_record_ids(self):
        self._create_rule('hide', [self.selected_user.id])

        self.assertEqual(self._hidden_ids(self.selected_user, ['bad-id']), [])
        self.assertEqual(
            self.env['flous.visibility.service'].with_user(self.selected_user)
            .get_hidden_record_ids('res.company', [self.record.id]),
            [],
        )
