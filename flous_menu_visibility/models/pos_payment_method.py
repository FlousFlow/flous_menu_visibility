# -*- coding: utf-8 -*-
"""Keep POS payment-method bootstrap independent from journal visibility."""

from odoo import models


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    def _load_pos_data(self, data):
        """Load payment methods without exposing their accounting journals.

        Odoo's POS payload contains payment-method metadata, while the
        accounting journal remains protected by the journal record rule. A
        journal may therefore be hidden in Accounting and still be usable as
        the backing journal for a POS payment method. Sudo is scoped to this
        bootstrap payload only; normal ORM reads and accounting operations
        remain subject to the user's rules.
        """
        return super(PosPaymentMethod, self.sudo())._load_pos_data(data)
