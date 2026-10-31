# -*- coding: utf-8 -*-
# Copyright 2026 Flous Flow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import http
from odoo.addons.point_of_sale.controllers.main import PosController
from odoo.http import request


class PosVisibilityController(PosController):
    @http.route()
    def pos_web(self, config_id=False, from_backend=False, subpath=None, **kwargs):
        if config_id:
            try:
                config_id = int(config_id)
            except (TypeError, ValueError):
                pass
            else:
                config = request.env['pos.config'].sudo().browse(config_id).exists()
                if config and config._is_restricted_for_current_user():
                    return request.not_found()
        return super().pos_web(
            config_id=config_id,
            from_backend=from_backend,
            subpath=subpath,
            **kwargs,
        )
