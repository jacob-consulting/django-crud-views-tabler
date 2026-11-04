from django.apps import AppConfig


class SalesConfig(AppConfig):
    name = "sales"

    def ready(self):
        from crud_views.lib.assets import register_assets

        register_assets("sales", js=["sales/sales.js"])
