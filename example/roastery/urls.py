from .views import cv_batch, cv_lot, cv_session

urlpatterns = cv_lot.urlpatterns + cv_session.urlpatterns + cv_batch.urlpatterns
