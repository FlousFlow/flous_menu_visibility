# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FlousFieldHideRule(models.Model):
    """Rule that hides a specific field of a model from a set of users.

    The rule is applied at view-render time inside
    ``ir.ui.view._postprocess_access_rights``, by setting ``invisible="1"``
    on the matching ``<field>`` nodes. Hiding (rather than removing) the
    node keeps the field's value loaded, so other view expressions and
    domains that reference the field keep working — the view is not broken.
    """

    _name = 'flous.field.hide.rule'
    _description = 'Field Visibility Rule'
    _order = 'sequence, id'

    name = fields.Char(
        string='Rule Name', required=True, tracking=True,
        help='A short name describing this rule, e.g. "Hide cost price from sales".',
    )
    active = fields.Boolean(string='Active', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)

    model_id = fields.Many2one(
        'ir.model', string='Model', required=True, ondelete='cascade',
        domain="[('transient', '=', False)]",
        help='The model containing the field to hide.',
    )
    model_name = fields.Char(
        string='Model Name', related='model_id.model', readonly=True, store=True,
    )
    field_id = fields.Many2one(
        'ir.model.fields', string='Field', required=True, ondelete='cascade',
        domain="[('model_id', '=', model_id)]",
        help='The field to hide (e.g. list_price, standard_price).',
    )
    field_name = fields.Char(
        string='Field Name', related='field_id.name', readonly=True, store=True,
    )
    field_string = fields.Char(
        string='Field Label', related='field_id.field_description', readonly=True,
    )

    user_ids = fields.Many2many(
        'res.users', string='Users',
        required=True,
        help='Users for whom this field will be hidden. System administrators '
             'always see every field.',
    )
    notes = fields.Text(string='Notes')

    _model_field_unique = models.Constraint(
        'unique(model_id, field_id)',
        _('A rule for this model/field already exists. Edit the existing rule '
          'to change the list of users instead of creating a duplicate.'),
    )

    @api.constrains('model_id', 'field_id')
    def _check_field_belongs_to_model(self):
        for rule in self:
            if rule.field_id and rule.model_id \
                    and rule.field_id.model_id != rule.model_id:
                raise ValidationError(
                    _('The selected field does not belong to the selected model.')
                )

    @api.onchange('model_id')
    def _onchange_model_id(self):
        """Reset the field when the model changes."""
        self.field_id = False
