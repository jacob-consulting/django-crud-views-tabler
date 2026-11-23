"""Tabler classes for django-crud-views' button class table, registered from CrudViewsTablerConfig.ready()."""

TABLER_BUTTON_CLASSES: dict[str, str] = {
    "workflow:badge-primary": "badge bg-primary-lt",
    "workflow:badge-secondary": "badge bg-secondary-lt",
    "workflow:badge-success": "badge bg-success-lt",
    "workflow:badge-danger": "badge bg-danger-lt",
    "workflow:badge-warning": "badge bg-warning-lt",
    "workflow:badge-info": "badge bg-info-lt",
    "workflow:badge-light": "badge bg-light-lt",
    "workflow:badge-dark": "badge bg-dark-lt",
    # Workflow transition buttons (button presentation) by the transition's custom["variant"] (upstream #362). The
    # values match upstream's Bootstrap defaults; declared here so the Tabler look is explicit and project-visible.
    "workflow:transition-primary": "btn btn-primary",
    "workflow:transition-secondary": "btn btn-secondary",
    "workflow:transition-success": "btn btn-success",
    "workflow:transition-danger": "btn btn-danger",
    "workflow:transition-warning": "btn btn-warning",
    "workflow:transition-info": "btn btn-info",
    "workflow:transition-light": "btn btn-light",
    "workflow:transition-dark": "btn btn-dark",
    # The workflow history like the theme's list tables, minus card-table: the history sits on the page, not in a card.
    "workflow:history-table": "table table-vcenter",
    "context:primary": "btn btn-primary",
    "context:secondary": "btn",
    "context:tertiary": "btn",
    "context:danger": "btn btn-outline-danger",
    "list:primary": "btn btn-sm btn-ghost-primary",
    "list:secondary": "btn btn-sm btn-ghost-secondary",
    "list:tertiary": "btn btn-sm btn-ghost-secondary",
    "list:danger": "btn btn-sm btn-ghost-danger",
    # Bulk selection: upstream's card cell is a block wrapper, which shrinks to its card inside Tabler's .row-deck
    # column (a flex row; finding 41). Fill the column; the card (Tabler gives .row-deck .card flex: 1 1 auto) then
    # fills the cell.
    "bulk:card-cell": "position-relative d-flex flex-fill",
    "card:primary": "btn btn-sm btn-primary",
    "card:secondary": "btn btn-sm",
    "card:tertiary": "btn btn-sm btn-ghost-secondary",
    "card:danger": "btn btn-sm btn-ghost-danger",
    # Icon-only buttons (label mode "icon", the toolbar and row default) are square: btn-icon. Labelled ones are not.
    "context:primary:icon": "btn btn-primary btn-icon",
    "context:secondary:icon": "btn btn-icon",
    "context:tertiary:icon": "btn btn-icon",
    "context:danger:icon": "btn btn-icon btn-outline-danger",
    "list:primary:icon": "btn btn-sm btn-icon btn-ghost-primary",
    "list:secondary:icon": "btn btn-sm btn-icon btn-ghost-secondary",
    "list:tertiary:icon": "btn btn-sm btn-icon btn-ghost-secondary",
    "list:danger:icon": "btn btn-sm btn-icon btn-ghost-danger",
    "card:primary:icon": "btn btn-sm btn-icon btn-primary",
    "card:secondary:icon": "btn btn-sm btn-icon",
    "card:tertiary:icon": "btn btn-sm btn-icon btn-ghost-secondary",
    "card:danger:icon": "btn btn-sm btn-icon btn-ghost-danger",
    # Bulk toolbar buttons by the destination's cv_action_variant (upstream #400): a page-level button row like the
    # context toolbar, so the same values. Labelled by default (bulk label mode "both"); :icon is the icon-only mode.
    "bulk:primary": "btn btn-primary",
    "bulk:secondary": "btn",
    "bulk:tertiary": "btn",
    "bulk:danger": "btn btn-outline-danger",
    "bulk:primary:icon": "btn btn-primary btn-icon",
    "bulk:secondary:icon": "btn btn-icon",
    "bulk:tertiary:icon": "btn btn-icon",
    "bulk:danger:icon": "btn btn-icon btn-outline-danger",
    "context:container": "btn-list",
    "list:container": "btn-list flex-nowrap justify-content-end gap-1",
    "card:container": "btn-list",
    "context:menu-toggle": "btn btn-icon",
    "list:menu-toggle": "btn btn-sm btn-icon btn-ghost-secondary",
    "card:menu-toggle": "btn btn-sm btn-icon",
    # The card itself (#243): no mb-3, the .row-deck.row-cards grid spaces the cards.
    "card:root": "card",
    "context:menu-wrapper": "dropdown",
    "list:menu-wrapper": "dropdown",
    "form:delete": "btn btn-danger",
    "form:actions": "d-flex flex-wrap gap-2",
    "form:filter-actions": "d-flex flex-wrap gap-1",
    "alert:dismissible": "alert-dismissible fade show",
    "alert:close": "btn-close",
    "card-order:toggle": "btn btn-icon",
    "card-order:container": "btn-group",
    # ViewSet Navigation (upstream #384, finding 36): Tabler's underline tabs (nav-bordered, as in the dashboard's
    # tasks.html) instead of the stock pills. Tabler's .nav-link is a flex row that collapses the space between icon
    # and label, hence gap-2. nav-bordered spaces the tabs with margin-inline-start on every item after the first,
    # which indents a wrapped row on a narrow screen: a column gap on the list and ms-0 on the items instead, and a
    # small row gap so a wrapped row does not touch the active underline above it. The
    # active key keeps upstream's default; wrapper and identity are not rendered by the theme's page (it composes the
    # owner header itself, finding 38).
    "navbar:nav": "nav nav-bordered flex-wrap column-gap-4 row-gap-1",
    "navbar:item": "nav-item mw-100 ms-0",
    "navbar:link": "nav-link mw-100 text-break gap-2",
    "formset:control": "btn btn-icon",
    "formset:control-danger": "btn btn-icon btn-danger",
    "conditional:legend": "cv-tabler-section-legend",
    "formset:legend": "cv-tabler-section-legend",
    # The structured manage page (#366, #370, #372; finding 35): Tabler's light badges, as for the workflow state.
    # Named colours, not primary: the page's legend says "Blue: required permission · Magenta: required group ·
    # Green: Guardian policy", and a project's primary may be any colour (Acme's is sienna). The group badge drops
    # upstream's fixed-colour cv-manage-badge-group for Tabler's pink, which follows dark mode.
    "manage:badge-model": "badge bg-secondary-lt",
    "manage:badge-resource": "badge bg-azure-lt",
    "manage:badge-objects": "badge badge-outline text-secondary",
    "manage:badge-permission": "badge bg-blue-lt",
    "manage:badge-group": "badge bg-pink-lt",
    "manage:badge-policy-global": "badge bg-green-lt",
    "manage:badge-policy-strict": "badge bg-green-lt",
    "manage:badge-policy-na": "badge bg-secondary-lt",
    "manage:help": "btn btn-sm",
    "manage:trace-allowed": "badge bg-green-lt",
    "manage:trace-passed": "badge bg-green-lt",
    "manage:trace-denied": "badge bg-red-lt",
    "manage:trace-not-found": "badge bg-yellow-lt",
    "manage:trace-login-redirect": "badge bg-yellow-lt",
    "manage:trace-error": "badge bg-yellow-lt",
    "manage:trace-no-such-route": "badge bg-yellow-lt",
    "manage:trace-not-evaluated": "badge bg-yellow-lt",
    "manage:trace-skipped": "badge bg-secondary-lt",
    "manage:trace-not-reached": "badge bg-secondary-lt",
}
