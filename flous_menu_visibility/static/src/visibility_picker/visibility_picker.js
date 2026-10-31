/** @odoo-module **/

import { Component, onWillDestroy, signal } from "@odoo/owl";
import { user } from "@web/core/user";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class VisibilityPickerSystray extends Component {
    static template = "flous_menu_visibility.VisibilityPickerSystray";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.active = signal(false);
        this.highlighted = null;
        this.onPointerOver = this.onPointerOver.bind(this);
        this.onPointerOut = this.onPointerOut.bind(this);
        this.onDocumentClick = this.onDocumentClick.bind(this);
        onWillDestroy(() => this.setPickerMode(false));
    }

    get isSystem() {
        return user.isSystem;
    }

    togglePickerMode() {
        this.setPickerMode(!this.active());
    }

    setPickerMode(active) {
        if (this.active() === active) {
            return;
        }
        this.active.set(active);
        if (active) {
            document.addEventListener("pointerover", this.onPointerOver, true);
            document.addEventListener("pointerout", this.onPointerOut, true);
            document.addEventListener("click", this.onDocumentClick, true);
            document.body.classList.add("o_flous_visibility_picker_active");
            this.pickerNotificationClose = this.notification.add(
                "Click a field or list column to select it. Click a parent menu once to open it; double-click or Alt-click to select the parent menu.",
                { type: "info", sticky: true, title: "Visibility selection is active" },
            );
        } else {
            document.removeEventListener("pointerover", this.onPointerOver, true);
            document.removeEventListener("pointerout", this.onPointerOut, true);
            document.removeEventListener("click", this.onDocumentClick, true);
            document.body.classList.remove("o_flous_visibility_picker_active");
            this.clearHighlight();
            this.pickerNotificationClose?.();
            this.pickerNotificationClose = null;
        }
    }

    getTarget(eventTarget) {
        const fieldNode = eventTarget.closest?.(".o_field_widget[name]");
        const fieldLabel = eventTarget.closest?.("label[for], .o_field_label[for]");
        const fieldId = fieldLabel?.getAttribute("for");
        const labelledField = fieldId
            ? document.getElementById(fieldId)?.closest(".o_field_widget[name]")
            : null;
        const listHeader = eventTarget.closest?.("th[data-name]");
        const listCell = eventTarget.closest?.("td[name], td[data-name]");
        const listFieldName = listCell?.getAttribute("name") || listCell?.dataset.name;
        const listTable = listCell?.closest("table");
        const listCellHeader = listFieldName && listTable
            ? [...listTable.querySelectorAll("th[data-name]")]
                .find((header) => header.dataset.name === listFieldName)
            : null;
        // Prefer list headers for clicks inside a table so the whole list or
        // its navigation menu cannot steal a field selection.
        const node = listHeader || listCellHeader || fieldNode || labelledField || listCell;
        if (node && !node.closest(".o_flous_visibility_picker")) {
            const controller = this.action.currentController;
            const modelName = controller?.props?.resModel;
            const fieldName = node.getAttribute("name") || node.dataset.name;
            if (modelName && fieldName) {
                return { node, type: "field", modelName, fieldName };
            }
        }

        const menuNode = eventTarget.closest?.("[data-menu-xmlid]");
        if (menuNode && !menuNode.closest(".o_flous_visibility_picker")) {
            return { node: menuNode, type: "menu", xmlid: menuNode.dataset.menuXmlid };
        }
        return null;
    }

    onPointerOver(event) {
        if (!this.active()) return;
        const target = this.getTarget(event.target);
        if (target?.node !== this.highlighted) {
            this.clearHighlight();
            this.highlighted = target?.node || null;
            this.highlighted?.classList.add("o_flous_visibility_picker_target");
        }
    }

    onPointerOut(event) {
        if (this.highlighted && !this.highlighted.contains(event.relatedTarget)) {
            this.clearHighlight();
        }
    }

    clearHighlight() {
        this.highlighted?.classList.remove("o_flous_visibility_picker_target");
        this.highlighted = null;
    }

    async onDocumentClick(event) {
        if (!this.active() || event.target.closest?.(".o_flous_visibility_picker")) return;
        const target = this.getTarget(event.target);
        if (!target) return;

        if (
            target.type === "menu" &&
            target.node.classList.contains("dropdown-toggle") &&
            !event.altKey &&
            event.detail < 2
        ) {
            // Let one click open expandable menus so users can reach a nested
            // menu item. Double-click (or Alt-click) still selects the parent.
            return;
        }

        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();
        this.setPickerMode(false);

        try {
            const action = target.type === "menu"
                ? await this.orm.call(
                    "flous.visibility.picker", "action_open_for_menu", [target.xmlid]
                )
                : await this.orm.call(
                    "flous.visibility.picker",
                    "action_open_for_field",
                    [target.modelName, target.fieldName],
                );
            await this.action.doAction(action);
        } catch (error) {
            this.notification.add(error.message || "Could not open visibility settings.", {
                type: "danger",
            });
        }
    }
}

registry.category("systray").add(
    "flous_menu_visibility.picker",
    { Component: VisibilityPickerSystray },
    { sequence: 90 },
);
