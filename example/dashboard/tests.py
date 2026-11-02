import re
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

import django_tabler

from .views import _month_starts

User = get_user_model()


class AuthTests(TestCase):
    def test_pages_require_login(self):
        for name in ("dashboard:index", "dashboard:users"):
            response = self.client.get(reverse(name))
            self.assertRedirects(response, f"{reverse('login')}?next={reverse(name)}")

    def test_login_page_renders(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, "Login to your account")

    def test_wrong_password_shows_error(self):
        User.objects.create_user("ann", password="s3cret-pass")
        response = self.client.post(reverse("login"), {"username": "ann", "password": "nope"})
        self.assertContains(response, "alert-danger")

    def test_login_and_logout(self):
        User.objects.create_user("ann", password="s3cret-pass")
        response = self.client.post(reverse("login"), {"username": "ann", "password": "s3cret-pass"})
        self.assertRedirects(response, reverse("dashboard:index"))
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        self.assertEqual(self.client.get(reverse("dashboard:index")).status_code, 302)


class DashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ann", first_name="Ann", last_name="Lee", password="s3cret-pass")
        self.client.force_login(self.user)

    def test_dashboard_shows_user_stats(self):
        User.objects.create_user("bob", is_staff=True)
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.context["totals"]["total"], 2)
        self.assertEqual(response.context["roles"]["values"], [0, 1, 1])
        self.assertEqual(len(response.context["signups"]["values"]), 12)
        self.assertContains(response, 'id="signups-data"')

    def test_members_do_not_see_users_link(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertNotContains(response, reverse("dashboard:users"))

    def test_seed_command_feeds_charts(self):
        call_command("seed_demo_users", count=10, stdout=open("/dev/null", "w"))
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.context["totals"]["total"], 11)
        # The chart covers 12 calendar months; seeded sign-ups reach back up to a year.
        window_start = _month_starts(timezone.now(), 12)[0]
        in_window = User.objects.filter(date_joined__gte=window_start).count()
        self.assertEqual(sum(response.context["signups"]["values"]), in_window)


class UserListTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("root", "root@example.com", "s3cret-pass")
        self.client.force_login(self.admin)

    def test_members_are_forbidden(self):
        self.client.force_login(User.objects.create_user("ann"))
        self.assertEqual(self.client.get(reverse("dashboard:users")).status_code, 403)

    def test_view_permission_is_enough_to_list(self):
        viewer = User.objects.create_user("viewer")
        viewer.user_permissions.add(Permission.objects.get(codename="view_user"))
        self.client.force_login(viewer)
        response = self.client.get(reverse("dashboard:users"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'id="modal-user"')

    def test_search(self):
        User.objects.create_user("ann", email="ann@example.com")
        User.objects.create_user("bob", email="bob@example.com")
        response = self.client.get(reverse("dashboard:users"), {"q": "ann@"})
        self.assertEqual([u.username for u in response.context["page"]], ["ann"])

    def test_create_user(self):
        response = self.client.post(reverse("dashboard:user_create"), {
            "username": "carol",
            "email": "carol@example.com",
            "password1": "a-Long-pass-123",
            "password2": "a-Long-pass-123",
        }, follow=True)
        self.assertRedirects(response, reverse("dashboard:users"))
        self.assertContains(response, "was created")
        self.assertTrue(User.objects.get(username="carol").check_password("a-Long-pass-123"))

    def test_invalid_create_reopens_form_with_errors(self):
        response = self.client.post(reverse("dashboard:user_create"), {
            "username": "root",
            "password1": "x",
            "password2": "y",
        })
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "data-show-on-load", status_code=400)
        self.assertContains(response, "is-invalid", status_code=400)

    def test_create_requires_add_permission(self):
        viewer = User.objects.create_user("viewer")
        viewer.user_permissions.add(Permission.objects.get(codename="view_user"))
        self.client.force_login(viewer)
        response = self.client.post(reverse("dashboard:user_create"), {"username": "x"})
        self.assertEqual(response.status_code, 403)


class LayoutBoundaryTests(SimpleTestCase):
    def test_example_overrides_the_site_name(self):
        self.assertEqual(render_to_string("django_tabler/includes/site_name.html"), "Acme Admin")

    def test_src_does_not_import_the_example(self):
        src = Path(django_tabler.__file__).parents[1]
        allowed = src / "crud_views_tabler" / "tests.py"
        pattern = re.compile(r"^\s*(from|import)\s+(catalog|customers|dashboard|config)\b", re.MULTILINE)
        for path in src.rglob("*.py"):
            if path != allowed:
                with self.subTest(path=path):
                    self.assertIsNone(pattern.search(path.read_text()))
