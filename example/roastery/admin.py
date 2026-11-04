from django.contrib import admin

from .models import CuppingScore, CuppingSession, GreenLot, RoastBatch

admin.site.register([GreenLot, CuppingSession, CuppingScore, RoastBatch])
