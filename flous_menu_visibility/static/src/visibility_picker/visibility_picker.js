/** @odoo-module **/

import { Component, onWillDestroy, signal } from "@odoo/owl";
import { onMounted } from "@odoo/owl";
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
        this.active = signal(false);
        this.highlighted = null;
        this.onPointerOver = this.onPointerOver.bind(this);
        this.onPointerOut = this.onPointerOut.bind(this);
        this.onDocumentClick = this.onDocumentClick.bind(this);
        this.scheduleKanbanVisibilityScan = this.scheduleKanbanVisibilityScan.bind(this);
        onMounted(() => {
            this.kanbanObserver = new MutationObserver(this.scheduleKanbanVisibilityScan);
            this.kanbanObserver.observe(document.body, { childList: true, subtree: true });
            this.scheduleKanbanVisibilityScan();
        });
        onWillDestroy(() => {
            this.setPickerMode(false);
            this.kanbanObserver?.disconnect();
            clearTimeout(this.kanbanScanTimer);
        });
    }

    get isSystem() {
        return user.isSystem;
    }

    get pickerTitle() {
        return this.active() ? _t("Cancel item selection") : _t("Select an item to hide");
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

    getControllerModelName(controller = this.action.currentController) {
        return (
            controller?.props?.resModel ||
            controller?.model?.root?.resModel ||
            controller?.model?.root?.config?.resModel
        );
    }

    getKanbanRecordInfo(card, controller = this.action.currentController) {
        const rawId = card?.getAttribute("data-id");
        const records = Array.isArray(controller?.model?.root?.records)
            ? controller.model.root.records
            : [];
        const cardIndex = card
            ? [...document.querySelectorAll(".o_kanban_record[data-id]")].indexOf(card)
            : -1;
        const record = rawId && records.length
            ? records.find((item) => item.id === rawId) || records[cardIndex]
            : null;
        const recordId = Number(record?.resId || rawId);
        const label =
            card?.querySelector('[name="card_title"] > span')?.textContent.trim() ||
            card?.querySelector(':scope > span.fw-bold')?.textContent.trim() ||
            card?.querySelector('.o_kanban_record_title, [name="name"]')?.textContent.trim() ||
            card?.textContent.trim();
        return {
            recordId: Number.isInteger(recordId) && recordId > 0 ? recordId : false,
            recordLabel: label,
        };
    }

    scheduleKanbanVisibilityScan() {
        if (this.kanbanScanTimer) return;
        this.kanbanScanTimer = setTimeout(async () => {
            this.kanbanScanTimer = null;
            await this.scanKanbanVisibility();
        }, 0);
    }

    async scanKanbanVisibility() {
        const controller = this.action.currentController;
        const modelName = this.getControllerModelName(controller);
        if (!modelName) return;
        const cards = [...document.querySelectorAll(".o_kanban_record[data-id]")];
        const cardInfos = cards.map((card) => this.getKanbanRecordInfo(card, controller));
        const recordIds = [...new Set(cardInfos.map((info) => info.recordId).filter(Boolean))];
        if (!recordIds.length) return;
        try {
            const hiddenIds = new Set(await this.orm.call(
                "flous.visibility.service", "get_hidden_record_ids", [modelName, recordIds],
            ));
            cards.forEach((card, index) => {
                const hidden = hiddenIds.has(cardInfos[index].recordId);
                card.style.display = hidden ? "none" : "";
                card.dataset.flousVisibilityHidden = hidden ? "1" : "0";
            });
        } catch {
            // An unavailable optional service must never break a standard Kanban view.
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
        const modelName = this.getControllerModelName(controller);
        if (modelName === "account.journal") {
            const journalRow = eventTarget.closest?.("tr.o_data_row[data-res-id]");
            const journalId = Number(journalRow?.getAttribute("data-res-id"));
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
        if (modelName === "pos.config") {
            const posRow = eventTarget.closest?.("tr.o_data_row[data-id]");
            const posId = Number(posRow?.getAttribute("data-id"));
            if (posRow && Number.isInteger(posId) && posId > 0) {
                return {
                    node: posRow,
                    type: "pos_config",
                    posConfigId: posId,
                    posConfigLabel: posRow.textContent.trim(),
                };
            }
        }
        const kanbanCard = eventTarget.closest?.(".o_kanban_record[data-id]");
        if (kanbanCard && modelName && modelName !== "pos.config") {
            const { recordId, recordLabel } = this.getKanbanRecordInfo(kanbanCard, controller);
            return {
                node: kanbanCard,
                type: "record",
                modelName,
                recordId,
                recordLabel,
            };
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
            if (target.type === "record" && !target.recordId && target.recordLabel) {
                const records = await this.orm.searchRead(
                    target.modelName,
                    [["display_name", "=", target.recordLabel]],
                    ["id"],
                    { limit: 1 },
                );
                target.recordId = records[0]?.id || false;
            }
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
                : target.type === "record"
                ? await this.orm.call(
                    "flous.visibility.picker",
                    "action_open_for_record",
                    [target.modelName, target.recordId, target.recordLabel],
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
