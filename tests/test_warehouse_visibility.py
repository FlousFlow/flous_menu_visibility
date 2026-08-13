# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo.tests.common import TransactionCase


class TestWarehouseVisibility(TransactionCase):
    """Verify that users in the Warehouse Visibility group only see the
    operations of their assigned warehouses."""

    def setUp(self):
        super().setUp()
        self.internal_group = self.env.ref('base.group_user')
        self.stock_user_group = self.env.ref('stock.group_stock_user')
        self.wh_group = self.env.ref(
            'flous_menu_visibility.group_warehouse_visibility')

        self.wh_a = self.env['stock.warehouse'].create({
            'name': 'Flous WH A', 'code': 'FWA',
        })
        self.wh_b = self.env['stock.warehouse'].create({
            'name': 'Flous WH B', 'code': 'FWB',
        })

        # One operation per warehouse (as in a two-step inter-warehouse
        # transfer: step 1 is a picking of warehouse A, step 2 of warehouse B).
        self.picking_a = self.env['stock.picking'].create({
            'picking_type_id': self.wh_a.int_type_id.id,
            'location_id': self.wh_a.lot_stock_id.id,
            'location_dest_id': self.wh_a.lot_stock_id.id,
        })
        self.picking_b = self.env['stock.picking'].create({
            'picking_type_id': self.wh_b.int_type_id.id,
            'location_id': self.wh_b.lot_stock_id.id,
            'location_dest_id': self.wh_b.lot_stock_id.id,
        })

        self.user_a = self._new_user(
            'flous_wh_user_a', restricted=True, warehouse_ids=[self.wh_a.id])
        self.user_b = self._new_user(
            'flous_wh_user_b', restricted=True, warehouse_ids=[self.wh_b.id])

    def _new_user(self, login, restricted=False, warehouse_ids=None):
        groups = [self.internal_group.id, self.stock_user_group.id]
        if restricted:
            groups.append(self.wh_group.id)
        vals = {
            'name': 'Flous ' + login,
            'login': login,
            'groups_id': [(6, 0, groups)],
        }
        if warehouse_ids:
            vals['visible_warehouse_ids'] = [(6, 0, warehouse_ids)]
        return self.env['res.users'].create(vals)

    def _visible_pickings(self, user):
        return self.env['stock.picking'].with_user(user).search(
            [('id', 'in', (self.picking_a | self.picking_b).ids)])

    def test_group_member_sees_only_assigned_warehouse(self):
        """A group member only sees operations of their own warehouse."""
        found = self._visible_pickings(self.user_a)
        self.assertIn(self.picking_a, found)
        self.assertNotIn(self.picking_b, found)

    def test_two_step_transfer_isolation(self):
        """Each warehouse operator sees only their own step of the transfer."""
        found_a = self._visible_pickings(self.user_a)
        found_b = self._visible_pickings(self.user_b)
        self.assertIn(self.picking_a, found_a)
        self.assertNotIn(self.picking_b, found_a)
        self.assertIn(self.picking_b, found_b)
        self.assertNotIn(self.picking_a, found_b)

    def test_non_member_sees_all(self):
        """Users outside the group are not restricted."""
        outsider = self._new_user('flous_wh_outsider')
        found = self._visible_pickings(outsider)
        self.assertIn(self.picking_a, found)
        self.assertIn(self.picking_b, found)

    def test_admin_sees_all(self):
        """System administrators see everything."""
        admin = self.env.ref('base.user_admin')
        found = self._visible_pickings(admin)
        self.assertIn(self.picking_a, found)
        self.assertIn(self.picking_b, found)

    def test_empty_list_sees_nothing(self):
        """A group member with no assigned warehouse sees no operations."""
        locked = self._new_user('flous_wh_locked', restricted=True)
        found = self._visible_pickings(locked)
        self.assertFalse(found)

    def test_move_lines_hidden(self):
        """Move lines of another warehouse's picking are not readable."""
        found_lines = self.env['stock.move.line'].with_user(self.user_a).search(
            [('picking_id', '=', self.picking_b.id)])
        self.assertFalse(found_lines)

    def test_sync_from_warehouse_side(self):
        """Adding a user on the warehouse form reflects on the user record."""
        outsider = self._new_user('flous_wh_sync_user')
        self.wh_a.visible_user_ids = [(4, outsider.id)]
        self.assertIn(self.wh_a, outsider.visible_warehouse_ids)
