# Odoo 20 Engineering Log

## 2026-11-09 — Per-user view button visibility

- Added contextual selection for `object` and `action` buttons inside form and
  list views, plus persistent per-model visibility rules and an administrator
  management screen.
- Rules match the technical button type and name, plus the XML `id` when
  present. Labels are stored for administrators but are not part of matching,
  so translations do not change behavior. Duplicate technical selectors in
  the same model share a rule when the view does not provide an `id`.
- The view hook sets `invisible="1"` per request, after the shared view cache
  is read. This is UI visibility, not server-side authorization; protected
  actions still need method-level access checks.
- Validation: Odoo 20 test DB `flous_menu_visibility_test_20261031`, full
  module test suite: 35 passed, 0 failed, 0 errors (one existing skip due to
  the test DB lacking a suitable required field). Browser interaction opened
  the picker on a real product stat button and displayed its clean label;
  cancelled without saving a rule. Python compilation and `git diff --check`
  passed.

## 2026-11-09 — Embedded list create controls

- Fixed selection of x2many list controls such as **Add a line**: the picker
  identifies the control by its parent field and Odoo shortcut, then marks only
  that control invisible for selected users.
- This keeps the one-to-many field and existing lines visible and editable.
- Validation: added a regression test exercising the wizard and checking the
  account invoice-line control in the generated view. Interactive verification
  is in progress.
