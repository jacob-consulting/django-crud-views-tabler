from django.contrib import admin

from .models import Category, Channel, Product, Tag

admin.site.register([Category, Channel, Product, Tag])
