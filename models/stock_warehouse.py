# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class StockWarehouse(models.Model):
    """Inverse side of ``res.users.visible_warehouse_ids``.

    Both fields share the relation table ``flous_warehouse_visibility_rel``.
    """

    _inherit = 'stock.warehouse'

    visible_user_ids = fields.Many2many(
        'res.users',
        relation='flous_warehouse_visibility_rel',
        column1='warehouse_id',
        column2='user_id',
        string='Visible Users',
        groups='base.group_system',
        help='Users (in the "Warehouse Visibility" group) who can see the '
             'operations of this warehouse.',
    )

    def write(self, vals):
        res = super().write(vals)
        if 'visible_user_ids' in vals:
            # ir.rule domains are cached per user (uid). Invalidate the
            # registry cache so the new restrictions apply immediately.
            self.env.registry.clear_cache()
        return res
