from .views import cv_category, cv_product

urlpatterns = cv_product.urlpatterns + cv_category.urlpatterns
