# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from lxml import etree

from odoo.tests.common import TransactionCase


class TestFieldHideRule(TransactionCase):
    """Verify that fields are hidden per user without breaking the view."""

    def setUp(self):
        super().setUp()
        self.internal_group = self.env.ref('base.group_user')
        self.partner_model = self.env['ir.model'].search(
            [('model', '=', 'res.partner')], limit=1)
        self.name_field = self.env['ir.model.fields'].search(
            [('model', '=', 'res.partner'), ('name', '=', 'name')], limit=1)
        self.test_user = self.env['res.users'].create({
            'name': 'Flous Field Test User',
            'login': 'flous_field_test_user',
            'groups_id': [(6, 0, [self.internal_group.id])],
        })
        self.partner_form = self.env.ref('base.view_partner_form')

    def _new_internal_user(self, login):
        return self.env['res.users'].create({
            'name': 'Flous Field ' + login,
            'login': login,
            'groups_id': [(6, 0, [self.internal_group.id])],
        })

    def _create_rule(self, user_ids):
        return self.env['flous.field.hide.rule'].create({
            'name': 'Hide partner name',
            'model_id': self.partner_model.id,
            'field_id': self.name_field.id,
            'user_ids': [(6, 0, user_ids)],
        })

    def _get_arch(self, user):
        """Load the partner form the same way the web client does: the
        ``get_views`` RPC is called on the *view's model* (res.partner),
        not on ir.ui.view (which internal users cannot read).
        """
        result = self.env['res.partner'].with_user(user).get_views(
            [(self.partner_form.id, 'form')])
        return etree.fromstring(result['views']['form']['arch'])

    def _node_invisible(self, arch):
        node = arch.xpath("//field[@name='name']")[0]
        return node.get('invisible') == '1'

    def test_field_visible_by_default(self):
        """Without a rule the field is visible for internal users."""
        arch = self._get_arch(self.test_user)
        self.assertFalse(self._node_invisible(arch))

    def test_field_hidden_for_restricted_user(self):
        """With an active rule the field gets invisible for the target user."""
        self._create_rule([self.test_user.id])
        arch = self._get_arch(self.test_user)
        self.assertTrue(self._node_invisible(arch))

    def test_field_visible_for_other_user(self):
        """The rule only affects the users listed in it."""
        self._create_rule([self.test_user.id])
        other = self._new_internal_user('flous_field_other_user')
        arch = self._get_arch(other)
        self.assertFalse(self._node_invisible(arch))

    def test_admin_always_sees_field(self):
        """System administrators are never restricted."""
        self._create_rule([self.test_user.id])
        admin = self.env.ref('base.user_admin')
        arch = self._get_arch(admin)
        self.assertFalse(self._node_invisible(arch))

    def test_inactive_rule_does_not_hide(self):
        """Archived rules have no effect."""
        rule = self._create_rule([self.test_user.id])
        rule.active = False
        arch = self._get_arch(self.test_user)
        self.assertFalse(self._node_invisible(arch))

    def test_view_is_not_broken(self):
        """Hiding sets invisible and keeps the field node in the arch."""
        self._create_rule([self.test_user.id])
        arch = self._get_arch(self.test_user)
        nodes = arch.xpath("//field[@name='name']")
        self.assertTrue(nodes, "Field node must remain in the arch")
        for node in nodes:
            self.assertEqual(node.get('invisible'), '1')

    def test_unique_rule_per_model_field(self):
        """Only one rule per (model, field) is allowed."""
        self._create_rule([self.test_user.id])
        with self.assertRaises(Exception):
            self._create_rule([self.test_user.id])
