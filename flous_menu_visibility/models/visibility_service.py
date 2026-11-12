# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models


class FlousVisibilityService(models.Model):
    """Small read-only RPC facade used by the Kanban visibility picker."""

    _name = 'flous.visibility.service'
    _description = 'Visibility Service'

    def get_hidden_record_ids(self, model_name, record_ids):
        return self.env['flous.record.hide.rule'].get_hidden_record_ids(
            model_name, record_ids,
        )

