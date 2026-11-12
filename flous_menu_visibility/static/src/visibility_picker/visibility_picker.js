/** @odoo-module **/

import { Component, onWillDestroy, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { user } from "@web/core/user";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class VisibilityPickerSystray extends Component {
    static template = "flous_menu_visibility.VisibilityPickerSystray";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.active = useState({ value: false });
        this.highlighted = null;
        this.onPointerOver = this.onPointerOver.bind(this);
        this.onPointerOut = this.onPointerOut.bind(this);
        this.onDocumentClick = this.onDocumentClick.bind(this);
        onWillDestroy(() => this.setPickerMode(false));
    }

    get isSystem() {
        return user.isSystem;
    }

    get pickerTitle() {
        return this.active.value ? _t("Cancel item selection") : _t("Select an item to hide");
    }

    togglePickerMode() {
        this.setPickerMode(!this.active.value);
    }

    setPickerMode(active) {
        if (this.active.value === active) {
            return;
        }
        this.active.value = active;
        if (active) {
            document.addEventListener("pointerover", this.onPointerOver, true);
            document.addEventListener("pointerout", this.onPointerOut, true);
            document.addEventListener("click", this.onDocumentClick, true);
            document.body.classList.add("o_flous_visibility_picker_active");
            this.pickerNotificationClose = this.notification.add(
                _t("Click a field, list column, view button, or accounting journal row to select it. Click a parent menu once to open it; double-click or Alt-click to select the parent menu."),
                { type: "info", sticky: true, title: _t("Visibility selection is active") },
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
        const createButton = eventTarget.closest?.(
            ".o_field_x2many_list_row_add button"
        );
        if (createButton && !createButton.closest(".o_flous_visibility_picker")) {
            const parentField = createButton.closest(".o_field_widget[name]");
            const modelName = this.action.currentController?.props?.resModel;
            const fieldName = parentField?.getAttribute("name");
            const buttonHotkey = createButton.getAttribute("data-hotkey") || false;
            const buttonLabel = createButton.textContent.trim();
            if (modelName && fieldName && buttonLabel) {
                return {
                    node: createButton,
                    type: "button",
                    modelName,
                    buttonName: `create:${fieldName}:${buttonHotkey || buttonLabel}`,
                    buttonType: "create",
                    buttonId: false,
                    buttonFieldName: fieldName,
                    buttonHotkey,
                    buttonLabel,
                };
            }
        }
        const buttonNode = eventTarget.closest?.("button[name][type]");
        if (
            buttonNode &&
            ["object", "action"].includes(buttonNode.getAttribute("type")) &&
            buttonNode.closest(".o_form_view, .o_list_view") &&
            !buttonNode.closest(".o_flous_visibility_picker")
        ) {
            const modelName = this.action.currentController?.props?.resModel;
            if (modelName) {
                return {
                    node: buttonNode,
                    type: "button",
                    modelName,
                    buttonName: buttonNode.getAttribute("name"),
                    buttonType: buttonNode.getAttribute("type"),
                    buttonId: buttonNode.getAttribute("id") || false,
                    buttonLabel:
                        buttonNode.querySelector(".o_stat_text")?.textContent.trim() ||
                        buttonNode.getAttribute("string") ||
                        buttonNode.textContent.trim(),
                };
            }
        }
        const controller = this.action.currentController;
        const modelName =
            controller?.props?.resModel ||
            controller?.model?.root?.resModel ||
            controller?.model?.root?.config?.resModel;
        if (modelName === "account.journal") {
            const journalRow = eventTarget.closest?.("tr.o_data_row[data-id]");
            const journalId = Number(journalRow?.getAttribute("data-id"));
            if (journalRow && Number.isInteger(journalId) && journalId > 0) {
                const nameCell = journalRow.querySelector(
                    'td[name="name"], td[data-name="name"]'
                );
                return {
                    node: journalRow,
                    type: "journal",
                    journalId,
                    journalLabel: nameCell?.textContent.trim() || journalRow.textContent.trim(),
                };
            }
        }
        if (modelName === "pos.config" || window.location.pathname.includes("/point-of-sale")) {
            const posRow = eventTarget.closest?.(
                "tr.o_data_row[data-id], .o_kanban_record[data-id]"
            );
            const rawPosId = posRow?.getAttribute("data-id");
            const records = controller?.model?.root?.records;
            const cardRecords = Array.isArray(records) ? records : [];
            const cardIndex = posRow
                ? [...document.querySelectorAll(".o_kanban_record[data-id]")].indexOf(posRow)
                : -1;
            const posRecord = rawPosId && cardRecords.length
                ? cardRecords.find((record) => record.id === rawPosId) || cardRecords[cardIndex]
                : null;
            const posId = Number(posRecord?.resId || rawPosId);
            if (posRow) {
                return {
                    node: posRow,
                    type: "pos_config",
                    posConfigId: Number.isInteger(posId) && posId > 0 ? posId : false,
                    posConfigLabel:
                        posRow.querySelector(".o_kanban_record_title")?.textContent.trim() ||
                        posRow.textContent.trim(),
                };
            }
        }
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
            const modelName =
                controller?.props?.resModel ||
                controller?.model?.root?.resModel ||
                controller?.model?.root?.config?.resModel;
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
        if (!this.active.value) return;
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
        if (!this.active.value || event.target.closest?.(".o_flous_visibility_picker")) return;
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
            if (target.type === "pos_config" && !target.posConfigId && target.posConfigLabel) {
                const configs = await this.orm.searchRead(
                    "pos.config",
                    [["name", "=", target.posConfigLabel]],
                    ["id"],
                    { limit: 1 },
                );
                target.posConfigId = configs[0]?.id || false;
            }
            const action = target.type === "menu"
                ? await this.orm.call(
                    "flous.visibility.picker", "action_open_for_menu", [target.xmlid]
                )
                : target.type === "journal"
                ? await this.orm.call(
                    "flous.visibility.picker",
                    "action_open_for_journal",
                    [target.journalId],
                )
                : target.type === "pos_config"
                ? await this.orm.call(
                    "flous.visibility.picker", "action_open_for_pos_config", [target.posConfigId]
                )
                : target.type === "button"
                ? await this.orm.call(
                    "flous.visibility.picker",
                    "action_open_for_button",
                    [
                        target.modelName,
                        target.buttonName,
                        target.buttonType,
                        target.buttonId,
                        target.buttonLabel,
                        target.buttonFieldName,
                        target.buttonHotkey,
                    ],
                )
                : await this.orm.call(
                    "flous.visibility.picker",
                    "action_open_for_field",
                    [target.modelName, target.fieldName],
                );
            await this.action.doAction(action);
        } catch (error) {
            this.notification.add(error.message || _t("Could not open visibility settings."), {
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
