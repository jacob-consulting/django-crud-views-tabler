"""The public demo's settings and URLconf (config.settings_demo, config.urls_demo; render.yaml)."""

import importlib
import os
import sys
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

DEMO_ENV = {"SECRET_KEY": "test-secret", "RENDER_EXTERNAL_HOSTNAME": "demo.example.org"}


def load_demo_settings(env):
    sys.modules.pop("config.settings_demo", None)
    with mock.patch.dict(os.environ, env, clear=False):
        for name in {"SECRET_KEY", "RENDER_EXTERNAL_HOSTNAME"} - env.keys():
            os.environ.pop(name, None)
        return importlib.import_module("config.settings_demo")


class DemoSettingsTest(SimpleTestCase):
    def test_hardened_values(self):
        demo = load_demo_settings(DEMO_ENV)
        self.assertFalse(demo.DEBUG)
        self.assertEqual(demo.SECRET_KEY, "test-secret")
        self.assertEqual(demo.ALLOWED_HOSTS, ["demo.example.org"])
        self.assertEqual(demo.CSRF_TRUSTED_ORIGINS, ["https://demo.example.org"])
        self.assertTrue(demo.SESSION_COOKIE_SECURE)
        self.assertTrue(demo.CSRF_COOKIE_SECURE)
        self.assertFalse(demo.CRUD_VIEWS_MANAGE_ACCESS_TRACE)
        self.assertEqual(demo.DEMO_WRITE_RATES, ("30/m", "300/d"))
        self.assertEqual(demo.ROOT_URLCONF, "config.urls_demo")

    def test_middleware_order(self):
        demo = load_demo_settings(DEMO_ENV)
        self.assertEqual(demo.MIDDLEWARE[0], "django.middleware.security.SecurityMiddleware")
        self.assertEqual(demo.MIDDLEWARE[1], "whitenoise.middleware.WhiteNoiseMiddleware")
        self.assertEqual(demo.MIDDLEWARE[-2], "config.boot.BootIdMiddleware")
        self.assertEqual(demo.MIDDLEWARE[-1], "config.ratelimit.WriteRateLimitMiddleware")

    def test_base_middleware_is_not_mutated(self):
        from config import settings as base

        load_demo_settings(DEMO_ENV)
        self.assertNotIn("whitenoise.middleware.WhiteNoiseMiddleware", base.MIDDLEWARE)
        self.assertNotIn("config.ratelimit.WriteRateLimitMiddleware", base.MIDDLEWARE)

    def test_missing_secret_key_fails(self):
        with self.assertRaises(KeyError):
            load_demo_settings({"RENDER_EXTERNAL_HOSTNAME": "demo.example.org"})

    def test_missing_hostname_allows_no_host(self):
        demo = load_demo_settings({"SECRET_KEY": "test-secret"})
        self.assertEqual(demo.ALLOWED_HOSTS, [])
        self.assertEqual(demo.CSRF_TRUSTED_ORIGINS, [])

    def test_local_tunnel_host_is_not_allowed(self):
        demo = load_demo_settings(DEMO_ENV)
        self.assertNotIn("cv.jacob-consulting.org", demo.ALLOWED_HOSTS)


class DemoUrlsTest(TestCase):
    def test_admin_mounted_locally(self):
        self.assertEqual(self.client.get("/admin/").status_code, 302)  # redirect to the admin login

    @override_settings(ROOT_URLCONF="config.urls_demo")
    def test_admin_not_mounted_on_demo(self):
        self.assertEqual(self.client.get("/admin/").status_code, 404)

    @override_settings(ROOT_URLCONF="config.urls_demo")
    def test_rest_of_site_still_routed(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)


class DemoStartTest(TestCase):
    """render.yaml's start command runs seed_demo --reset on every start, also on a database that has the data."""

    def test_seed_demo_reset_on_empty_database(self):
        call_command("seed_demo", "--reset", stdout=StringIO())
        self.assertEqual(
            set(
                get_user_model().objects.filter(username__in=["alex", "sam", "kim"]).values_list("username", flat=True)
            ),
            {"alex", "sam", "kim"},
        )

    def test_seed_demo_reset_twice(self):
        call_command("seed_demo", "--reset", stdout=StringIO())
        call_command("seed_demo", "--reset", stdout=StringIO())
        self.assertEqual(get_user_model().objects.filter(username="sam").count(), 1)


class DemoManifestStaticTest(TestCase):
    """DEBUG=False with whitenoise's manifest storage: a static path missing from the manifest raises at render time."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        import tempfile

        cls._static_root = tempfile.TemporaryDirectory()
        demo = load_demo_settings(DEMO_ENV)
        cls._settings = override_settings(
            DEBUG=False,
            STATIC_ROOT=cls._static_root.name,
            STORAGES=demo.STORAGES,
            ALLOWED_HOSTS=["testserver"],
        )
        cls._settings.enable()
        call_command("collectstatic", interactive=False, verbosity=0)

    @classmethod
    def tearDownClass(cls):
        cls._settings.disable()
        cls._static_root.cleanup()
        super().tearDownClass()

    def test_login_page_renders(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)

    def test_crud_views_list_renders(self):
        call_command("seed_demo", stdout=StringIO())
        self.client.login(username="alex", password="demo")
        self.assertEqual(self.client.get(reverse("customer-list")).status_code, 200)
