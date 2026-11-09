# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models


class IrUiView(models.Model):
    """Hide configured fields and buttons at view-render time.

    Odoo 20 calls ``_postprocess_access_rights`` once per requested view,
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
        hidden_fields = set()
        if 'flous.field.hide.rule' in self.env:
            rules = self.env['flous.field.hide.rule'].sudo().search([
                ('active', '=', True),
                ('user_ids', 'in', self.env.user.id),
            ])
            # Ignore incomplete/stale rules defensively.
            hidden_fields = {
                rule.field_id.name
                for rule in rules
                if rule.field_id and rule.model_id
                and rule.model_id.model == model_name
            }

        # Set invisible="1" instead of removing the node: the field's value
        # stays loaded, so expressions/domains referencing it keep working
        # and the view layout is not broken.
        if hidden_fields:
            for node in tree.xpath(".//field[@name]"):
                if node.get('name') in hidden_fields:
                    node.set('invisible', '1')

        if 'flous.button.hide.rule' in self.env:
            button_rules = self.env['flous.button.hide.rule'].sudo().search([
                ('active', '=', True),
                ('user_ids', 'in', self.env.user.id),
                ('model_name', '=', model_name),
            ])
            rules_by_selector = {
                (rule.button_type, rule.button_name, rule.button_id or '')
                for rule in button_rules
                if rule.button_type in ('object', 'action')
            }
            for node in tree.xpath(".//button[@name][@type='object' or @type='action']"):
                selector = (node.get('type'), node.get('name'), node.get('id') or '')
                if selector in rules_by_selector:
                    node.set('invisible', '1')

            create_rules = button_rules.filtered(
                lambda rule: rule.button_type == 'create'
                and rule.button_field_name
            )
            create_selectors_by_hotkey = {
                (rule.button_field_name, rule.button_hotkey)
                for rule in create_rules
                if rule.button_hotkey
            }
            create_selectors_by_label = {
                (rule.button_field_name, rule.button_label)
                for rule in create_rules
                if not rule.button_hotkey and rule.button_label
            }
            for field_node in tree.xpath(".//field[@name]"):
                field_name = field_node.get('name')
                for list_node in field_node.xpath(".//list"):
                    create_nodes = list_node.xpath("./control/create")
                    if not create_nodes:
                        # Odoo generates a default Add a line control when a
                        # relational list has no explicit <control> section.
                        if (field_name, 'shift+l') in create_selectors_by_hotkey:
                            list_node.set('create', 'False')
                        continue
                    for create_node in create_nodes:
                        hotkey = create_node.get('data-hotkey')
                        if (
                            (hotkey and (field_name, hotkey) in create_selectors_by_hotkey)
                            or (
                                not hotkey
                                and (field_name, create_node.get('string'))
                                in create_selectors_by_label
                            )
                        ):
                            create_node.set('invisible', 'True')
        return tree
