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

    def test_members_do_not_see_users_link(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertNotContains(response, reverse("dashboard:users"))


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


class RoasteryDashboardTests(TestCase):
    """Known small world: exact numbers for the stat cards, scoped per user."""

    @classmethod
    def setUpTestData(cls):
        from datetime import timedelta
        from decimal import Decimal

        from catalog.models import Beans, Origin, Subscription
        from roastery.models import CuppingScore, CuppingSession, GreenLot, RoastBatch
        from sales.models import Customer, CustomerSubscription, Order, OrderLine
        from sales.permissions import grant_customer

        call_command("seed_demo", stdout=StringIO())  # accounts and groups only matter; wipe the rest
        for model in (RoastBatch, Order, CustomerSubscription, Customer, CuppingScore, CuppingSession, GreenLot):
            model.objects.all().delete()
        cls.alex, cls.sam, cls.kim = (User.objects.get(username=n) for n in ("alex", "sam", "kim"))

        origin = Origin.objects.first()
        beans = Beans.objects.create(name="Dash beans", slug="dash-beans", sku="D-1", price=Decimal("10.00"), origin=origin)
        sub = Subscription.objects.create(name="Dash sub", slug="dash-sub", sku="D-2", price=Decimal("30.00"))
        cls.consumer = Customer.objects.create(name="Consumer One", kind="consumer")
        cls.shop = Customer.objects.create(name="Shop Two", kind="wholesale", company="Shop", price_tier="B")  # 12%
        grant_customer(cls.sam, cls.consumer)

        today = timezone.localdate()
        now = timezone.now()

        def order(customer, state, qty, days_ago, roast_in=None):
            o = Order.objects.create(
                customer=customer, state=state, requested_roast_date=today + timedelta(days=roast_in) if roast_in is not None else None
            )
            OrderLine.objects.create(order=o, product=beans, quantity=qty)
            Order.objects.filter(pk=o.pk).update(created_at=now - timedelta(days=days_ago))
            return o

        cls.to_roast = order(cls.consumer, "confirmed", 5, 5, roast_in=2)  # 50.00
        order(cls.shop, "shipped", 10, 10)  # 100.00 - 12.00 = 88.00
        order(cls.shop, "delivered", 10, 40)  # 88.00, previous 30 days
        order(cls.consumer, "draft", 100, 0)  # excluded
        order(cls.consumer, "cancelled", 100, 2)  # excluded
        order(cls.shop, "roasted", 1, 3)  # 10.00 - 1.20 = 8.80
        order(cls.shop, "confirmed", 2, 1, roast_in=20)  # 17.60, not due this week

        CustomerSubscription.objects.create(customer=cls.consumer, product=sub, next_delivery=today + timedelta(days=3))
        CustomerSubscription.objects.create(customer=cls.shop, product=sub, next_delivery=today + timedelta(days=1))
        CustomerSubscription.objects.create(customer=cls.shop, product=sub, next_delivery=today, is_active=False)

        cls.lot = GreenLot.objects.create(
            code="XX-24-001", origin=origin, producer="P", variety="V", harvest_year=2024,
            kg_purchased=Decimal("100"), kg_on_hand=Decimal("40.5"), price_per_kg=Decimal("8"), arrived_on=today,
        )
        GreenLot.objects.create(
            code="XX-24-002", origin=origin, producer="P", variety="V", harvest_year=2024,
            kg_purchased=Decimal("10"), kg_on_hand=Decimal("10"), price_per_kg=Decimal("8"), arrived_on=today,
        )
        cls.session = CuppingSession.objects.create(lot=cls.lot, held_on=today)
        for taster, value in ((cls.kim, "8"), (cls.alex, "7")):
            CuppingScore.objects.create(
                session=cls.session, taster=taster, **{a: Decimal(value) for a in CuppingScore.ATTRIBUTES}
            )

    def get(self, user):
        self.client.force_login(user)
        return self.client.get(reverse("dashboard:index"))

    def test_stats_match_data(self):
        from decimal import Decimal

        ctx = self.get(self.alex).context
        self.assertEqual(ctx["revenue_30d"], Decimal("164.40"))  # confirmed, roasted, shipped, delivered by created_at
        self.assertEqual(ctx["revenue_trend_pct"], Decimal("86.8"))  # vs 88.00 in the 30 days before
        self.assertEqual(ctx["open_orders"], 3)  # two confirmed, one roasted
        self.assertEqual(ctx["orders_waiting_to_roast"], 2)
        self.assertEqual(list(ctx["orders_to_roast"]), [self.to_roast])
        self.assertEqual(ctx["active_subscriptions"], 2)
        self.assertEqual(ctx["next_subscription_run"], timezone.localdate() + timezone.timedelta(days=1))
        self.assertEqual(ctx["green_stock_kg"], Decimal("50.5"))
        self.assertEqual([s.pk for s in ctx["recent_cuppings"]], [self.session.pk])
        self.assertEqual(ctx["recent_cuppings"][0].average, Decimal("82.5"))  # totals 30 + 7 * 8 and 30 + 7 * 7

    def test_revenue_by_week_has_12_points(self):
        from decimal import Decimal

        weeks = self.get(self.alex).context["revenue_by_week"]
        self.assertEqual(len(weeks), 12)
        self.assertTrue(all(label.startswith("W") for label, _ in weeks))
        self.assertEqual(sum(v for _, v in weeks), Decimal("252.40"))  # the delivered order of 40 days ago counts too

    def test_sam_dashboard_counts_only_granted_customers(self):
        from decimal import Decimal

        ctx = self.get(self.sam).context
        self.assertEqual(ctx["revenue_30d"], Decimal("50.00"))
        self.assertIsNone(ctx["revenue_trend_pct"])  # nothing in the previous period
        self.assertEqual(ctx["open_orders"], 1)
        self.assertEqual(ctx["active_subscriptions"], 1)
        self.assertEqual(ctx["next_subscription_run"], timezone.localdate() + timezone.timedelta(days=3))
        self.assertEqual(sum(v for _, v in ctx["revenue_by_week"]), Decimal("50.00"))
        self.assertEqual(list(ctx["orders_to_roast"]), [self.to_roast])
        self.assertNotContains(self.get(self.sam), "Shop Two")

    def test_kim_sees_all_sales_numbers_and_the_roastery(self):
        from decimal import Decimal

        ctx = self.get(self.kim).context
        self.assertEqual(ctx["revenue_30d"], Decimal("164.40"))
        self.assertEqual(ctx["green_stock_kg"], Decimal("50.5"))

    def test_rows_link_to_crud_pages(self):
        response = self.get(self.alex)
        self.assertContains(response, reverse("order-detail", kwargs={"customer_pk": self.consumer.pk, "pk": self.to_roast.pk}))
        self.assertContains(response, reverse("cupping-detail", kwargs={"lot_pk": self.lot.pk, "pk": self.session.pk}))

    def test_chart_assets_are_pinned_with_sri(self):
        html = self.get(self.alex).content.decode()
        self.assertRegex(html, r'@tabler/core@[\d.]+/dist/libs/apexcharts/[^"]*"[^>]*integrity="sha384-[^"]+"[^>]*crossorigin="anonymous"')
        self.assertIn('id="revenue-data"', html)
        self.assertIsNotNone(finders.find("dashboard/revenue-chart.js"))


def _text(html):
    """The visible text of highlighted code: tags stripped, entities unescaped."""
    import html as html_lib

    return html_lib.unescape(re.sub(r"<[^>]+>", "", html))


class ShowCodeTests(TestCase):
    """The "Show code" panel on crud_views pages and the "How this is themed" page (config/showcode.py)."""

    def setUp(self):
        self.admin = User.objects.create_superuser("root", password="s3cret-pass")
        self.client.force_login(self.admin)

    def test_code_panel_on_crud_pages(self):
        """The page carries the empty shell; the sources come from the fragment endpoint."""
        html = self.client.get(reverse("customer-list")).content.decode()
        url = reverse("code-panel", kwargs={"app_label": "sales"})
        self.assertEqual(url, "/_code/sales/")
        self.assertIn('id="code-panel"', html)
        self.assertIn(f'data-code-url="{url}"', html)
        self.assertIn('data-code-active="sales/views/customers.py"', html)
        self.assertIn('href="#code-panel"', html)  # the "Show code" toggle in the page header
        self.assertIn("acme/code-panel.js", html)
        self.assertNotIn("GuardianViewSet", html)  # no source on the page itself
        fragment = self.client.get(url)
        self.assertEqual(fragment.status_code, 200)
        self.assertIn("cv_customer = GuardianViewSet", _text(fragment.content.decode()))
        self.assertIn('data-code-file="sales/views/customers.py"', fragment.content.decode())

    def test_code_panel_endpoint_rejects_other_labels(self):
        for label in ("auth", "nonexistent", "dashboard", "crud_views_tabler", "django_tabler"):
            self.assertEqual(self.client.get(f"/_code/{label}/").status_code, 404, label)
        for path in ("/_code/../config/", "/_code/..%2Fconfig/", "/_code/config/settings.py/"):
            self.assertEqual(self.client.get(path).status_code, 404, path)

    def test_code_panel_endpoint_requires_login(self):
        self.client.logout()
        url = reverse("code-panel", kwargs={"app_label": "sales"})
        self.assertRedirects(self.client.get(url), f"{reverse('login')}?next={url}")

    def test_pygments_stylesheet_has_light_and_dark_colours(self):
        css = self.client.get(reverse("pygments-css"))
        self.assertEqual(css["Content-Type"], "text/css")
        text = css.content.decode()
        self.assertIn(":root:not([data-bs-theme=dark]) .code-block .k {", text)
        self.assertIn("[data-bs-theme=dark] .code-block .k {", text)
        self.assertNotIn("\npre {", "\n" + text)  # nothing unscoped
        self.assertIn(reverse("pygments-css"), self.client.get(reverse("theming")).content.decode())

    def test_settings_excerpt_handles_every_assignment_form(self):
        from config.showcode import settings_excerpt

        text = "SECRET_KEY = 'x'\nINSTALLED_APPS = ['a']\nINSTALLED_APPS += ['b']\nCRUD_VIEWS_EXTENDS: str = 'p.html'\nDEBUG = True\n"
        self.assertEqual(
            settings_excerpt(text), ["INSTALLED_APPS = ['a']", "INSTALLED_APPS += ['b']", "CRUD_VIEWS_EXTENDS: str = 'p.html'"]
        )

    def test_package_files_skip_binaries(self):
        import tempfile

        from config.showcode import _highlighted, _package_files

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "apps.py").write_text("x = 1\n")
            (root / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n\xff\xfe")
            (root / "bad.css").write_bytes(b"\xff\xfe\x00")
            self.assertEqual([p.name for p in _package_files(root)], ["apps.py", "bad.css"])  # png: no lexer
            bad = root / "bad.css"
            self.assertIsNone(_highlighted(bad, bad.stat().st_mtime_ns))  # not UTF-8: skipped, not a 500

    def test_code_panel_never_shows_theme_imports(self):
        from config.showcode import collect_sources_for_app

        for app in ("sales", "catalog", "roastery", "shipping"):
            sources = collect_sources_for_app(app)
            self.assertTrue(sources, app)
            for source in sources:
                for name in ("django_tabler", "crud_views_tabler"):
                    self.assertNotIn(name, _text(source.html), source.label)

    def test_code_panel_lists_models_views_and_templates_but_not_seed(self):
        from config.showcode import collect_sources_for_app

        labels = [s.label for s in collect_sources_for_app("sales")]
        self.assertIn("sales/models.py", labels)
        self.assertIn("sales/views/customers.py", labels)
        self.assertIn("sales/templates/sales/order_detail.html", labels)
        self.assertNotIn("sales/seed.py", labels)
        self.assertFalse([label for label in labels if "/tests" in label])

    def test_code_panel_only_for_example_apps(self):
        from config.showcode import collect_app_sources, collect_sources_for_app

        class NotAnExampleView:
            pass

        NotAnExampleView.__module__ = "crud_views.lib.views"
        self.assertEqual(collect_app_sources(NotAnExampleView()), [])
        self.assertEqual(collect_sources_for_app("../config"), [])
        self.assertEqual(collect_sources_for_app("dashboard"), [])

    def test_panel_is_collapsed_by_default(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        match = re.search(r'<div class="([^"]*)" id="code-panel"', html)
        self.assertIsNotNone(match)
        self.assertIn("collapse", match.group(1).split())
        self.assertNotIn("show", match.group(1).split())

    def test_theming_page_counts(self):
        from config.showcode import collect_theme_sources

        sources = collect_theme_sources()
        html = self.client.get(reverse("theming")).content.decode()
        lines = sum(s.lines for s in sources)
        self.assertIn(f"The whole theme is {len(sources)} files, {lines} lines.", html)
        self.assertIn("Your app code is unchanged.", html)
        for source in sources:
            self.assertIn(source.label, html)

    def test_theme_sources_cover_the_theme_app(self):
        from config.showcode import collect_theme_sources

        labels = [s.label for s in collect_theme_sources()]
        for label in (
            "crud_views_tabler/apps.py",
            "crud_views_tabler/buttons.py",
            "crud_views_tabler/static/crud_views_tabler/tabler-adapters.js",
            "crud_views_tabler/templates/crud_views_tabler/page.html",
            "example/config/settings.py (excerpt)",
        ):
            self.assertIn(label, labels)
        self.assertFalse([label for label in labels if "__pycache__" in label or "/tests" in label])

    def test_theming_page_shows_the_settings_but_not_the_secret_key(self):
        html = self.client.get(reverse("theming")).content.decode()
        text = _text(html)
        for name in ("INSTALLED_APPS", "CRUD_VIEWS_EXTENDS", "CRISPY_TEMPLATE_PACK", "DJANGO_TABLES2_TEMPLATE"):
            self.assertIn(name, text)
        self.assertNotIn("SECRET_KEY", html)
        self.assertNotIn(settings.SECRET_KEY, html)
        self.assertNotIn("django-insecure", html)

    def test_theming_page_links_to_the_docs(self):
        html = self.client.get(reverse("theming")).content.decode()
        self.assertIn("https://django-crud-views.readthedocs.io/en/latest/reference/theme/", html)
        self.assertIn("https://github.com/alexander-jacob/tabler-test/blob/main/docs/crud_views_tabler.md", html)

    def test_theming_is_in_the_nav_for_every_user(self):
        User.objects.create_user("plain", password="s3cret-pass")
        self.client.force_login(User.objects.get(username="plain"))
        response = self.client.get(reverse("dashboard:index"))
        self.assertContains(response, reverse("theming"))
        self.assertContains(response, "How this is themed")
        self.assertEqual(self.client.get(reverse("theming")).status_code, 200)

    def test_theming_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("theming"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('theming')}")
