# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


class PosConfig(models.Model):
    _inherit = 'pos.config'

    restricted_user_ids = fields.Many2many(
        'res.users', relation='flous_pos_visibility_rel',
        column1='config_id', column2='user_id', string='Restricted Users',
        groups='base.group_system', domain=[('active', '=', True), ('share', '=', False)],
        help='Users restricted from seeing or opening this point of sale.',
    )
    visibility_mode = fields.Selection(
        [('hide', 'Hide from selected users'), ('show', 'Show only to selected users')],
        string='Visibility Mode', required=True, default='hide', groups='base.group_system',
    )

    def _is_restricted_for_current_user(self):
        self.ensure_one()
        if self.env.user.has_group('base.group_system'):
            return False
        selected = self.env.user in self.sudo().restricted_user_ids
        visible = not selected if self.sudo().visibility_mode == 'hide' else selected
        return not visible

    def _check_visibility_access(self):
        if self.filtered(lambda config: config._is_restricted_for_current_user()):
            raise AccessError(_('You are not allowed to open this point of sale. Contact your administrator.'))

    @api.model_create_multi
    def create(self, vals_list):
        configs = super().create(vals_list)
        configs._remove_system_administrators_from_restrictions()
        return configs

    def write(self, vals):
        changed = 'restricted_user_ids' in vals or 'visibility_mode' in vals
        previous = {config.id: set(config.sudo().restricted_user_ids.ids) for config in self} if changed else {}
        result = super().write(vals)
        if changed:
            for config in self:
                config.invalidate_recordset(['current_session_id'])
                newly_restricted = set(config.sudo().restricted_user_ids.ids) - previous[config.id]
                if newly_restricted and config.current_session_id:
                    raise ValidationError(_('Close the active POS session before restricting this point of sale.'))
            if not self.env.context.get('flous_skip_pos_visibility_admin_guard'):
                self._remove_system_administrators_from_restrictions()
            self.env.registry.clear_cache()
        return result

    def _remove_system_administrators_from_restrictions(self):
        for config in self.sudo():
            admins = config.restricted_user_ids.filtered(lambda user: user.has_group('base.group_system'))
            if admins:
                config.with_context(flous_skip_pos_visibility_admin_guard=True).write({
                    'restricted_user_ids': [(3, user.id) for user in admins],
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
