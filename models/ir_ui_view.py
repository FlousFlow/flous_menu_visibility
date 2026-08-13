# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models


class IrUiView(models.Model):
    """Hide fields for specific users at view-render time.

    Odoo 18 calls ``_postprocess_access_rights`` once per requested view,
    on the *combined* arch, *after* the (group-based) cache is read. This
    makes it the ideal single hook for per-user field visibility: the change
    is applied per request, so the shared view cache is never polluted.
    """

    _inherit = 'ir.ui.view'

    def _postprocess_access_rights(self, tree):
        # The root node carries the view model in 'model_access_rights';
        # the base implementation pops it, so read it before calling super.
        model_name = tree.get('model_access_rights')
        tree = super()._postprocess_access_rights(tree)

        if not model_name or self.env.user.has_group('base.group_system'):
            # System administrators always see every field.
            return tree
        if 'flous.field.hide.rule' not in self.env:
            # Safety net: rules model not (yet) registered.
            return tree

        rules = self.env['flous.field.hide.rule'].sudo().search([
            ('active', '=', True),
            ('user_ids', 'in', self.env.user.id),
        ])
        if not rules:
            return tree

        hidden_fields = {
            rule.field_id.name
            for rule in rules
            if rule.model_id.model == model_name
        }
        if not hidden_fields:
            return tree

        # Set invisible="1" instead of removing the node: the field's value
        # stays loaded, so expressions/domains referencing it keep working
        # and the view layout is not broken.
        for node in tree.xpath(".//field[@name]"):
            if node.get('name') in hidden_fields:
                node.set('invisible', '1')
        return tree
