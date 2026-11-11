# -*- coding: utf-8 -*-
"""Shared visibility semantics used by all Flous Flow rules."""

from odoo import fields


VISIBILITY_MODE = [
    ('hide', 'Hide from selected users'),
    ('show', 'Show only to selected users'),
]


def is_visible_for_user(selected_users, mode, user):
    """Return whether *user* can see a rule target.

    The system group is deliberately handled by callers because record rules
    and view rendering have different administrator contexts.
    """
    selected = user in selected_users
    return not selected if mode == 'hide' else selected


def visibility_mode_field(**kwargs):
    """Build the common selection field without duplicating its definition."""
    defaults = {
        'selection': VISIBILITY_MODE,
        'string': 'Visibility Mode',
        'required': True,
        'default': 'hide',
        'help': 'Hide from selected users, or show only to selected users.',
    }
    defaults.update(kwargs)
    return fields.Selection(**defaults)
