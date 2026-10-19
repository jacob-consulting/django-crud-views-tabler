from django.apps import AppConfig


class CrudViewsTablerConfig(AppConfig):
    """Tabler theme for django-crud-views.

    Overrides the package's templates under the ``crud_views/`` namespace, so it must be listed
    before ``crud_views`` in INSTALLED_APPS.
    """

    name = "crud_views_tabler"
    verbose_name = "django-crud-views Tabler theme"

    def ready(self):
        from crud_views.lib.assets import register_assets

        register_assets("crud_views_tabler", css=["crud_views_tabler/crud_views_tabler.css"])
