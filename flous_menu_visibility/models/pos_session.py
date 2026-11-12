# -*- coding: utf-8 -*-
from odoo import models


class PosSession(models.Model):
    _inherit = 'pos.session'

    def load_data(self, models_to_load, only_data=False):
        self.ensure_one()
        self.sudo().config_id._check_visibility_access()
        return super().load_data(models_to_load, only_data=only_data)
