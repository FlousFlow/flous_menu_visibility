# Flous Flow POS Visibility

Optional integration for `flous_menu_visibility`. Odoo installs this addon
automatically when both the core visibility addon and `point_of_sale` are
installed. It does not install Point of Sale when the core visibility addon is
used on its own.

## Configure

1. Open **Settings → Visibility Control → Point of Sale Visibility** after Odoo
   installs both the core addon and Point of Sale.
2. Choose an existing POS configuration from the list and select the internal
   users who must not see or start it. This screen does not create POS
   configurations. The same field is available on the POS configuration's
   **Visibility** tab.

The **Point of Sale Visibility** list shows all configured points of sale,
including ones that are not restricted yet. It uses compact cards on phones and
a sortable table on wider screens.

Restricted configurations are removed from the POS dashboard. The regular
backend launch action and direct `/pos/ui/<id>` URLs are also blocked for the
selected users. System administrators always retain access.

Close the POS session before adding restricted users. The addon refuses to
apply restrictions while a session is active so that it does not disrupt an
open register or unsynchronized sales. It never closes sessions or deletes
orders. Existing POS orders remain governed by Odoo's normal access rights.
