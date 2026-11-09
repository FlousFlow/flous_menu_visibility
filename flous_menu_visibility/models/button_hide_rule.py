# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, _lt, fields, models


class FlousButtonHideRule(models.Model):
    """Hide a view button for selected users at view-render time."""

    _name = 'flous.button.hide.rule'
    _description = 'Button Visibility Rule'
    _order = 'sequence, id'

    name = fields.Char(string='Rule Name', required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade')
    model_name = fields.Char(
        string='Technical Model Name', related='model_id.model',
        store=True, readonly=True,
    )
    button_name = fields.Char(string='Technical Name', required=True)
    button_type = fields.Selection(
        [('object', 'Object Method'), ('action', 'Window Action')],
        required=True,
    )
    button_id = fields.Char(
        string='View Button ID',
        help='Optional XML ID attribute to distinguish this button.',
    )
    button_label = fields.Char(
        string='Button Label',
        help='Displayed for administrators; not used to match the button.',
    )
    selector_key = fields.Char(required=True, index=True)
    user_ids = fields.Many2many(
        'res.users', string='Users', required=True,
        help='Users for whom this button is hidden. System administrators always see it.',
    )
    user_count = fields.Integer(compute='_compute_user_count')

    _button_selector_unique = models.Constraint(
        'unique(model_id, selector_key)',
        _lt('A visibility rule for this button already exists. Edit the existing rule.'),
    )

    def _compute_user_count(self):
        for rule in self:
            rule.user_count = len(rule.user_ids)
