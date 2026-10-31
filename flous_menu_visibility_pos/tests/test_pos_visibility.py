# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from lxml import etree

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase
from odoo.tools.safe_eval import safe_eval


class TestPosVisibility(TransactionCase):
    def setUp(self):
        super().setUp()
        groups = [
            self.env.ref('base.group_user').id,
            self.env.ref('point_of_sale.group_pos_user').id,
        ]
        self.user = self.env['res.users'].create({
            'name': 'Flous POS Visibility User',
            'login': 'flous_pos_visibility_user',
            'group_ids': [(6, 0, groups)],
        })
        self.other_user = self.env['res.users'].create({
            'name': 'Flous POS Other User',
            'login': 'flous_pos_other_user',
            'group_ids': [(6, 0, groups)],
        })
        config_defaults = {'payment_method_ids': [(5, 0, 0)]}
        self.config_a = self.env['pos.config'].create({
            **config_defaults, 'name': 'Flous POS A',
        })
        self.config_b = self.env['pos.config'].create({
            **config_defaults, 'name': 'Flous POS B',
        })

    def _visible_configs(self, user):
        return self.env['pos.config'].with_user(user).search([
            ('id', 'in', (self.config_a | self.config_b).ids),
        ])

    def test_visibility_management_lists_existing_pos_without_create(self):
        action = self.env.ref(
            'flous_menu_visibility_pos.action_visibility_pos_config'
        ).read()[0]
        list_arch = etree.fromstring(
            self.env.ref('flous_menu_visibility_pos.view_visibility_pos_config_list').arch_db
        )
        kanban_arch = etree.fromstring(
            self.env.ref('flous_menu_visibility_pos.view_visibility_pos_config_kanban').arch_db
        )
        form_arch = etree.fromstring(
            self.env.ref('flous_menu_visibility_pos.view_visibility_pos_config_form').arch_db
        )

        self.assertIn('list', action['view_mode'])
        self.assertIn('kanban', action['view_mode'])
        self.assertIn('form', action['view_mode'])
        self.assertEqual(action['mobile_view_mode'], 'kanban')
        self.assertFalse(safe_eval(action.get('domain') or '[]'))
        self.assertFalse(safe_eval(action.get('context') or '{}').get('create', True))
        self.assertEqual(list_arch.get('create'), '0')
        self.assertEqual(kanban_arch.get('create'), '0')
        self.assertEqual(form_arch.get('create'), '0')
        self.assertIsNotNone(form_arch.find(".//field[@name='restricted_user_ids']"))

    def test_restricted_config_is_hidden_and_other_config_remains(self):
        self.config_a.restricted_user_ids = [(4, self.user.id)]

        visible = self._visible_configs(self.user)

        self.assertNotIn(self.config_a, visible)
        self.assertIn(self.config_b, visible)

    def test_other_user_is_not_affected(self):
        self.config_a.restricted_user_ids = [(4, self.user.id)]

        self.assertIn(self.config_a, self._visible_configs(self.other_user))

    def test_system_administrator_always_sees_restricted_config(self):
        self.config_a.restricted_user_ids = [(4, self.user.id)]
        admin = self.env.ref('base.user_admin')

        self.assertIn(self.config_a, self._visible_configs(admin))
        self.config_a.with_user(admin)._check_visibility_access()
        with self.assertRaises(AccessError):
            self.config_a.with_user(self.user).open_ui()

    def test_restricted_user_cannot_open_pos(self):
        self.config_a.restricted_user_ids = [(4, self.user.id)]

        with self.assertRaises(AccessError):
            self.config_a.with_user(self.user).action_open_ui()
