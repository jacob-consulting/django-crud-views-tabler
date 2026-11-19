from .views import cv_address, cv_all_orders, cv_all_subscriptions, cv_customer, cv_order, cv_subscription

urlpatterns = (
    cv_customer.urlpatterns
    + cv_address.urlpatterns
    + cv_order.urlpatterns
    + cv_all_orders.urlpatterns
    + cv_subscription.urlpatterns
    + cv_all_subscriptions.urlpatterns
)
