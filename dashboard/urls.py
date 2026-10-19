from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.index, name="index"),
    path("users/", views.user_list, name="users"),
    path("users/new/", views.user_create, name="user_create"),
]
