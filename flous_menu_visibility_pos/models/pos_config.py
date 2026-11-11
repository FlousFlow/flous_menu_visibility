# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


def _is_visible_for_user(selected_users, mode, user):
    selected = user in selected_users
    return not selected if mode == 'hide' else selected


class PosConfig(models.Model):
    _inherit = 'pos.config'

    restricted_user_ids = fields.Many2many(
        'res.users',
        relation='flous_pos_visibility_rel',
        column1='config_id',
        column2='user_id',
        string='Restricted Users',
        groups='base.group_system',
        domain=[('active', '=', True), ('share', '=', False)],
        help='These users cannot see or start this point of sale. '
             'Close any active session before applying a restriction.',
    )
    visibility_mode = fields.Selection(
        [('hide', 'Hide from selected users'), ('show', 'Show only to selected users')],
        string='Visibility Mode', required=True, default='hide',
        groups='base.group_system',
        help='Hide from selected users, or show this point of sale only to selected users.',
    )

    def _is_restricted_for_current_user(self):
        self.ensure_one()
        if self.env.user.has_group('base.group_system'):
            return False
        return not _is_visible_for_user(
            self.sudo().restricted_user_ids, self.sudo().visibility_mode, self.env.user
        )

    def _check_visibility_access(self):
        restricted = self.filtered(lambda config: config._is_restricted_for_current_user())
        if restricted:
            raise AccessError(
                _('You are not allowed to open this point of sale. Contact your administrator.')
            )

    @api.model_create_multi
    def create(self, vals_list):
        configs = super().create(vals_list)
        configs._remove_system_administrators_from_restrictions()
        return configs

    def write(self, vals):
        restriction_field_changed = (
            'restricted_user_ids' in vals or 'visibility_mode' in vals
        )
        previous_restrictions = {}
        if restriction_field_changed:
            previous_restrictions = {
                config.id: set(config.sudo().restricted_user_ids.ids)
                for config in self
            }
            with self.env.cr.savepoint():
                result = super().write(vals)
                for config in self:
                    config.invalidate_recordset(['current_session_id'])
                    newly_restricted = (
                        set(config.sudo().restricted_user_ids.ids)
                        - previous_restrictions[config.id]
                    )
                    if newly_restricted and config.current_session_id:
                        raise ValidationError(
                            _('Close the active POS session before restricting this point of sale. '
                              'This protects in-progress sales and unsynchronized orders.')
                        )
        else:
            result = super().write(vals)

        if restriction_field_changed:
            if not self.env.context.get('flous_skip_pos_visibility_admin_guard'):
                self._remove_system_administrators_from_restrictions()
            self.env.registry.clear_cache()
        return result

    def _remove_system_administrators_from_restrictions(self):
        for config in self.sudo():
            administrators = config.restricted_user_ids.filtered(
                lambda user: user.has_group('base.group_system')
            )
            if administrators:
                config.with_context(flous_skip_pos_visibility_admin_guard=True).write({
                    'restricted_user_ids': [(3, user.id) for user in administrators],
                })

    def action_open_ui(self):
        self._check_visibility_access()
        return super().action_open_ui()

    def open_ui(self):
        self._check_visibility_access()
        return super().open_ui()

    def open_session_if_not_opened(self):
        self._check_visibility_access()
        return super().open_session_if_not_opened()
