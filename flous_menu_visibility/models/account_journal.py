# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class AccountJournal(models.Model):
    """Inverse side of ``res.users.hidden_journal_ids``.

    Both fields share the relation table ``flous_journal_visibility_rel``.
    """

    _inherit = 'account.journal'

    restricted_user_ids = fields.Many2many(
        'res.users',
        relation='flous_journal_visibility_rel',
        column1='journal_id',
        column2='user_id',
        string='Restricted Users',
        groups='base.group_system',
        help='Users for whom this journal will be hidden.',
    )

    def write(self, vals):
        res = super().write(vals)
        if 'restricted_user_ids' in vals:
            # ir.rule domains are cached per user (uid). Invalidate the
            # registry cache so the new restrictions apply immediately.
            self.env.registry.clear_cache()
            # Defense in depth: the administrator is never restricted.
            if not self.env.context.get('flous_skip_admin_guard'):
                admin = self.env.ref('base.user_admin')
                restricted = self.filtered(lambda j: admin in j.restricted_user_ids)
                if restricted:
                    restricted.with_context(flous_skip_admin_guard=True).sudo().write(
                        {'restricted_user_ids': [(3, admin.id)]})
        return res
