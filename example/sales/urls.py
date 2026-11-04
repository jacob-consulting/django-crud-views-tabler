from .views import cv_address, cv_customer

urlpatterns = cv_customer.urlpatterns + cv_address.urlpatterns
