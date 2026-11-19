"""Typeahead lookups of the sales app.

``crud_views_widget_typeahead`` imports every app's ``typeahead.py`` on startup.
"""

from crud_views_widget_typeahead.lookups import TypeaheadLookup, register_lookup

from .permissions import customers_for


@register_lookup("sales.customers")
class CustomerLookup(TypeaheadLookup):
    """Customers by name, company or city; only those the user may view (Sam: the granted ones)."""

    search_fields = ["name", "company", "city"]
    ordering = ["name"]
    min_chars = 0  # the select popup lists the first customers on open

    def get_queryset(self, request, **params):
        return customers_for(request.user)

    def label(self, obj) -> str:
        return f"{obj.name} ({obj.city})" if obj.city else obj.name
