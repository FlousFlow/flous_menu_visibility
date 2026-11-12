# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from .visibility_utils import visibility_mode_field


class FlousRecordHideRule(models.Model):
    """Presentation rule for one record in any Odoo model.

    The rule is consumed by the backend visibility picker for Kanban cards.
    It intentionally does not replace Odoo ACLs or record rules: the record can
    still be accessed through a permitted server-side route unless a standard
    security rule also denies it.
    """

    _name = 'flous.record.hide.rule'
    _description = 'Kanban Record Visibility Rule'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    visibility_mode = visibility_mode_field()
    model_id = fields.Many2one('ir.model', required=True, ondelete='cascade')
    model_name = fields.Char(related='model_id.model', store=True, readonly=True)
    record_id = fields.Integer(required=True, index=True)
    record_name = fields.Char(string='Record', required=True)
    user_ids = fields.Many2many('res.users', string='Users', required=True)
    user_count = fields.Integer(compute='_compute_user_count')

    @api.depends('user_ids')
    def _compute_user_count(self):
        for rule in self:
            rule.user_count = len(rule.user_ids)

    _sql_constraints = [
        ('model_record_unique', 'unique(model_id, record_id)',
         'A visibility rule for this record already exists.'),
    ]

    @api.model
    def get_hidden_record_ids(self, model_name, record_ids):
        """Return record ids hidden for the current user in the Kanban UI."""
        if self.env.user.has_group('base.group_system'):
            return []
        try:
            record_ids = [int(record_id) for record_id in record_ids]
        except (TypeError, ValueError):
            return []
        if not model_name or not record_ids:
            return []
        rules = self.sudo().search([
            ('active', '=', True),
            ('model_name', '=', model_name),
            ('record_id', 'in', record_ids),
        ])
        user_id = self.env.user.id
        hidden = rules.filtered(lambda rule: (
            rule.visibility_mode == 'hide' and user_id in rule.user_ids.ids
        ) or (
            rule.visibility_mode == 'show' and user_id not in rule.user_ids.ids
        ))
        return hidden.mapped('record_id')

