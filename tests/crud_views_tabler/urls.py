from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.http import HttpResponse
from django.urls import include, path

dashboard_urls = ([path("", lambda request: HttpResponse("dashboard"), name="index")], "dashboard")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("tests.crud_views_tabler.testapp.urls")),
    path("dashboard/", include(dashboard_urls)),
]
