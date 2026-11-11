# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from lxml import etree

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestButtonHideRule(TransactionCase):
    def setUp(self):
        super().setUp()
        self.model = self.env['ir.model'].search([('model', '=', 'stock.picking')], limit=1)
        self.form = self.env.ref('stock.view_picking_form')
        self.user = self.env['res.users'].create({
            'name': 'Flous Button Test User',
            'login': 'flous_button_test_user',
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('stock.group_stock_user').id,
            ])],
        })
        form_view = self.env['stock.picking'].get_view(self.form.id, 'form')
        source_arch = etree.fromstring(form_view['arch'].encode())
        nodes = source_arch.xpath(".//button[@name][@type='object' or @type='action']")
        if not nodes:
            self.skipTest('The stock picking form has no selectable action button in this database')
        node = nodes[0]
        self.button_type = node.get('type')
        self.button_name = node.get('name')
        self.button_id = node.get('id') or False
        self.button_label = node.get('string') or self.button_name
        self.selector_key = '%s|%s|%s' % (
            self.button_type, self.button_name, self.button_id or '',
        )

    def _create_rule(self, users):
        return self.env['flous.button.hide.rule'].create({
            'name': 'Hide partner action button',
            'model_id': self.model.id,
            'button_type': self.button_type,
            'button_name': self.button_name,
            'button_id': self.button_id,
            'button_label': self.button_label,
            'selector_key': self.selector_key,
            'user_ids': [(6, 0, users)],
        })

    def _button_nodes(self, user):
        views = self.env['stock.picking'].with_user(user).get_views(
            [(self.form.id, 'form')]
        )
        arch = etree.fromstring(views['views']['form']['arch'].encode())
        xpath = ".//button[@name=$name][@type=$type]"
        if self.button_id:
            xpath += "[@id=$button_id]"
        return arch.xpath(
            xpath, name=self.button_name, type=self.button_type,
            button_id=self.button_id,
        )

    def test_button_hidden_only_for_selected_user(self):
        self._create_rule([self.user.id])

        target_nodes = self._button_nodes(self.user)
        self.assertTrue(target_nodes, 'The selected button remains in the view arch')
        self.assertTrue(
            all(node.get('invisible') == '1' for node in target_nodes),
            'Button rule did not match. Rule=%r buttons=%r' % (
                self.env['flous.button.hide.rule'].search([]).read([
                    'model_name', 'button_type', 'button_name', 'button_id', 'selector_key',
                ]),
                [node.attrib for node in target_nodes],
            ),
        )
        other = self.env['res.users'].create({
            'name': 'Flous Button Other User',
            'login': 'flous_button_other_user',
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('stock.group_stock_user').id,
            ])],
        })
        self.assertTrue(self._button_nodes(other))
        self.assertTrue(all(node.get('invisible') != '1' for node in self._button_nodes(other)))

    def test_system_administrator_always_sees_button(self):
        self._create_rule([self.user.id])
        admin_nodes = self._button_nodes(self.env.ref('base.user_admin'))
        self.assertTrue(admin_nodes)
        self.assertTrue(all(node.get('invisible') != '1' for node in admin_nodes))

    def test_picker_creates_rule_for_selected_users(self):
        action = self.env['flous.visibility.picker'].action_open_for_button(
            'stock.picking', self.button_name, self.button_type,
            self.button_id, self.button_label,
        )
        wizard = self.env['flous.visibility.picker'].browse(action['res_id'])
        wizard.user_ids = [(6, 0, [self.user.id])]
        wizard.action_apply()

        rule = self.env['flous.button.hide.rule'].search([
            ('model_id', '=', self.model.id), ('selector_key', '=', self.selector_key),
        ])
        self.assertEqual(rule.user_ids, self.user)

    def test_x2many_create_control_hides_without_hiding_the_field(self):
        move_form = self.env.ref('account.view_move_form')
        account_user = self.env['res.users'].create({
            'name': 'Flous Invoice Button User',
            'login': 'flous_invoice_button_user',
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('account.group_account_user').id,
            ])],
        })
        action = self.env['flous.visibility.picker'].action_open_for_button(
            'account.move',
            'create:invoice_line_ids:l',
            'create',
            False,
            'Add a line',
            'invoice_line_ids',
            'l',
        )
        wizard = self.env['flous.visibility.picker'].browse(action['res_id'])
        wizard.user_ids = [(6, 0, [account_user.id])]
        wizard.action_apply()

        views = self.env['account.move'].with_user(account_user).get_views(
            [(move_form.id, 'form')]
        )
        arch = etree.fromstring(views['views']['form']['arch'].encode())
        create_controls = arch.xpath(
            ".//field[@name='invoice_line_ids']//create[@data-hotkey='l' or @name='add_line_control']"
        )
        self.assertTrue(create_controls)
        self.assertTrue(all(node.get('invisible') == 'True' for node in create_controls))
        invoice_lines = arch.xpath(".//field[@name='invoice_line_ids']")
        self.assertTrue(invoice_lines)
        self.assertTrue(all(node.get('invisible') != '1' for node in invoice_lines))

    def test_non_admin_cannot_open_button_rule_picker(self):
        with self.assertRaises(AccessError):
            self.env['flous.visibility.picker'].with_user(self.user).action_open_for_button(
                'stock.picking', self.button_name, self.button_type,
                self.button_id, self.button_label,
            )
