# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo.exceptions import AccessError
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

    def test_journal_show_mode_only_allows_selected_users(self):
        """Show mode exposes the journal only to selected non-admin users."""
        other = self._new_user('flous_journal_show_other')
        self.journal_a.write({
            'visibility_mode': 'show',
            'restricted_user_ids': [(6, 0, [self.test_user.id])],
        })

        self.assertIn(self.journal_a, self._visible_journals(self.test_user))
        self.assertNotIn(self.journal_a, self._visible_journals(other))
        self.assertIn(self.journal_a, self._visible_journals(self.env.ref('base.user_admin')))

    def test_hidden_journal_cannot_be_read_by_known_record_id(self):
        """A guessed or previously known journal ID does not bypass the rule."""
        self.journal_a.restricted_user_ids = [(4, self.test_user.id)]

        with self.assertRaises(AccessError):
            self.journal_a.with_user(self.test_user).read(['name'])

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

    def test_pos_user_cannot_see_hidden_journal_but_can_read_payment_method(self):
        """Hiding a journal applies to POS users without hiding POS methods."""
        pos_user = self.env['res.users'].create({
            'name': 'Flous POS Journal User',
            'login': 'flous_pos_journal_user',
            'groups_id': [(6, 0, [
                self.internal_group.id,
                self.readonly_group.id,
                self.env.ref('point_of_sale.group_pos_user').id,
            ])],
        })
        payment_method = self.env['pos.payment.method'].create({
            'name': 'Flous POS payment method',
            'journal_id': self.journal_a.id,
        })
        self.journal_a.restricted_user_ids = [(4, pos_user.id)]

        visible = self.env['account.journal'].with_user(pos_user).search(
            [('id', '=', self.journal_a.id)])
        self.assertNotIn(self.journal_a, visible)
        self.assertIn(
            payment_method,
            self.env['pos.payment.method'].with_user(pos_user).search(
                [('id', '=', payment_method.id)]),
        )

        account = self.env['account.account'].create({
            'name': 'Flous POS Test Account',
            'code': '19992',
            'account_type': 'asset_current',
        })
        move = self.env['account.move'].create({
            'journal_id': self.journal_a.id,
            'line_ids': [
                (0, 0, {
                    'name': 'Flous POS test debit',
                    'account_id': account.id,
                    'debit': 50.0,
                }),
                (0, 0, {
                    'name': 'Flous POS test credit',
                    'account_id': account.id,
                    'credit': 50.0,
                }),
            ],
        })
        self.assertNotIn(
            move,
            self.env['account.move'].with_user(pos_user).search(
                [('id', '=', move.id)]),
            'POS membership must not bypass accounting entry visibility.',
        )
        self.assertFalse(
            self.env['account.move.line'].with_user(pos_user).search(
                [('move_id', '=', move.id)]),
            'POS membership must not bypass accounting line visibility.',
        )

        self.journal_b.restricted_user_ids = [(4, pos_user.id)]
        self.assertNotIn(
            self.journal_b,
            self.env['account.journal'].with_user(pos_user).search(
                [('id', '=', self.journal_b.id)]),
        )

    def test_hidden_cash_and_bank_journals_do_not_break_pos_session_loading(self):
        """Hidden POS payment journals stay hidden while the POS session still loads."""
        pos_user = self.env['res.users'].create({
            'name': 'Flous POS Session Visibility User',
            'login': 'flous_pos_session_visibility_user',
            'groups_id': [(6, 0, [
                self.internal_group.id,
                self.readonly_group.id,
                self.env.ref('point_of_sale.group_pos_user').id,
            ])],
        })
        company = self.env.company
        receivable = self.env['account.account'].create({
            'name': 'Flous POS Visibility Receivable',
            'code': '18980',
            'account_type': 'asset_receivable',
            'reconcile': True,
        })
        cash_account = self.env['account.account'].create({
            'name': 'Flous POS Visibility Cash',
            'code': '18981',
            'account_type': 'asset_cash',
        })
        bank_account = self.env['account.account'].create({
            'name': 'Flous POS Visibility Bank',
            'code': '18982',
            'account_type': 'asset_cash',
        })
        cash_journal = self.env['account.journal'].create({
            'name': 'Flous POS Visibility Cash',
            'type': 'cash',
            'code': 'FVC01',
            'company_id': company.id,
            'default_account_id': cash_account.id,
        })
        bank_journal = self.env['account.journal'].create({
            'name': 'Flous POS Visibility Bank',
            'type': 'bank',
            'code': 'FVB01',
            'company_id': company.id,
            'default_account_id': bank_account.id,
        })
        config = self.env['pos.config'].create({
            'name': 'Flous POS Hidden Journal Test',
        })
        cash_method = self.env['pos.payment.method'].create({
            'name': 'Flous POS Hidden Cash Method',
            'journal_id': cash_journal.id,
            'receivable_account_id': receivable.id,
            'company_id': company.id,
        })
        bank_method = self.env['pos.payment.method'].create({
            'name': 'Flous POS Hidden Bank Method',
            'journal_id': bank_journal.id,
            'receivable_account_id': receivable.id,
            'company_id': company.id,
        })
        config.write({
            'payment_method_ids': [(6, 0, [cash_method.id, bank_method.id])],
        })
        session = self.env['pos.session'].create({
            'config_id': config.id,
            'user_id': pos_user.id,
        })

        hidden_journals = config.journal_id | cash_journal | bank_journal
        hidden_journals.write({'restricted_user_ids': [(4, pos_user.id)]})

        visible_journals = self.env['account.journal'].with_user(pos_user).search(
            [('id', 'in', hidden_journals.ids)])
        self.assertFalse(
            visible_journals,
            'POS membership must not expose hidden sales, cash, or bank journals.',
        )
        self.assertTrue(all(journal.exists() for journal in hidden_journals))
        visible_methods = self.env['pos.payment.method'].with_user(pos_user).search(
            [('id', 'in', [cash_method.id, bank_method.id])])
        self.assertEqual(set(visible_methods.ids), {cash_method.id, bank_method.id})
        self.assertIn(
            config,
            self.env['pos.config'].with_user(pos_user).search([('id', '=', config.id)]),
        )

        pos_data = session.with_user(pos_user).load_data([], only_data=True)
        loaded_method_ids = {
            method['id'] for method in pos_data['pos.payment.method']['data']
        }
        self.assertTrue({cash_method.id, bank_method.id} <= loaded_method_ids)
        # A cash-controlled POS opens in opening_control before the cashier
        # confirms the opening balance; loading data at this step is expected.
        self.assertEqual(session.state, 'opening_control')

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

    def test_visibility_picker_hides_selected_journal_for_users(self):
        """The contextual picker applies restrictions to the selected journal."""
        action = self.env['flous.visibility.picker'].action_open_for_journal(
            self.journal_a.id,
        )
        wizard = self.env['flous.visibility.picker'].browse(action['res_id'])
        self.assertEqual(wizard.target_type, 'journal')
        self.assertEqual(wizard.journal_id, self.journal_a)
        self.assertIn('Flous Journal A', wizard.target_label)

        wizard.user_ids = [(6, 0, [self.test_user.id])]
        wizard.action_apply()

        self.assertIn(self.test_user, self.journal_a.restricted_user_ids)
        self.assertNotIn(self.journal_a, self._visible_journals(self.test_user))
        self.assertIn(self.journal_a, self._visible_journals(self.env.ref('base.user_admin')))

        reopen_action = self.env['flous.visibility.picker'].action_open_for_journal(
            self.journal_a.id,
        )
        reopened = self.env['flous.visibility.picker'].browse(reopen_action['res_id'])
        self.assertIn(self.test_user, reopened.user_ids)

    def test_non_admin_cannot_open_journal_picker(self):
        with self.assertRaises(AccessError):
            self.env['flous.visibility.picker'].with_user(self.test_user).action_open_for_journal(
                self.journal_a.id,
            )

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
