"""Login required on every page, on every supported Django version.

Django 5.1 added ``django.contrib.auth.middleware.LoginRequiredMiddleware``; ``MIDDLEWARE_PATH`` names it there. On
older Django (4.2) it names the stand-in below, a port of Django 5.1's middleware: requests are exempt by *view*
(``login_required = False``, which Django 5.1's ``login_not_required`` sets), never by URL path. One addition: Django
5.1 marks ``LoginView`` as ``login_not_required``; Django 4.2 does not, so the stand-in exempts ``LoginView`` and its
subclasses by class. ``ParityWithDjangoTest`` checks that both answer the same, request by request.

Imported by ``config.settings``: no Django imports at module level besides ``django`` itself.
"""

import django

MIDDLEWARE_PATH = (
    "django.contrib.auth.middleware.LoginRequiredMiddleware"
    if django.VERSION >= (5, 1)
    else "config.login_required.LoginRequiredMiddleware"
)


class LoginRequiredMiddleware:
    """Stand-in for Django 5.1's LoginRequiredMiddleware on older Django (same logic, same answers)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not getattr(view_func, "login_required", True) or _is_login_view(view_func):
            return None
        if request.user.is_authenticated:
            return None
        return self.handle_no_permission(request, view_func)

    def handle_no_permission(self, request, view_func):
        from urllib.parse import urlsplit

        from django.conf import settings
        from django.contrib.auth import REDIRECT_FIELD_NAME
        from django.contrib.auth.views import redirect_to_login
        from django.shortcuts import resolve_url

        login_url = str(getattr(view_func, "login_url", None) or settings.LOGIN_URL)
        path = request.build_absolute_uri()
        resolved_login_url = resolve_url(login_url)
        # Same scheme and host as the login page: use the path as the "next" URL.
        login_scheme, login_netloc = urlsplit(resolved_login_url)[:2]
        current_scheme, current_netloc = urlsplit(path)[:2]
        if (not login_scheme or login_scheme == current_scheme) and (
            not login_netloc or login_netloc == current_netloc
        ):
            path = request.get_full_path()
        redirect_field_name = getattr(view_func, "redirect_field_name", REDIRECT_FIELD_NAME)
        return redirect_to_login(path, resolved_login_url, redirect_field_name)


def _is_login_view(view_func) -> bool:
    from django.contrib.auth.views import LoginView

    view_class = getattr(view_func, "view_class", None)
    return isinstance(view_class, type) and issubclass(view_class, LoginView)
