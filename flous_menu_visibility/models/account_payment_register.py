# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, models


class AccountPaymentRegister(models.TransientModel):
    """Keep payment-register defaults inside the user's visible journals."""

    _inherit = 'account.payment.register'

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
