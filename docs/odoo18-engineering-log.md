# Odoo 18 Engineering Log

## 2026-11-11 — Port Odoo 20 visibility features to 18.0

- Ported button visibility rules, central visibility picker, embedded list create-control hiding, and optional POS restrictions from `20.0` to `18.0`.
- Adapted Odoo-version APIs: `_sql_constraints`, `ir.rule`, `groups_id`, Odoo 18 POS controller/session signatures, and Odoo 18 POS form layout.
- Verified installation, upgrade, and module tests on disposable database `flous_menu_visibility_o18_port_20261111` using local Odoo 18. POS integration installed and its focused tests completed without test failures.
