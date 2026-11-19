"""config.login_required: the stand-in for Django 5.1's LoginRequiredMiddleware, used on older Django.

The tests run the stand-in on every Django version, so it is exercised even where Django's own middleware is used.
"""

from unittest import skipUnless

import django
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.test.utils import override_script_prefix
from django.urls import path, resolve, reverse

from config import login_required
from config.urls import urlpatterns as _project_urlpatterns

STAND_IN = "config.login_required.LoginRequiredMiddleware"


def _open_view(request):
    return HttpResponse("open")


_open_view.login_required = False  # what Django 5.1's login_not_required decorator sets

urlpatterns = [path("_open/", _open_view, name="open-view"), *_project_urlpatterns]


def _stand_in_middleware():
    return [STAND_IN if name == login_required.MIDDLEWARE_PATH else name for name in settings.MIDDLEWARE]


class SelectionTest(TestCase):
    def test_selected_middleware_matches_django_version(self):
        django_path = "django.contrib.auth.middleware.LoginRequiredMiddleware"
        self.assertEqual(django_path == login_required.MIDDLEWARE_PATH, django.VERSION >= (5, 1))
        self.assertIn(login_required.MIDDLEWARE_PATH, settings.MIDDLEWARE)


class StandInTest(TestCase):
    def setUp(self):
        self._settings = override_settings(MIDDLEWARE=_stand_in_middleware(), ROOT_URLCONF=__name__)
        self._settings.enable()
        self.addCleanup(self._settings.disable)

    def test_anonymous_page_redirects_to_login(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertRedirects(response, f"{reverse('login')}?next=/", fetch_redirect_response=False)

    def test_login_page_is_open(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)

    def test_logout_post_redirects_to_login_like_django(self):
        # Django 5.1's middleware does not exempt LogoutView either: anonymous logout goes to the login page.
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, f"{reverse('login')}?next=/accounts/logout/", fetch_redirect_response=False)

    def test_signed_in_user_passes(self):
        self.client.force_login(get_user_model().objects.create_user("visitor", password="x"))
        self.assertEqual(self.client.get(reverse("dashboard:index")).status_code, 200)

    @override_settings(STATIC_URL="/")
    def test_static_url_does_not_open_pages(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertRedirects(response, f"{reverse('login')}?next=/", fetch_redirect_response=False)

    @override_settings(LOGIN_URL="/accounts/login/")
    def test_login_url_given_as_a_path(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertRedirects(response, "/accounts/login/?next=/", fetch_redirect_response=False)

    def test_view_marked_login_not_required_is_open(self):
        self.assertEqual(self.client.get(reverse("open-view")).status_code, 200)

    def test_login_page_is_open_under_a_script_prefix(self):
        # Deployed below /sub/: reverse() includes the prefix, request.path_info does not. The test client resets the
        # prefix per request, so the middleware is called directly.
        request = RequestFactory().get("/accounts/login/")
        request.user = AnonymousUser()
        view = resolve("/accounts/login/").func
        with override_script_prefix("/sub/"):
            self.assertIsNone(
                login_required.LoginRequiredMiddleware(lambda r: None).process_view(request, view, (), {})
            )


@skipUnless(django.VERSION >= (5, 1), "compares with Django 5.1's LoginRequiredMiddleware")
class ParityWithDjangoTest(TestCase):
    """The stand-in answers exactly like Django's middleware, request by request."""

    REQUESTS = [
        ("get", "/"),
        ("get", "/customer/"),
        ("get", "/accounts/login/"),
        ("post", "/accounts/logout/"),
        ("get", "/_open/"),
        ("get", "/no-such-page/"),
        ("get", "/customer/?page=2&sort=name"),
    ]

    def answers(self, middleware):
        with override_settings(MIDDLEWARE=middleware, ROOT_URLCONF=__name__):
            client = self.client_class()
            return [
                (r.status_code, r.headers.get("Location")) for r in (getattr(client, m)(p) for m, p in self.REQUESTS)
            ]

    def test_same_answers_as_django(self):
        django_middleware = [*settings.MIDDLEWARE]
        self.assertEqual(self.answers(_stand_in_middleware()), self.answers(django_middleware))
