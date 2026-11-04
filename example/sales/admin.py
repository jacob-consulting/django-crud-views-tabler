from django.contrib import admin

from .models import Address, Customer


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["name", "kind", "city", "country", "owner"]
    list_filter = ["kind", "country"]
    search_fields = ["name", "contact_name", "email"]
    inlines = [AddressInline]
