# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models
from .visibility_utils import visibility_mode_field


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
    visibility_mode = visibility_mode_field(groups='base.group_system')

    @api.model
    def _ensure_pos_journal(self, code, name):
        """Let POS resolve its company journal independently of UI visibility.

        The global journal visibility rule is for users browsing accounting
        records. Odoo calls this helper during POS session closing too; without
        sudo, a hidden existing journal is missed and Odoo attempts to create
        a duplicate company/code pair.
        """
        return super(AccountJournal, self.sudo())._ensure_pos_journal(code, name)

    def write(self, vals):
        res = super().write(vals)
        if 'restricted_user_ids' in vals or 'visibility_mode' in vals:
            # ir.access domains are cached per user (uid). Invalidate the
            # registry cache so the new restrictions apply immediately.
            self.env.transaction.invalidate_access_cache()
            # Defense in depth: every system administrator is never restricted.
            if not self.env.context.get('flous_skip_admin_guard'):
                for journal in self:
                    admins = journal.restricted_user_ids.filtered(
                        lambda user: user.has_group('base.group_system'))
                    if admins:
                        journal.with_context(flous_skip_admin_guard=True).sudo().write(
                            {'restricted_user_ids': [(3, uid) for uid in admins.ids]})
        return res
