# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo.tests.common import TransactionCase


class TestJournalVisibility(TransactionCase):
    """Verify that journals (and their entries/lines) are hidden per user."""

    def setUp(self):
        super().setUp()
        self.internal_group = self.env.ref('base.group_user')
        # Read-only accountant: the least-privileged group that can read
        # journals, moves and move lines.
        self.readonly_group = self.env.ref('account.group_account_readonly')
        self.test_user = self.env['res.users'].create({
            'name': 'Flous Journal Test User',
            'login': 'flous_journal_test_user',
            'groups_id': [(6, 0, [self.internal_group.id, self.readonly_group.id])],
        })
        self.journal_a = self.env['account.journal'].create({
            'name': 'Flous Journal A', 'type': 'general', 'code': 'FJAA',
        })
        self.journal_b = self.env['account.journal'].create({
            'name': 'Flous Journal B', 'type': 'general', 'code': 'FJBB',
        })

    def _new_user(self, login):
        return self.env['res.users'].create({
            'name': 'Flous ' + login,
            'login': login,
            'groups_id': [(6, 0, [self.internal_group.id, self.readonly_group.id])],
        })

    def _visible_journals(self, user):
        return self.env['account.journal'].with_user(user).search(
            [('id', 'in', (self.journal_a | self.journal_b).ids)])

    def test_sees_all_when_no_restriction(self):
        """With an empty restriction the user sees every journal."""
        found = self._visible_journals(self.test_user)
        self.assertIn(self.journal_a, found)
        self.assertIn(self.journal_b, found)

    def test_journal_hidden_for_restricted_user(self):
        """A journal added to the user's hidden list is not readable."""
        self.test_user.hidden_journal_ids = [(4, self.journal_a.id)]
        found = self._visible_journals(self.test_user)
        self.assertNotIn(self.journal_a, found)
        self.assertIn(self.journal_b, found)

    def test_other_user_not_affected(self):
        """Restricting one user must not affect other users."""
        self.test_user.hidden_journal_ids = [(4, self.journal_a.id)]
        other = self._new_user('flous_journal_other_user')
        found = self._visible_journals(other)
        self.assertIn(self.journal_a, found)

    def test_admin_sees_all_journals(self):
        """System administrators are never restricted."""
        self.test_user.hidden_journal_ids = [(4, self.journal_a.id)]
        admin = self.env.ref('base.user_admin')
        found = self._visible_journals(admin)
        self.assertIn(self.journal_a, found)

    def test_removing_restriction_restores(self):
        """Removing the restriction makes the journal visible again."""
        self.test_user.hidden_journal_ids = [(4, self.journal_a.id)]
        self.test_user.hidden_journal_ids = [(3, self.journal_a.id)]
        found = self._visible_journals(self.test_user)
        self.assertIn(self.journal_a, found)

    def test_sync_from_journal_side(self):
        """Selecting a user on the journal form reflects on the user record."""
        self.journal_a.restricted_user_ids = [(4, self.test_user.id)]
        self.assertIn(self.journal_a, self.test_user.hidden_journal_ids)

    def test_moves_and_lines_hidden_for_restricted_user(self):
        """Moves and move lines of a hidden journal are not readable."""
        account = self.env['account.account'].create({
            'name': 'Flous Test Asset Account',
            'code': '19991',
            'account_type': 'asset_current',
        })
        move = self.env['account.move'].create({
            'journal_id': self.journal_a.id,
            'line_ids': [
                (0, 0, {
                    'name': 'Flous test line',
                    'account_id': account.id,
                    'debit': 100.0,
                }),
                (0, 0, {
                    'name': 'Flous test line 2',
                    'account_id': account.id,
                    'credit': 100.0,
                }),
            ],
        })
        self.test_user.hidden_journal_ids = [(4, self.journal_a.id)]

        found_moves = self.env['account.move'].with_user(self.test_user).search(
            [('id', '=', move.id)])
        self.assertNotIn(move, found_moves)

        found_lines = self.env['account.move.line'].with_user(self.test_user).search(
            [('move_id', '=', move.id)])
        self.assertFalse(found_lines)

        # The admin still sees the move.
        admin = self.env.ref('base.user_admin')
        found_admin = self.env['account.move'].with_user(admin).search(
            [('id', '=', move.id)])
        self.assertIn(move, found_admin)
