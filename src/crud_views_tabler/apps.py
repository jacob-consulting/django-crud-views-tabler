from django.apps import AppConfig


class CrudViewsTablerConfig(AppConfig):
    """Tabler theme for django-crud-views.

    Overrides the package's templates under the ``crud_views/`` namespace, so it must be listed
    before ``crud_views`` in INSTALLED_APPS. Registers the ``tabler`` icon library, a Tabler icon for every
    semantic name and the Tabler button classes, so projects need no icon or button settings.
    """

    name = "crud_views_tabler"
    verbose_name = "django-crud-views Tabler theme"

    def ready(self):
        from crud_views.lib import register_js_namespace, register_tooltip_placements
        from crud_views.lib.assets import register_assets
        from crud_views.lib.button_classes import register_button_classes
        from crud_views.lib.icons import register_icon_library, register_icons

        import crud_views_tabler.checks  # noqa: F401
        from crud_views_tabler.buttons import TABLER_BUTTON_CLASSES
        from crud_views_tabler.icons import TABLER_ICONS

        register_icon_library("tabler", renderer="crud_views_tabler.icons.render")
        register_icons(TABLER_ICONS)
        from crud_views.lib.view.label_mode import register_label_mode_defaults

        register_label_mode_defaults({"form": "both"})
        register_button_classes(
            {
                key: value
                for key, value in TABLER_BUTTON_CLASSES.items()
                if not key.startswith("workflow:") or self.apps.is_installed("crud_views_workflow")
            }
        )
        # Tabler's bundle exposes Bootstrap's components on window.tabler, not window.bootstrap; upstream's stock
        # adapters resolve the registered name on every call (upstream #398). The data prefix stays Bootstrap's bs.
        register_js_namespace("tabler")
        # Toolbar tooltips open below the buttons, so they do not cover the page header; the rest keep Tabler's
        # default. A data-bs-placement on the button wins.
        register_tooltip_placements({"context": "bottom"})
        register_assets("crud_views_tabler", css=["crud_views_tabler/crud_views_tabler.css"])
