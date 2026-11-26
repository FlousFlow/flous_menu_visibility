# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, models


class AccountPaymentRegister(models.TransientModel):
    """Keep payment-register defaults inside the user's visible journals."""

    _inherit = 'account.payment.register'

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
