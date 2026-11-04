from .views import cv_address, cv_all_orders, cv_customer, cv_order

urlpatterns = cv_customer.urlpatterns + cv_address.urlpatterns + cv_order.urlpatterns + cv_all_orders.urlpatterns
