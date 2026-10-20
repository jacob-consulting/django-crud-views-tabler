from django.apps import AppConfig


class CrudViewsTablerConfig(AppConfig):
    """Tabler theme for django-crud-views.

    Overrides the package's templates under the ``crud_views/`` namespace, so it must be listed
    before ``crud_views`` in INSTALLED_APPS. Registers the ``tabler`` icon library and a Tabler icon for every
    semantic name, so projects need no icon settings.
    """

    name = "crud_views_tabler"
    verbose_name = "django-crud-views Tabler theme"

    def ready(self):
        from crud_views.lib.assets import register_assets
        from crud_views.lib.icons import register_icon_library, register_icons

        import crud_views_tabler.checks  # noqa: F401
        from crud_views_tabler.icons import TABLER_ICONS

        register_icon_library("tabler", renderer="crud_views_tabler.icons.render")
        register_icons(TABLER_ICONS)
        register_assets(
            "crud_views_tabler",
            js=["crud_views_tabler/tabler-adapters.js"],
            css=["crud_views_tabler/crud_views_tabler.css"],
        )
