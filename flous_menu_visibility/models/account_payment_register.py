# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, models


class AccountPaymentRegister(models.TransientModel):
    """Keep payment-register defaults inside the user's visible journals."""

    _inherit = 'account.payment.register'

    @staticmethod
    def _m2o_id(value):
        """Return an id from the representations used by web onchange calls."""
        if isinstance(value, dict):
            return value.get('id')
        if isinstance(value, (list, tuple)):
            return value[0] if value else False
        return value

    def _sanitize_inaccessible_payment_values(self, values):
        """Remove stale hidden payment values sent by the web client.

        When the user changes a payment journal, the browser can submit the
        journal that was selected before the visibility rule was applied. Odoo
        reads that value while building its onchange snapshot, so record rules
        raise an access error before the normal journal domain can recover.
        """
        values = dict(values)
        # These are computed domains.  The browser keeps their previous values
        # in its onchange snapshot, which can include a journal that became
        # hidden after the wizard was opened.  Never trust that client cache:
        # let Odoo recompute it under the current user's record rules.
        for field_name in (
            'available_journal_ids',
            'available_payment_method_line_ids',
            'available_partner_bank_ids',
        ):
            values.pop(field_name, None)

        journal_id = self._m2o_id(values.get('journal_id'))
        if journal_id and not self.env['account.journal'].search([
            ('id', '=', journal_id),
            ('type', 'in', ('bank', 'cash', 'credit')),
        ], limit=1):
            # Keep the key because web's onchange marks it as modified.
            values['journal_id'] = False

        method_line_id = self._m2o_id(values.get('payment_method_line_id'))
        if method_line_id:
            method_line = self.env['account.payment.method.line'].sudo().browse(
                method_line_id
            ).exists()
            method_journal_id = method_line.journal_id.id
            if not method_line or not self.env['account.journal'].search([
                ('id', '=', method_journal_id),
                ('type', 'in', ('bank', 'cash', 'credit')),
            ], limit=1):
                values['payment_method_line_id'] = False
        return values

    def onchange(self, values, field_names, fields_spec):
        """Prevent a stale hidden journal from aborting payment onchange."""
        sanitized_values = self._sanitize_inaccessible_payment_values(values)
        return super().onchange(
            sanitized_values,
            field_names,
            fields_spec,
        )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        journal_id = values.get('journal_id')
        if journal_id:
            visible_journals = self.env['account.journal'].search([
                ('id', '=', journal_id),
                ('type', 'in', ('bank', 'cash', 'credit')),
            ])
            if not visible_journals:
                values.pop('journal_id', None)
        return values

    @api.model_create_multi
    def create(self, vals_list):
        wizards = super().create(vals_list)
        for wizard in wizards:
            available = wizard.available_journal_ids
            if wizard.journal_id.id not in available.ids:
                wizard.journal_id = available.filtered(
                    lambda journal: journal.type in ('bank', 'cash', 'credit')
                )[:1]
        return wizards

    @api.depends('available_journal_ids')
    def _compute_journal_id(self):
        for wizard in self:
            available = wizard.available_journal_ids
            available_ids = set(available.ids)
            if wizard.journal_id.id in available_ids:
                continue

            # Odoo normally prefers the journal from the invoice's preferred
            # payment method. That journal may be hidden by this module.
            preferred = wizard.line_ids.move_id.preferred_payment_method_line_id.filtered(
                lambda line: line.sudo().journal_id.id in available_ids
            )
            if preferred and len(preferred) == 1:
                wizard.journal_id = preferred.journal_id
                continue

            candidate = False
            if wizard.can_edit_wizard and wizard.batches:
                candidate = wizard._get_batch_journal(wizard.batches[0])
            if candidate and candidate.id in available_ids:
                wizard.journal_id = candidate
                continue

            # Never browse or assign a journal outside the user's visible set.
            wizard.journal_id = available.filtered(
                lambda journal: journal.type in ('bank', 'cash', 'credit')
            )[:1]
