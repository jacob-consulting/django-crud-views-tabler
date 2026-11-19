from django.contrib import admin
from ordered_model.admin import OrderedModelAdmin
from polymorphic.admin import PolymorphicChildModelAdmin, PolymorphicParentModelAdmin

from .models import Beans, Category, Equipment, FlavorNote, Origin, Product, Subscription


@admin.register(Beans, Equipment, Subscription)
class ProductChildAdmin(PolymorphicChildModelAdmin):
    base_model = Product


@admin.register(Product)
class ProductAdmin(PolymorphicParentModelAdmin):
    base_model = Product
    child_models = (Beans, Equipment, Subscription)
    list_display = ("name", "sku", "price", "stock", "is_active")


@admin.register(Category)
class CategoryAdmin(OrderedModelAdmin):
    list_display = ("name", "move_up_down_links")


admin.site.register([Origin, FlavorNote])
