"""Login required on every page, on every supported Django version.

Django 5.1 added ``django.contrib.auth.middleware.LoginRequiredMiddleware``; ``MIDDLEWARE_PATH`` names it there. On
older Django (4.2) it names the stand-in below, which behaves the same for this project: anonymous requests redirect
to ``LOGIN_URL``; views marked ``login_required = False`` (Django 5.1's ``login_not_required``) stay open, and so do
the login and logout URLs and static files, which Django 5.1 exempts through its views or which runserver serves.

Imported by ``config.settings``: no Django imports at module level besides ``django`` itself.
"""

import django

MIDDLEWARE_PATH = (
    "django.contrib.auth.middleware.LoginRequiredMiddleware"
    if django.VERSION >= (5, 1)
    else "config.login_required.LoginRequiredMiddleware"
)


class LoginRequiredMiddleware:
    """Stand-in for Django 5.1's LoginRequiredMiddleware on older Django."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        from django.conf import settings
        from django.contrib.auth.views import redirect_to_login
        from django.urls import reverse

        if request.user.is_authenticated or getattr(view_func, "login_required", True) is False:
            return None
        static_url = "/" + settings.STATIC_URL.lstrip("/")
        if request.path_info.startswith(static_url):
            return None
        if request.path_info in (reverse(settings.LOGIN_URL), reverse("logout")):
            return None
        return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
