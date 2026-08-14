# Menu, Field, Warehouse & Journal Visibility Control

**Flous Flow** — Odoo module to hide specific menu items, hide specific
fields, restrict warehouse operations per user, and hide accounting
journals per user.

## Features

- **Hide menus per user** — configure from the user form or the menu form
  (both stay in sync).
- **Hide fields per user** — e.g. hide `list_price` (sale price) or
  `standard_price` (cost price) on the product form from specific users.
- **Restrict warehouse operations per user** — users in the "Warehouse
  Visibility" group only see operations of their assigned warehouses.
- **Hide accounting journals per user** — a restricted user cannot read the
  journal, its entries or their lines (real record rules, not just UI).
- Hiding a field sets `invisible="1"` on the view node — the value stays
  loaded, so view expressions/domains keep working and **the view is never
  broken**.
- System administrators (`base.group_system`) always see everything.

## Part 1 — Hide menus

| Model        | Field                              | Description                              |
|--------------|------------------------------------|------------------------------------------|
| `res.users`  | `hidden_menu_ids` (M2M → `ir.ui.menu`) | Menus hidden for the user            |
| `ir.ui.menu` | `restricted_user_ids` (M2M → `res.users`) | Users restricted from the menu    |
| `ir.ui.menu` | `_filter_visible_menus()` override  | Removes restricted menus for the current user (except system admins) |

The two many2many fields point to the same relation table with swapped
columns — a standard Odoo pattern for a two-way many2many. Writing to either
side automatically updates the other.

## Part 2 — Hide fields

New model **`flous.field.hide.rule`** — one rule per (model, field) with the
list of users for whom the field must be hidden.

| Field      | Description                                             |
|------------|---------------------------------------------------------|
| `name`     | Rule name                                               |
| `model_id` | Model containing the field (e.g. `product.template`)    |
| `field_id` | Field to hide (e.g. `list_price`, `standard_price`)     |
| `user_ids` | Users for whom the field is hidden (admins are excluded)|
| `active`   | Archive the rule to disable it                          |

Odoo 18 renders every view through `ir.ui.view.get_view()` →
`_postprocess_access_rights()`. This module overrides
`_postprocess_access_rights` and, for the current user, sets
`invisible="1"` on every `<field>` node matching an active rule for that
view's model. The change happens **per request**, after the shared view cache
is read — the cache is never polluted.

## Part 3 — Restrict warehouse operations

### The two-step transfer scenario

When a warehouse transfer is configured with **two steps** (e.g. a resupply
route between two warehouses), Odoo creates **one operation per warehouse**:
step 1 is a delivery picking of warehouse A, step 2 is a receipt picking of
warehouse B. This module lets each warehouse operator see **only their own
warehouse's operations**.

### How to use

1. **Settings → Users & Companies → Users**, open the warehouse operator.
2. Add them to the **Warehouse Visibility** group (Settings → Users →
   Groups → Warehouse Visibility).
3. On the **Visible Warehouses** page, select the warehouses whose operations
   they may see.

From then on, that user only sees operations (receipts, deliveries, internal
transfers) of those warehouses — not in the Operations dashboard, not in the
lists, not through reports or the API. Users outside the group (and admins)
always see everything.

### Technical notes

| Model               | Field / rule                                          | Description                     |
|---------------------|-------------------------------------------------------|---------------------------------|
| `res.users`         | `visible_warehouse_ids` (M2M → `stock.warehouse`)      | Warehouses the user may see     |
| `stock.warehouse`   | `visible_user_ids` (M2M → `res.users`)                 | Inverse side (same table)       |
| `stock.picking`     | `ir.rule` `picking_warehouse_visibility_rule`          | Hides operations of other warehouses |
| `stock.move`        | `ir.rule` `move_warehouse_visibility_rule`             | Hides moves of other warehouses |
| `stock.move.line`   | `ir.rule` `move_line_warehouse_visibility_rule`        | Hides move lines of other warehouses |

The three rules are **group rules** on the `Warehouse Visibility` group and
filter by the user's `visible_warehouse_ids`. Stock ships no permissive
per-user group rules on these models (only company-based global rules), so
the restriction is not neutralized. The rules apply to **read** only.

## Part 4 — Hide accounting journals

### How to use

1. **Settings → Users & Companies → Users**, open a user.
2. On the **Hidden Journals** page (admins only), add the journals to hide
   for that user.

Alternatively, open **Accounting → Configuration → Journals**, and on the
**Restricted Users** tab pick the users that must not see the journal. Both
sides stay in sync natively.

### Technical notes

| Model              | Field / rule                              | Description                        |
|--------------------|-------------------------------------------|-----------------------------------|
| `res.users`        | `hidden_journal_ids` (M2M → `account.journal`) | Journals hidden for the user |
| `account.journal`  | `restricted_user_ids` (M2M → `res.users`) | Inverse side (same table)         |
| `account.journal`  | `ir.rule` `journal_visibility_rule`        | Hides journals where the user is restricted |
| `account.move`     | `ir.rule` `move_visibility_rule`           | Hides entries of hidden journals  |
| `account.move.line`| `ir.rule` `move_line_visibility_rule`      | Hides items of hidden journals    |

The three rules are **global rules** (AND-ed with every group rule), so
permissive "see-all" group rules from `account` cannot neutralize them.
A journal is hidden only when the current user is listed in its
`restricted_user_ids`; an empty list means visible to everyone. Admins are
never restricted. The rules apply to **read** only.

## Installation

```bash
# from the Odoo source directory (installs the `stock` and `account` deps too)
./odoo-bin -c odoo.conf -d odoo18 -i flous_menu_visibility --stop-after-init
```

To upgrade an already-installed copy:

```bash
./odoo-bin -c odoo.conf -d odoo18 -u flous_menu_visibility --stop-after-init
```

## Manual test checklist

### Menus
- [ ] Module installs/upgrades without errors.
- [ ] Internal (non-admin) user form shows the "Hidden Menus" page.
- [ ] Adding a menu in the user form also shows the user on the menu form (and vice versa).
- [ ] The restricted user no longer sees the menu after reload; other users and the admin still do.

### Fields
- [ ] **Settings → Field Visibility Rules** is visible and works (admins only).
- [ ] Create a rule hiding `list_price` on `product.template` from a test user.
- [ ] The test user no longer sees the sale price on the product form; others do; archiving restores it.

### Warehouses
- [ ] Create two warehouses and a two-step resupply route between them.
- [ ] Add user A to the **Warehouse Visibility** group and assign warehouse A.
- [ ] User A sees only warehouse A's operations (its step of the transfer).
- [ ] User B (assigned warehouse B) sees only warehouse B's step.
- [ ] Users outside the group and the admin see every operation.
- [ ] A group member with no assigned warehouse sees no operations.
- [ ] Removing the user from the group restores full visibility.

### Journals
- [ ] User form shows the "Hidden Journals" page (admins only).
- [ ] Journal form shows the "Restricted Users" tab (admins only).
- [ ] Hiding a journal from a user also shows the user on the journal form (and vice versa).
- [ ] The restricted user no longer sees the journal in Accounting, and cannot open its entries or items.
- [ ] Other users still see the journal; the admin still sees everything.
- [ ] Removing the restriction restores access immediately.

## Automated tests

```bash
./odoo-bin -c odoo.conf -d odoo18 -u flous_menu_visibility --test-enable --stop-after-init
```

## Known limitations

- Warehouse restriction covers **operations** (picking, moves, move lines);
  inventory quantities (`stock.quant`) are not restricted.
- Group rules can in theory be OR-neutralized by permissive per-user group
  rules added by *other* modules on these models; stock itself adds none.
- Do not hide **required** fields: the field stays required, so the form
  cannot be saved by the restricted user.
- Journal restriction is enforced for **read**; users with journal write
  rights (managers) are trusted and not further limited.
- The `account.move.line` journal rule uses a 3-level domain traversal
  (`move_id.journal_id.restricted_user_ids`); on very large move-line tables
  this adds a join to queries.

## License

LGPL-3 — © 2026 Flous Flow. Original module, written from scratch by Flous
Flow. You may reuse it in your Odoo instances, including commercial
deployments, under the terms of the GNU Lesser General Public License v3.
