# Menu, Field, Button, Warehouse & Journal Visibility Control

**Flous Flow** — Odoo module to hide specific menu items, fields and view
buttons, restrict warehouse operations per user, and hide accounting journals.

## Features

- **Central Visibility Control** — configure menus, fields, buttons, journals and
  warehouses from **Settings → Visibility Control**. Rules are not exposed
  as tabs on individual user forms.
- **Pick from the interface** — system administrators can enable **Visibility**
  in the systray, point at a menu item, form field, or list column, and choose
  the internal users who should not see it.
- **Hide view buttons per user** — select an Odoo form or list action button,
  then choose which internal users should not see it. Manage saved rules from
  **Settings → Visibility Control → Button Visibility Rules**.
- **Hide menus per user** — select restricted users from the central menu list.
- **Hide fields per user** — e.g. hide `list_price` (sale price) or
  `standard_price` (cost price) on the product form from specific users.
- **Restrict warehouse operations per user** — users in the "Warehouse
  Visibility" group only see operations of their assigned warehouses.
- **Hide accounting journals per user** — a restricted user cannot read the
  journal, its entries or their lines (server-side access restrictions, not just UI).
- **Responsive admin screens** — the visibility lists use readable cards on
  phones and retain sortable tables on wider screens. User assignments wrap
  cleanly, and the field picker dialog keeps its actions visible on small screens.
- Hiding a field sets `invisible="1"` on the view node — the value stays
  loaded, so view expressions/domains keep working and **the view is never
  broken**.
- System administrators (`base.group_system`) always see everything.
- Menu and field visibility affect the interface. They do not secure the
  underlying field value from exports, reports, RPC or other server-side
  access; use Odoo access rights for confidential data.

### Select an item directly

1. Sign in as a system administrator and open the menu or model view.
2. Click **Visibility** in the top bar. The button stays active while the
   pointer highlights selectable items. An on-screen notice explains the
   current selection controls.
3. Point at a menu entry, a field on a form, or a column heading in a list and
   click it. This pauses the interface and opens the user selector.
   For nested menus, click a parent once to open it, then select a child. To
   select the parent itself, double-click it or use Alt-click.
4. Search for internal users in the selector, or use **Select All Internal
   Users** / **Clear Selection**. The selected-user count updates with the
   selection. Click **Apply** to save. Applying an empty selection clears the
   restriction for that menu or field.

The picker creates or updates the same rules managed from **Settings →
Visibility Control**. It supports menu entries, form fields, list columns, and
view action buttons. Button rules match the technical method/action name and
type; when a view button has an XML `id`, it is included to distinguish it.
Buttons that reuse the same technical name and type without an ID across views
of the same model share a rule.

Administrators can edit or delete field rules from **Settings → Visibility
Control → Field Visibility Rules**. The list shows each model/field target,
selected users and the user count.

Button hiding changes interface visibility only. It does not block the button's
server-side method or action from being called through RPC; use access rights
and server-side checks when an action must be restricted for security.

The optional companion addon `flous_menu_visibility_pos` is installed
automatically when both this module and Odoo Point of Sale are installed. It adds
**Hidden Points of Sale** under **Settings → Visibility Control** without making
Point of Sale a dependency of this core addon. Databases that already had both
modules installed before this automatic integration was added may need a
one-time installation of **Flous Flow POS Visibility** from Apps. Close active
sessions before restricting a POS configuration.

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

Odoo 20 renders every view through `ir.ui.view.get_view()` →
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

1. Open **Settings → Visibility Control → Warehouse Visibility**.
2. Add the operator to the **Warehouse Visibility** group.
3. On each warehouse row, select the users allowed to see its operations.

From then on, that user only sees operations (receipts, deliveries, internal
transfers) of those warehouses — not in the Operations dashboard, not in the
lists, not through reports or the API. Users outside the group (and admins)
always see everything.

### Technical notes

| Model               | Field / rule                                          | Description                     |
|---------------------|-------------------------------------------------------|---------------------------------|
| `res.users`         | `visible_warehouse_ids` (M2M → `stock.warehouse`)      | Warehouses the user may see     |
| `stock.warehouse`   | `visible_user_ids` (M2M → `res.users`)                 | Inverse side (same table)       |
| `stock.picking`     | `ir.access` `picking_warehouse_visibility_rule`        | Hides operations of other warehouses |
| `stock.move`        | `ir.access` `move_warehouse_visibility_rule`           | Hides moves of other warehouses |
| `stock.move.line`   | `ir.access` `move_line_warehouse_visibility_rule`      | Hides move lines of other warehouses |

The three rules are **group rules** on the `Warehouse Visibility` group and
filter by the user's `visible_warehouse_ids`. Stock ships no permissive
per-user group rules on these models (only company-based global rules), so
the restriction is not neutralized. The rules apply to **read** only.

## Part 4 — Hide accounting journals

### How to use

1. Open **Settings → Visibility Control → Hidden Journals**.
2. On each journal row, select the users for whom it must be hidden.

The journal form's **Restricted Users** field remains synchronized with this
central list.

### Technical notes

| Model              | Field / rule                              | Description                        |
|--------------------|-------------------------------------------|-----------------------------------|
| `res.users`        | `hidden_journal_ids` (M2M → `account.journal`) | Journals hidden for the user |
| `account.journal`  | `restricted_user_ids` (M2M → `res.users`) | Inverse side (same table)         |
| `account.journal`  | `ir.access` `journal_visibility_rule`      | Hides journals where the user is restricted |
| `account.move`     | `ir.access` `move_visibility_rule`         | Hides entries of hidden journals  |
| `account.move.line`| `ir.access` `move_line_visibility_rule`   | Hides items of hidden journals    |

The three rules are **global rules** (AND-ed with every group rule), so
permissive "see-all" group rules from `account` cannot neutralize them.
A journal is hidden only when the current user is listed in its
`restricted_user_ids`; an empty list means visible to everyone. Admins are
never restricted. The rules apply to **read** only.

## Installation

```bash
# from the Odoo source directory (installs the `stock` and `account` deps too)
./odoo-bin -c odoo.conf -d odoo20 -i flous_menu_visibility --stop-after-init
```

To upgrade an already-installed copy:

```bash
./odoo-bin -c odoo.conf -d odoo20 -u flous_menu_visibility --stop-after-init
```

## Manual test checklist

### Menus
- [ ] Module installs/upgrades without errors.
- [ ] **Settings → Visibility Control → Hidden Menus** is visible to administrators.
- [ ] Adding a restricted user on a menu updates the inverse field (and vice versa).
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
- [ ] **Settings → Visibility Control → Hidden Journals** is visible to administrators.
- [ ] Journal form shows the "Restricted Users" tab (admins only).
- [ ] Hiding a journal from a user also shows the user on the journal form (and vice versa).
- [ ] The restricted user no longer sees the journal in Accounting, and cannot open its entries or items.
- [ ] Other users still see the journal; the admin still sees everything.
- [ ] Removing the restriction restores access immediately.

## Automated tests

```bash
./odoo-bin -c odoo.conf -d odoo20 -u flous_menu_visibility --test-enable --stop-after-init
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
