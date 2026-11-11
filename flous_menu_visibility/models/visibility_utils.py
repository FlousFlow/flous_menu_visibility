# -*- coding: utf-8 -*-
"""Shared visibility semantics used by all Flous Flow rules."""
from odoo import fields

VISIBILITY_MODE = [('hide', 'Hide from selected users'), ('show', 'Show only to selected users')]

def is_visible_for_user(selected_users, mode, user):
    selected = user in selected_users
    return not selected if mode == 'hide' else selected

def visibility_mode_field(**kwargs):
    defaults = {'selection': VISIBILITY_MODE, 'string': 'Visibility Mode', 'required': True,
                'default': 'hide', 'help': 'Hide from selected users, or show only to selected users.'}
    defaults.update(kwargs)
    return fields.Selection(**defaults)
