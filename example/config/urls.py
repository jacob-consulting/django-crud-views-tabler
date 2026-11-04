from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from . import views

urlpatterns = [
    path("accounts/login/", auth_views.LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("admin/", admin.site.urls),
    path("theming/", views.theming, name="theming"),
    path("_code/pygments.css", views.pygments_stylesheet, name="pygments-css"),
    path("_code/<slug:app_label>/", views.code_panel, name="code-panel"),
    path("_typeahead/", include("crud_views_widget_typeahead.urls")),
    path("", include("catalog.urls")),
    path("", include("sales.urls")),
    path("", include("roastery.urls")),
    path("", include("shipping.urls")),
    path("", include("showcase.urls")),
    path("", include("dashboard.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
