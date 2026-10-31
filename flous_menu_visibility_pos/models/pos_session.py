# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models


class PosSession(models.Model):
    _inherit = 'pos.session'

    def load_data(self, local_data=None):
        self.ensure_one()
        self.sudo().config_id._check_visibility_access()
        return super().load_data(local_data or {})
