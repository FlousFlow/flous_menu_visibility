# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class FlousVisibilityPicker(models.TransientModel):
    _name = 'flous.visibility.picker'
    _description = 'Visibility Rule User Selection'

    target_type = fields.Selection(
        [
            ('field', 'Field'),
            ('menu', 'Menu'),
            ('button', 'Button'),
            ('journal', 'Journal'),
            ('pos_config', 'Point of Sale'),
        ],
        required=True,
        readonly=True,
    )
    model_id = fields.Many2one('ir.model', readonly=True)
    field_id = fields.Many2one('ir.model.fields', readonly=True)
    menu_id = fields.Many2one('ir.ui.menu', readonly=True)
    journal_id = fields.Many2one('account.journal', readonly=True)
    pos_config_id = fields.Many2one('pos.config', readonly=True)
    button_name = fields.Char(readonly=True)
    button_type = fields.Selection(
        [
            ('object', 'Object Method'),
            ('action', 'Window Action'),
            ('create', 'Add Line Control'),
        ],
        readonly=True,
    )
    button_id = fields.Char(readonly=True)
    button_field_name = fields.Char(readonly=True)
    button_hotkey = fields.Char(readonly=True)
    button_selector_key = fields.Char(readonly=True)
    button_label = fields.Char(readonly=True)
    visibility_mode = fields.Selection(
        [('hide', 'Hide from selected users'), ('show', 'Show only to selected users')],
        string='Visibility Mode', required=True, default='hide',
        help='Choose whether the selected users are hidden or are the only users allowed to see the item.',
    )
    target_label = fields.Char(compute='_compute_target_label')
    user_ids = fields.Many2many(
        'res.users', string='Selected Users',
        domain="[('id', 'in', eligible_user_ids)]",
        help='Select the internal users who should not see this item. '
             'System administrators always retain visibility.',
    )
    eligible_user_ids = fields.Many2many(
        'res.users', compute='_compute_eligible_user_ids',
    )
    selected_user_count = fields.Integer(
        string='Selected Users', compute='_compute_selected_user_count',
    )

    def _get_eligible_users(self):
        users = self.env['res.users'].search([
            ('active', '=', True), ('share', '=', False),
        ])
        return users.filtered(lambda user: not user.has_group('base.group_system'))

    @api.depends('target_type')
    def _compute_eligible_user_ids(self):
        eligible_users = self._get_eligible_users()
        for wizard in self:
            wizard.eligible_user_ids = eligible_users

    @api.depends('user_ids')
    def _compute_selected_user_count(self):
        for wizard in self:
            wizard.selected_user_count = len(wizard.user_ids)

    @api.onchange('user_ids')
    def _onchange_user_ids(self):
        """Keep system administrators out of the restriction selection."""
        for wizard in self:
            wizard.user_ids = wizard.user_ids.filtered(
                lambda user: not user.has_group('base.group_system')
            )

    def action_select_all_users(self):
        self.ensure_one()
        self.user_ids = [(6, 0, self._get_eligible_users().ids)]
        return self._get_dialog_action()

    def action_clear_users(self):
        self.ensure_one()
        self.user_ids = [(5, 0, 0)]
        return self._get_dialog_action()

    @api.depends(
        'target_type', 'model_id', 'field_id.field_description',
        'menu_id.complete_name',
        'journal_id.display_name',
        'pos_config_id.display_name',
        'button_label', 'button_name',
    )
    def _compute_target_label(self):
        for wizard in self:
            if wizard.target_type == 'field' and wizard.field_id:
                wizard.target_label = '%s · %s' % (
                    wizard.model_id.name, wizard.field_id.field_description,
                )
            elif wizard.target_type == 'menu' and wizard.menu_id:
                wizard.target_label = wizard.menu_id.complete_name
            elif wizard.target_type == 'journal' and wizard.journal_id:
                wizard.target_label = wizard.journal_id.display_name
            elif wizard.target_type == 'pos_config' and wizard.pos_config_id:
                wizard.target_label = wizard.pos_config_id.display_name
            elif wizard.target_type == 'button' and wizard.model_id:
                wizard.target_label = '%s · %s' % (
                    wizard.model_id.name, wizard.button_label or wizard.button_name,
                )
            else:
                wizard.target_label = ''

    @api.model
    def _check_visibility_admin(self):
        if not self.env.user.has_group('base.group_system'):
            raise AccessError(_('Only system administrators can configure visibility rules.'))

    @api.model
    def action_open_for_field(self, model_name, field_name):
        self._check_visibility_admin()
        model = self.env['ir.model'].sudo().search([('model', '=', model_name)], limit=1)
        field = self.env['ir.model.fields'].sudo().search([
            ('model_id', '=', model.id), ('name', '=', field_name),
        ], limit=1) if model else self.env['ir.model.fields']
        if not model or not field:
            raise UserError(_('The selected field could not be identified.'))
        if field.required:
            raise UserError(_('Required fields cannot be hidden because the form may no longer be saveable.'))

        rule = self.env['flous.field.hide.rule'].sudo().search([
            ('model_id', '=', model.id), ('field_id', '=', field.id),
        ], limit=1)
        wizard = self.sudo().create({
            'target_type': 'field',
            'model_id': model.id,
            'field_id': field.id,
            'visibility_mode': rule.visibility_mode if rule and rule.active else 'hide',
            'user_ids': [(6, 0, rule.user_ids.ids if rule and rule.active else [])],
        })
        return wizard._get_dialog_action()

    @api.model
    def action_open_for_menu(self, menu_xmlid):
        self._check_visibility_admin()
        menu = self.env.ref(menu_xmlid, raise_if_not_found=False)
        if not menu or menu._name != 'ir.ui.menu':
            raise UserError(_('The selected menu could not be identified.'))
        wizard = self.sudo().create({
            'target_type': 'menu',
            'menu_id': menu.id,
            'visibility_mode': menu.visibility_mode,
            'user_ids': [(6, 0, menu.restricted_user_ids.ids)],
        })
        return wizard._get_dialog_action()

    @api.model
    def action_open_for_journal(self, journal_id):
        self._check_visibility_admin()
        try:
            journal_id = int(journal_id)
        except (TypeError, ValueError):
            journal_id = 0
        journal = self.env['account.journal'].sudo().browse(journal_id).exists()
        if not journal:
            raise UserError(_('The selected journal could not be identified.'))
        wizard = self.sudo().create({
            'target_type': 'journal',
            'journal_id': journal.id,
            'visibility_mode': journal.visibility_mode,
            'user_ids': [(6, 0, journal.restricted_user_ids.ids)],
        })
        return wizard._get_dialog_action()

    @api.model
    def action_open_for_pos_config(self, pos_config_id):
        self._check_visibility_admin()
        try:
            pos_config_id = int(pos_config_id)
        except (TypeError, ValueError):
            pos_config_id = 0
        config = self.env['pos.config'].sudo().browse(pos_config_id).exists()
        if not config:
            raise UserError(_('The selected point of sale could not be identified.'))
        wizard = self.sudo().create({
            'target_type': 'pos_config',
            'pos_config_id': config.id,
            'visibility_mode': config.visibility_mode,
            'user_ids': [(6, 0, config.restricted_user_ids.ids)],
        })
        return wizard._get_dialog_action()

    @api.model
    def action_open_for_button(
        self, model_name, button_name, button_type, button_id=False, button_label=False,
        button_field_name=False, button_hotkey=False,
    ):
        self._check_visibility_admin()
        if button_type not in ('object', 'action', 'create'):
            raise UserError(_('Only form and list view action buttons can be hidden.'))
        if button_type == 'create':
            if not button_field_name:
                raise UserError(_('The selected list control could not be identified.'))
            button_name = button_name or 'create:%s:%s' % (
                button_field_name, button_hotkey or button_label or '',
            )
        elif not button_name:
            raise UserError(_('The selected button could not be identified.'))
        model = self.env['ir.model'].sudo().search([('model', '=', model_name)], limit=1)
        if not model:
            raise UserError(_('The selected button could not be identified.'))
        # Labels are translated and therefore deliberately excluded from the key.
        selector_key = (
            'create|%s|%s' % (button_field_name, button_hotkey or button_label or '')
            if button_type == 'create'
            else '%s|%s|%s' % (button_type, button_name, button_id or '')
        )
        rule = self.env['flous.button.hide.rule'].sudo().search([
            ('model_id', '=', model.id), ('selector_key', '=', selector_key),
        ], limit=1)
        wizard = self.sudo().create({
            'target_type': 'button',
            'model_id': model.id,
            'button_name': button_name,
            'button_type': button_type,
            'button_id': button_id or False,
            'button_field_name': button_field_name or False,
            'button_hotkey': button_hotkey or False,
            'button_label': button_label or button_name,
            'button_selector_key': selector_key,
            'visibility_mode': rule.visibility_mode if rule and rule.active else 'hide',
            'user_ids': [(6, 0, rule.user_ids.ids if rule and rule.active else [])],
        })
        return wizard._get_dialog_action()

    def _get_dialog_action(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Visibility Rule'),
            'res_model': self._name,
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def action_apply(self):
        self.ensure_one()
        self._check_visibility_admin()
        selected_users = self.user_ids.filtered(
            lambda user: user.active and not user.share
        )
        selected_users = selected_users.filtered(
            lambda user: not user.has_group('base.group_system')
        )

        if self.target_type == 'menu':
            self.menu_id.sudo().write({
                'restricted_user_ids': [(6, 0, selected_users.ids)],
                'visibility_mode': self.visibility_mode,
            })
        elif self.target_type == 'journal':
            self.journal_id.sudo().write({
                'restricted_user_ids': [(6, 0, selected_users.ids)],
                'visibility_mode': self.visibility_mode,
            })
        elif self.target_type == 'pos_config':
            self.pos_config_id.sudo().write({
                'restricted_user_ids': [(6, 0, selected_users.ids)],
                'visibility_mode': self.visibility_mode,
            })
        elif self.target_type == 'field':
            rule = self.env['flous.field.hide.rule'].sudo().search([
                ('model_id', '=', self.model_id.id), ('field_id', '=', self.field_id.id),
            ], limit=1)
            values = {
                'name': _('Hide %s from selected users') % self.field_id.field_description,
                'model_id': self.model_id.id,
                'field_id': self.field_id.id,
                'user_ids': [(6, 0, selected_users.ids)],
                'visibility_mode': self.visibility_mode,
                'active': True,
            }
            if rule:
                rule.write(values)
            else:
                self.env['flous.field.hide.rule'].sudo().create(values)
        elif self.target_type == 'button':
            rule = self.env['flous.button.hide.rule'].sudo().search([
                ('model_id', '=', self.model_id.id),
                ('selector_key', '=', self.button_selector_key),
            ], limit=1)
            values = {
                'name': _('Hide %s from selected users') % (self.button_label or self.button_name),
                'model_id': self.model_id.id,
                'button_name': self.button_name,
                'button_type': self.button_type,
                'button_id': self.button_id or False,
                'button_field_name': self.button_field_name or False,
                'button_hotkey': self.button_hotkey or False,
                'button_label': self.button_label or self.button_name,
                'selector_key': self.button_selector_key,
                'user_ids': [(6, 0, selected_users.ids)],
                'visibility_mode': self.visibility_mode,
                'active': True,
            }
            if rule:
                rule.write(values)
            else:
                self.env['flous.button.hide.rule'].sudo().create(values)
        else:
            raise UserError(_('The selected item type is not supported.'))
        return {'type': 'ir.actions.act_window_close'}
