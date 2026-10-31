# Flous Flow POS Visibility

Optional integration for `flous_menu_visibility`. Install this addon only on
databases that use Odoo Point of Sale. It depends on both the core visibility
addon and `point_of_sale`.

## Configure

1. Install **Flous Flow POS Visibility** from Apps.
2. Open **Settings → Visibility Control → Hidden Points of Sale**.
3. Open a POS configuration and select the internal users who must not see or
   start it. The same field is available on the POS configuration's **Visibility**
   tab.

The **Hidden Points of Sale** list uses compact cards on phones and a sortable
table on wider screens.

Restricted configurations are removed from the POS dashboard. The regular
backend launch action and direct `/pos/ui/<id>` URLs are also blocked for the
selected users. System administrators always retain access.

Close the POS session before adding restricted users. The addon refuses to
apply restrictions while a session is active so that it does not disrupt an
open register or unsynchronized sales. It never closes sessions or deletes
orders. Existing POS orders remain governed by Odoo's normal access rights.
