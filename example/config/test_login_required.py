"""config.login_required: the stand-in for Django 5.1's LoginRequiredMiddleware, used on older Django.

The tests run the stand-in on every Django version, so it is exercised even where Django's own middleware is used.
"""

import django
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.urls import path, reverse

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

    def test_logout_post_is_open(self):
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("login"))  # LOGOUT_REDIRECT_URL, no ?next=

    def test_signed_in_user_passes(self):
        self.client.force_login(get_user_model().objects.create_user("visitor", password="x"))
        self.assertEqual(self.client.get(reverse("dashboard:index")).status_code, 200)

    def test_static_url_is_open(self):
        response = self.client.get("/" + settings.STATIC_URL.lstrip("/") + "django_tabler/django_tabler.css")
        self.assertNotEqual(response.status_code, 302)

    def test_view_marked_login_not_required_is_open(self):
        self.assertEqual(self.client.get(reverse("open-view")).status_code, 200)
