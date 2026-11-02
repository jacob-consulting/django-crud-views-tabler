"""The Tabler icons in django-crud-views' icon registry.

They plug in as the ``tabler`` library (``tabler:eye``, see ``render``). ``TABLER_ICONS`` maps the package's semantic
icon names to Tabler icons; a project overrides single keys with ``CRUD_VIEWS_ICONS``. The icons themselves live in
``django_tabler.icons``.
"""

from django.utils.safestring import SafeString

from django_tabler.icons import svg

TABLER_ICONS: dict[str, str] = {
    "list": "tabler:list",
    "card": "tabler:layout-grid",
    "detail": "tabler:eye",
    "create": "tabler:square-plus",
    "update": "tabler:pencil",
    "delete": "tabler:trash",
    "save": "tabler:check",
    "cancel": "tabler:arrow-left",
    "filter-reset": "tabler:filter-x",
    "order-up": "tabler:arrow-up",
    "order-down": "tabler:arrow-down",
    "manage": "tabler:settings",
    "workflow": "tabler:hierarchy",
    "actions-menu": "tabler:dots",
    "filter": "tabler:filter",
    "filter-close": "tabler:filter-x",
    "language": "tabler:language",
    "sort-asc": "tabler:sort-ascending",
    "sort-desc": "tabler:sort-descending",
    "table-sort-asc": "tabler:chevrons-up",
    "table-sort-desc": "tabler:chevrons-down",
    "formset-up": "tabler:caret-up",
    "formset-down": "tabler:caret-down",
    "formset-add": "tabler:plus",
    "formset-delete": "tabler:square-x",
    "field-marker": "tabler:chevrons-right",
    "boolean-true": "tabler:circle-check",
    "boolean-false": "tabler:circle-x",
    "property-detail": "tabler:info-circle",
    "text-icon": "tabler:file-text",
    "message-success": "tabler:check",
    "message-info": "tabler:info-circle",
    "message-warning": "tabler:alert-triangle",
    "message-error": "tabler:alert-circle",
    "message-debug": "tabler:bug",
    "page-previous": "tabler:chevron-left",
    "page-next": "tabler:chevron-right",
}


def render(name: str, *, css: str, config: dict) -> SafeString:
    """Renderer of the ``tabler`` icon library in django-crud-views' icon registry."""
    return svg(name, css)
