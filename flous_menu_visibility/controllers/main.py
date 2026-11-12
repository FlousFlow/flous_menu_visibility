# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.point_of_sale.controllers.main import PosController
from odoo.http import request


class PosVisibilityController(PosController):
    @http.route()
    def pos_web(self, config_id=False, from_backend=False, **kwargs):
        if config_id:
            try:
                config = request.env['pos.config'].sudo().browse(int(config_id)).exists()
            except (TypeError, ValueError):
                config = request.env['pos.config']
            if config and config._is_restricted_for_current_user():
                return request.not_found()
        return super().pos_web(config_id=config_id, from_backend=from_backend, **kwargs)
