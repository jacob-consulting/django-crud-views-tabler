"""The same real routes and access contract under two template-only compositions."""

from copy import deepcopy
from html import unescape
import re

from django.conf import settings
from django.template.loader import get_template, render_to_string
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from catalog.models import Subscription
from sales.models import CustomerSubscription
from . import test_customer_navigation as navigation


def template_sources(sources):
    templates = deepcopy(settings.TEMPLATES)
    templates[0]["APP_DIRS"] = False
    templates[0]["OPTIONS"]["loaders"] = [
        ("django.template.loaders.locmem.Loader", sources),
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
    ]
    return override_settings(TEMPLATES=templates)


def select_layout(layout):
    return template_sources({
        "project/crud_views.html": '{% extends "project/customer_navigation/' + layout + '.html" %}'
    })


class SelectedLayout:
    def setUp(self):
        self.enterContext(select_layout(self.navigation_layout))
        super().setUp()


class HeaderPageCoverageTests(SelectedLayout, navigation.PageCoverageTests):
    navigation_layout = "header"


class CardPageCoverageTests(SelectedLayout, navigation.PageCoverageTests):
    navigation_layout = "card"


class HeaderNavigationAccessTests(SelectedLayout, navigation.NavigationAccessTests):
    navigation_layout = "header"


class CardNavigationAccessTests(SelectedLayout, navigation.NavigationAccessTests):
    navigation_layout = "card"


class HeaderNavigationPreservationTests(SelectedLayout, navigation.NavigationPreservationTests):
    navigation_layout = "header"


class CardNavigationPreservationTests(SelectedLayout, navigation.NavigationPreservationTests):
    navigation_layout = "card"


class TemplateLayoutTests(navigation.NavigationAssertions, navigation.OrderTestCase):
    def setUp(self):
        self.login()
        self.order = self.make_order(customer=self.mine)
        self.subscription = CustomerSubscription.objects.create(
            customer=self.mine, product=Subscription.objects.first(), next_delivery=timezone.localdate())

    def test_theme_seam_precedes_filters_and_content(self):
        response = self.client.get(reverse("order-list", kwargs={"customer_pk": self.mine.pk}))
        view = response.context["view"]
        probe = ('{% extends "crud_views_tabler/page.html" %}'
                 '{% block cv_content_before %}NAVIGATION-SEAM{% endblock %}'
                 '{% block cv_filter %}FILTER-SEAM{% endblock %}'
                 '{% block cv_content %}CONTENT-SEAM{% endblock %}')
        with template_sources({"seam-probe.html": probe}):
            html = render_to_string("seam-probe.html", {"view": view}, request=view.request)
        main = html.split("<main ", 1)[1].split("</main>", 1)[0]
        self.assertIn("NAVIGATION-SEAM", main)
        self.assertLess(main.index("NAVIGATION-SEAM"), main.index("FILTER-SEAM"))
        self.assertLess(main.index("FILTER-SEAM"), main.index("CONTENT-SEAM"))

    def test_same_link_tuples_and_placement_on_all_thirteen_routes(self):
        cases = [("customer-detail", {"pk": self.mine.pk}, "Details")]
        for prefix, obj, actions, section in (
            ("order", self.order, ("list", "detail", "create", "update", "workflow"), "Orders"),
            ("address", self.mine.addresses.first(), ("list", "detail", "create", "update"), "Addresses"),
            ("subscription", self.subscription, ("list", "create", "update"), "Subscriptions"),
        ):
            for action in actions:
                kwargs = {"customer_pk": self.mine.pk}
                if action not in ("list", "create"):
                    kwargs["pk"] = obj.pk
                cases.append((f"{prefix}-{action}", kwargs, section))
        self.assertEqual(len(cases), 13)
        for name, kwargs, section in cases:
            snapshots = []
            for layout in ("header", "card"):
                with self.subTest(route=name, layout=layout), select_layout(layout):
                    self.navigation_layout = layout
                    response = self.client.get(reverse(name, kwargs=kwargs))
                    self.navigation(response, self.mine, active=section)
                    html = response.content.decode()
                    nav = re.search(r'<nav\b[^>]*data-customer-navigation[^>]*>(.*?)</nav>', html, re.S).group(1)
                    snapshots.append([(unescape(url), title, 'aria-current="page"' in attrs)
                                      for url, attrs, title in re.findall(
                                          r'<a\b[^>]*href="([^"]+)"([^>]*)>([^<]+)</a>', nav)])
                    self.assertEqual(html.count("Show code</a>"), 1)
                    self.assertTemplateUsed(response, f"project/customer_navigation/{layout}.html")
            self.assertEqual(snapshots[0], snapshots[1])

    def test_card_precedes_filter_and_content_without_wrapping_them(self):
        response = self.client.get(reverse("order-list", kwargs={"customer_pk": self.mine.pk}))
        view = response.context["view"]
        probe = ('{% extends "project/crud_views.html" %}'
                 '{% block cv_filter %}<div data-test-filter>Filter</div>{% endblock %}'
                 '{% block cv_content %}<div data-test-content>Content</div>{% endblock %}')
        with select_layout("card"):
            # Retain the selector override when adding a one-off leaf that exposes block ordering.
            sources = dict(settings.TEMPLATES[0]["OPTIONS"]["loaders"][0][1])
            sources["content-probe.html"] = probe
            with template_sources(sources):
                html = render_to_string("content-probe.html", {"view": view}, request=view.request)
        main = html.split("<main ", 1)[1].split("</main>", 1)[0]
        self.assertRegex(main, r'(?s)</nav>\s*</div>\s*</div>\s*<div data-test-filter')
        self.assertLess(main.index("data-customer-navigation-card"), main.index("data-test-filter"))
        self.assertLess(main.index("data-test-filter"), main.index("data-test-content"))

    def test_selection_restores_settings_and_cached_default(self):
        before = deepcopy(settings.TEMPLATES)
        default_source = get_template("project/crud_views.html").template.source
        for layout in ("card", "header", "card"):
            with select_layout(layout):
                self.assertIn(f'/{layout}.html', get_template("project/crud_views.html").template.source)
                self.assertTrue(str(get_template(f"project/customer_navigation/{layout}.html").origin.name).endswith(
                    f"example/templates/project/customer_navigation/{layout}.html"))
            self.assertEqual(settings.TEMPLATES, before)
            self.assertEqual(get_template("project/crud_views.html").template.source, default_source)
        self.assertIn("/header.html", default_source)

    def test_empty_theme_seam_preserves_nonparticipating_output(self):
        response = self.client.get(reverse("customer-list"))
        view = response.context["view"]
        template = "crud_views_tabler/page.html"
        source = get_template(template).template.source
        original = render_to_string(template, {"view": view}, request=view.request)
        without_seam = source.replace("{% block cv_content_before %}{% endblock cv_content_before %}", "")
        with template_sources({template: without_seam}):
            self.assertEqual(render_to_string(template, {"view": view}, request=view.request), original)
        self.no_navigation(response)
