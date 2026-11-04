import re
from pathlib import Path

from io import StringIO

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Permission
from django.contrib.staticfiles import finders
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
        call_command("seed_demo", stdout=open("/dev/null", "w"))
        response = self.client.get(reverse("dashboard:index"))
        # ann plus alex, sam and kim
        self.assertEqual(response.context["totals"]["total"], 4)
        window_start = _month_starts(timezone.now(), 12)[0]
        in_window = User.objects.filter(date_joined__gte=window_start).count()
        self.assertEqual(sum(response.context["signups"]["values"]), in_window)


class DemoAccountTests(TestCase):
    def test_seed_creates_demo_accounts(self):
        call_command("seed_demo", stdout=open("/dev/null", "w"))
        for name in ("alex", "sam", "kim"):
            self.assertTrue(User.objects.filter(username=name).exists())
        self.assertIsNotNone(authenticate(username="sam", password="demo"))
        self.assertTrue(User.objects.get(username="sam").groups.filter(name="Account managers").exists())

    def test_seed_demo_refuses_when_accounts_exist(self):
        call_command("seed_demo", stdout=open("/dev/null", "w"))
        out = StringIO()
        call_command("seed_demo", stdout=out)
        self.assertEqual(out.getvalue().strip(), "Demo data already present; use --reset to rebuild.")
        self.assertEqual(User.objects.filter(username__in=("alex", "sam", "kim")).count(), 3)

    def test_login_page_lists_demo_accounts(self):
        html = self.client.get("/accounts/login/").content.decode()
        for name in ("Alex", "Sam", "Kim"):
            self.assertIn(name, html)
        self.assertIn('data-demo-user="sam"', html)

    def test_crud_views_extends_project_template(self):
        self.assertEqual(settings.CRUD_VIEWS_EXTENDS, "project/crud_views.html")


class DashboardIconTests(TestCase):
    def test_dashboard_icons_still_render(self):
        self.client.force_login(User.objects.create_user("ann"))
        html = self.client.get(reverse("dashboard:index")).content.decode()
        self.assertIn("<svg", html)
        self.assertNotIn("<i class=", html)


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


class LayoutSwitchTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_user("switcher"))
        self.html = self.client.get(reverse("dashboard:index")).content.decode()

    def test_page_renders_both_navigations(self):
        self.assertEqual(self.html.count("<header class=\"navbar navbar-expand-md"), 1)
        self.assertEqual(self.html.count("<aside class=\"navbar navbar-vertical navbar-expand-lg"), 1)

    def test_sidebar_comes_before_the_page_wrapper_inside_page(self):
        # Tabler's CSS shows or hides each navigation through `.page > .navbar`.
        self.assertRegex(self.html, r"<div class=\"page\">\s*<aside class=\"navbar navbar-vertical")

    def test_each_navigation_has_its_own_menu_target(self):
        self.assertIn('data-bs-target="#navbar-menu"', self.html)
        self.assertIn('id="navbar-menu"', self.html)
        self.assertIn('data-bs-target="#sidebar-menu"', self.html)
        self.assertIn('id="sidebar-menu"', self.html)

    def test_no_id_is_used_twice(self):
        ids = re.findall(r"\sid=\"([^\"]+)\"", self.html)
        self.assertEqual(sorted(ids), sorted(set(ids)))

    def test_each_navigation_has_a_layout_switch(self):
        self.assertEqual(self.html.count('aria-label="Layout settings"'), 2)

    def test_sidebar_tools_are_in_the_footer_outside_the_collapse(self):
        # Tabler restyles every dropdown inside a folded .navbar-collapse as a small flyout,
        # which collapses the layout panel and traps the user in the folded sidebar.
        sidebar = self.html[self.html.index("<aside"):self.html.index("</aside>")]
        footer = sidebar[sidebar.index('class="navbar-footer"'):sidebar.index('id="sidebar-menu"')]
        for label in ("Layout settings", "Enable dark mode", "Open user menu"):
            with self.subTest(label=label):
                self.assertIn(f'aria-label="{label}"', footer)

    def test_sidebar_tools_share_one_row_on_a_phone(self):
        # Below the sidebar's lg breakpoint the footer sits in the top bar.
        self.assertRegex(self.html, r'class="navbar-footer">\s*<ul class="navbar-nav flex-row flex-lg-column">')

    def test_sidebar_switch_menu_is_anchored_to_its_start(self):
        # Tabler anchors a footer dropup to its end on a phone, which runs off the left edge.
        sidebar = self.html[self.html.index("<aside"):self.html.index("</aside>")]
        self.assertRegex(sidebar, r'aria-label="Layout settings"[\s\S]*?<div class="dropdown-menu start-0 end-auto p-3"')

    def test_switch_offers_every_option_with_its_tabler_settings(self):
        for label, settings in (
            ("Top", '{"navbar-position":"horizontal","sidebar":"default"}'),
            ("Side", '{"navbar-position":"vertical","sidebar":"default"}'),
            ("Folded", '{"navbar-position":"vertical","sidebar":"folded"}'),
            ("Fluid", '{"layout":"fluid"}'),
            ("Boxed", '{"layout":"boxed"}'),
            ("Dark", '{"navbar-theme":"dark"}'),
            ("Floating", '{"navbar-style":"floating"}'),
        ):
            with self.subTest(label=label):
                self.assertRegex(self.html, rf"data-layout-settings='{re.escape(settings)}'[^>]*>\s*{label}\s*<")

    def test_sidebar_switch_opens_upwards(self):
        # It sits at the bottom of the sidebar: opening sideways runs off the window.
        sidebar = self.html[self.html.index("<aside"):self.html.index("</aside>")]
        self.assertRegex(sidebar, r'<li class="nav-item dropup">\s*<button[^>]*aria-label="Layout settings"')

    def test_stylesheet_is_loaded_and_exists(self):
        self.assertIn('href="/static/django_tabler/django_tabler.css"', self.html)
        self.assertIsNotNone(finders.find("django_tabler/django_tabler.css"))

    def test_switch_script_is_loaded_and_exists(self):
        self.assertIn('src="/static/django_tabler/layout-switch.js"', self.html)
        self.assertIsNotNone(finders.find("django_tabler/layout-switch.js"))

    def test_nothing_is_set_on_html_by_the_server(self):
        # localStorage is the only store: a server value would be a second source of truth.
        self.assertIn('<html lang="en">', self.html)


class LayoutBoundaryTests(SimpleTestCase):
    def test_example_overrides_the_site_name(self):
        self.assertEqual(render_to_string("django_tabler/includes/site_name.html"), "Acme Roasters")

    def test_src_does_not_import_the_example(self):
        src = Path(django_tabler.__file__).parents[1]
        pattern = re.compile(
            r"^\s*(from|import)\s+(catalog|customers|dashboard|config|sales|roastery|shipping|showcase)\b", re.MULTILINE
        )
        for path in src.rglob("*.py"):
            with self.subTest(path=path):
                self.assertIsNone(pattern.search(path.read_text()))


def _counts():
    """Row counts of every demo model, by label."""
    from django.apps import apps

    labels = ("catalog", "sales", "roastery")
    models = [m for label in labels for m in apps.get_app_config(label).get_models()]
    counts = {m._meta.label: m._base_manager.count() for m in models}
    counts["auth.User"] = User.objects.count()
    return counts


class SeedWorldTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())

    def test_seed_refuses_on_populated_db(self):
        before = _counts()
        out = StringIO()
        call_command("seed_demo", stdout=out)
        self.assertEqual(out.getvalue().strip(), "Demo data already present; use --reset to rebuild.")
        self.assertEqual(_counts(), before)

    def test_seed_reset_is_deterministic(self):
        from sales.models import Customer

        User.objects.create_superuser("admin", "a@example.com", "admin")
        call_command("seed_demo", "--reset", stdout=StringIO())
        first = (_counts(), Customer.objects.order_by("pk").first().name)
        call_command("seed_demo", "--reset", stdout=StringIO())
        self.assertEqual((_counts(), Customer.objects.order_by("pk").first().name), first)
        self.assertTrue(User.objects.filter(username="admin").exists())  # reset never touches other users
        self.assertEqual(User.objects.count(), 4)

    def test_seed_world_shape(self):
        from datetime import timedelta

        from django.db.models import Count
        from guardian.shortcuts import get_objects_for_user

        from catalog.models import Beans, Equipment, Product, Subscription
        from roastery.models import GreenLot
        from sales.models import Customer, CustomerSubscription, Order, OrderState

        self.assertGreaterEqual(Customer.objects.count(), 20)
        self.assertGreaterEqual(Order.objects.count(), 60)
        self.assertEqual({o.state for o in Order.objects.all()}, {s.value for s in OrderState})
        self.assertGreaterEqual(Order.objects.filter(state=OrderState.DELIVERED).count(), 20)  # history, not all drafts
        self.assertLess(Order.objects.filter(state=OrderState.DRAFT).count(), 15)
        self.assertGreaterEqual(Product.objects.count(), 25)
        for model in (Beans, Equipment, Subscription):
            self.assertGreater(model.objects.count(), 0)
        lots = GreenLot.objects.annotate(n=Count("sessions__scores")).filter(n__gt=0)
        self.assertGreaterEqual(lots.count(), 6)
        sam = User.objects.get(username="sam")
        self.assertGreaterEqual(get_objects_for_user(sam, "sales.view_customer", Customer).count(), 3)
        dates = [o.created_at.date() for o in Order.objects.all()]
        today = timezone.localdate()
        self.assertGreaterEqual((today - min(dates)).days, 80)
        self.assertLessEqual((today - min(dates)).days, 92)
        for start in range(0, 90, 30):  # every month has orders
            window = [d for d in dates if start <= (today - d).days < start + 30]
            self.assertGreaterEqual(len(window), 10)
        self.assertGreaterEqual(CustomerSubscription.objects.filter(is_active=True).count(), 10)
        self.assertTrue(Order.objects.filter(roast_batches__isnull=False).exists())
