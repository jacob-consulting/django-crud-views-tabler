from .views import cv_customer
from .views_bulk import cv_bulk_customer

urlpatterns = [*cv_customer.urlpatterns, *cv_bulk_customer.urlpatterns]
