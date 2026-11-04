from django.contrib import admin

from .models import ShowcaseCategory, ShowcaseChannel, ShowcaseItem, ShowcaseTag

admin.site.register([ShowcaseCategory, ShowcaseChannel, ShowcaseItem, ShowcaseTag])
