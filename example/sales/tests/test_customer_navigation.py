"""Integration checks for the private customer section navigation experiment."""

import re
from html import escape, unescape
from types import SimpleNamespace
from unittest.mock import Mock

from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from catalog.models import Subscription
from config.templatetags.acme_nav import customer_navigation
from sales.models import CustomerSubscription, OrderState
from sales.permissions import grant_customer
from .test_customers import SalesTestCase
from .test_orders import OrderTestCase


class NavigationAssertions:
    """Assertions scoped to the added body region, independent of document titles."""

    def navigation(self, response, customer, active=None, titles=None):
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        header = html.split('<div class="page-header d-print-none">', 1)[1].split('<main ', 1)[0]
        match = re.search(r'<section\b[^>]*data-customer-navigation[^>]*>(.*?)</section>', header, re.S)
        self.assertIsNotNone(match)
        body = match.group(1)
        self.assertEqual(body.count("data-customer-identity"), 1)
        self.assertIn(escape(customer.name), body)
        self.assertIn(f">{escape(customer.initials)}</span>", body)
        self.assertLess(header.index("</section>"), header.index('class="row g-2 align-items-center"'))
        links = [(unescape(url), title) for url, title in
                 re.findall(r'<a\b[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', body)]
        destinations = {
            "Details": reverse("customer-detail", kwargs={"pk": customer.pk}),
            "Orders": reverse("order-list", kwargs={"customer_pk": customer.pk}),
            "Addresses": reverse("address-list", kwargs={"customer_pk": customer.pk}),
            "Subscriptions": reverse("subscription-list", kwargs={"customer_pk": customer.pk}),
        }
        titles = list(destinations) if titles is None else titles
        self.assertEqual(links, [(destinations[title], title) for title in titles])
        self.assertEqual(body.count('aria-current="page"'), int(active is not None))
        if active:
            self.assertRegex(body, rf'<a[^>]*aria-current="page"[^>]*>{active}</a>')
        if titles:
            self.assertLess(body.index("data-customer-identity"), body.index("<nav"))
        else:
            self.assertNotIn("<nav", body)
        return links

    def no_navigation(self, response):
        self.assertNotIn(b"data-customer-navigation", response.content)
        self.assertNotIn(b"data-customer-identity", response.content)


class PageCoverageTests(NavigationAssertions, OrderTestCase):
    def setUp(self):
        self.login()
        self.order = self.make_order(customer=self.mine)
        self.address = self.mine.addresses.first()
        self.subscription = CustomerSubscription.objects.create(
            customer=self.mine, product=Subscription.objects.first(), next_delivery=timezone.localdate()
        )

    def test_thirteen_full_pages_and_same_customer_destinations(self):
        actor = self.world["users"]["alex"]
        self.assertTrue(self.order.is_editable)
        self.assertIn("wf_confirm", [t.name for t in self.order.get_available_user_state_transitions(actor)])
        self.order.workflow_check_transition("wf_confirm", user=actor)
        cases = [("customer-detail", {"pk": self.mine.pk}, "Details")]
        for prefix, obj, actions, section in (
            ("order", self.order, ("list", "detail", "create", "update", "workflow"), "Orders"),
            ("address", self.address, ("list", "detail", "create", "update"), "Addresses"),
            ("subscription", self.subscription, ("list", "create", "update"), "Subscriptions"),
        ):
            for action in actions:
                kwargs = {"customer_pk": self.mine.pk}
                if action not in ("list", "create"):
                    kwargs["pk"] = obj.pk
                cases.append((f"{prefix}-{action}", kwargs, section))
        self.assertEqual(len(cases), 13)
        for name, kwargs, section in cases:
            with self.subTest(route=name):
                response = self.client.get(reverse(name, kwargs=kwargs))
                links = self.navigation(response, self.mine, active=section)
                self.assertEqual(response.content.decode().count("Show code</a>"), 1)
                for url, title in links:
                    destination = self.client.get(url)
                    self.navigation(destination, self.mine, active=title)
                    view = destination.context["view"]
                    reached = view.object if title == "Details" else view.cv_get_parent_object()
                    self.assertEqual(reached.pk, self.mine.pk)

    def test_order_detail_preserves_badge_transition_form_and_tracking(self):
        url = reverse("order-detail", kwargs=self.order_kwargs(self.order))
        response = self.client.get(url)
        self.navigation(response, self.mine, active="Orders")
        html = response.content.decode()
        self.assertRegex(html, r'class="page-title"[^>]*>.*?badge bg-secondary-lt')
        self.assertIn('data-transition="wf_confirm"', html)
        self.assertIn('name="csrfmiddlewaretoken"', html)
        self.assertIn(f'action="{reverse("order-workflow", kwargs=self.order_kwargs(self.order))}"', html)
        shipped = self.make_order(customer=self.mine, state=OrderState.SHIPPED)
        response = self.client.get(reverse("order-detail", kwargs=self.order_kwargs(shipped)))
        self.navigation(response, self.mine, active="Orders")
        self.assertContains(response, "Track shipment")
        self.assertContains(response, reverse("shipment-detail", kwargs={"pk": f"ACME{shipped.number:08d}"}))

    def test_delete_full_pages_and_real_modal_responses_are_excluded(self):
        cases = [
            ("customer-delete", {"pk": self.mine.pk}, "customer-detail"),
            ("order-delete", self.order_kwargs(self.order), "order-detail"),
            ("address-delete", {"customer_pk": self.mine.pk, "pk": self.address.pk}, "address-detail"),
            ("subscription-delete", {"customer_pk": self.mine.pk, "pk": self.subscription.pk}, "subscription-update"),
        ]
        for name, kwargs, ordinary in cases:
            with self.subTest(route=name):
                for headers in ({}, {"HTTP_X_CV_MODAL": "true"}):
                    response = self.client.get(reverse(name, kwargs=kwargs), **headers)
                    self.assertEqual(response.status_code, 200)
                    self.no_navigation(response)
                self.assertContains(self.client.get(reverse(ordinary, kwargs=kwargs)), "data-customer-navigation")

    def test_excluded_routes_and_modal_guard_before_parent_lookup(self):
        cases = [(name, {}) for name in (
            "customer-list", "customer-create", "orders-list", "orders-create", "subscriptions-list",
            "subscriptions-run", "dashboard:index",
        )]
        cases += [("customer-update", {"pk": self.mine.pk})]
        cases += [(name, self.order_kwargs(self.order)) for name in ("order-packing_slip", "order-duplicate")]
        for name, kwargs in cases:
            with self.subTest(route=name):
                response = self.client.get(reverse(name, kwargs=kwargs))
                self.assertEqual(response.status_code, 200)
                self.no_navigation(response)
        # Backend-only actions cannot render a page; guard them without executing a mutation.
        for name, modal in (("address-make_default", False), ("order-detail", True), ("order-future", False)):
            request = RequestFactory().get("/", headers={"X-CV-Modal": "true"} if modal else {})
            request.resolver_match = SimpleNamespace(url_name=name)
            view = Mock()
            self.assertIsNone(customer_navigation({"request": request, "view": view}))
            view.cv_get_parent_object.assert_not_called()

    def test_customer_identity_escapes_html_on_detail_and_child(self):
        self.mine.name = '<script>alert("customer")</script> & Coffee'
        self.mine.save(update_fields=["name"])
        for name, kwargs, section in (
            ("customer-detail", {"pk": self.mine.pk}, "Details"),
            ("order-create", {"customer_pk": self.mine.pk}, "Orders"),
        ):
            response = self.client.get(reverse(name, kwargs=kwargs))
            self.navigation(response, self.mine, active=section)
            self.assertNotIn(self.mine.name, response.content.decode())

class CustomerNavigationTests(SalesTestCase):
    def test_detail_links_follow_same_customer(self):
        customer = self.granted.filter(kind="wholesale").first()
        grant_customer(self.sam, customer, actions=("view",))
        for permission in ("view_order", "view_address", "view_customersubscription"):
            self.assertTrue(self.sam.has_perm(f"sales.{permission}"))
        self.login("sam")
        detail_url = reverse("customer-detail", kwargs={"pk": customer.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        header = html.split('<div class="page-header d-print-none">', 1)[1].split('<main ', 1)[0]
        match = re.search(r'<section\b[^>]*data-customer-navigation[^>]*>(.*?)</section>', header, re.S)
        self.assertIsNotNone(match)
        navigation = match.group(1)
        self.assertEqual(navigation.count("data-customer-identity"), 1)
        self.assertIn(escape(customer.name), navigation)
        self.assertIn(f">{customer.initials}</span>", navigation)
        self.assertLess(navigation.index("data-customer-identity"), navigation.index("<nav"))
        self.assertLess(header.index("</section>"), header.index('class="row g-2 align-items-center"'))
        self.assertIn('aria-label="Customer sections"', navigation)
        self.assertIn("flex-wrap", navigation)
        links = re.findall(r'<a\b[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', navigation)
        expected = [
            (detail_url, "Details"),
            (reverse("order-list", kwargs={"customer_pk": customer.pk}), "Orders"),
            (reverse("address-list", kwargs={"customer_pk": customer.pk}), "Addresses"),
            (reverse("subscription-list", kwargs={"customer_pk": customer.pk}), "Subscriptions"),
        ]
        self.assertEqual([(unescape(url), title) for url, title in links], expected)
        self.assertEqual(navigation.count('aria-current="page"'), 1)
        self.assertRegex(navigation, r'<a[^>]*href="' + re.escape(detail_url) + r'"[^>]*aria-current="page"[^>]*>Details</a>')
        for url, title in links:
            with self.subTest(section=title):
                destination = self.client.get(unescape(url))
                self.assertEqual(destination.status_code, 200)
                view = destination.context["view"]
                reached = view.object if title == "Details" else view.cv_get_parent_object()
                self.assertEqual(reached.pk, customer.pk)
        document_title = re.search(r"<title>(.*?)</title>", html, re.S).group(1)
        self.assertIn(escape(customer.name), document_title)
        self.assertIn(f">{customer.initials}<", document_title)
        self.assertRegex(header, r'class="page-title"[^>]*>Details</h2>')
        for preserved in ("Price tier", customer.get_price_tier_display(), "Payment terms", "Wholesale", "Show code"):
            self.assertIn(preserved, html)

    def test_detail_replaces_section_actions_and_preserves_other_actions(self):
        from sales.views.customers import CustomerDetailView, cv_customer

        self.assertEqual(CustomerDetailView.cv_context_actions, ["home", "update", "delete"])
        self.assertEqual(CustomerDetailView.cv_context_actions_inline, ["update"])
        self.assertTrue({"orders", "addresses", "subscriptions"} <= {button.key for button in cv_customer.context_buttons})
        self.login("alex")
        customer = self.granted.filter(kind="wholesale").first()
        response = self.client.get(reverse("customer-detail", kwargs={"pk": customer.pk}))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        header = html.split('<div class="page-header d-print-none">', 1)[1].split('<main ', 1)[0]
        actions = header.split('class="btn-list"', 1)[1]
        for name in ("order-list", "address-list", "subscription-list"):
            url = reverse(name, kwargs={"customer_pk": customer.pk})
            self.assertNotIn(url, actions)
            self.assertEqual(header.count(f'href="{url}"'), 1)
        for name in ("customer-update", "customer-delete"):
            self.assertIn(reverse(name, kwargs={"pk": customer.pk}), actions)
        self.assertIn(reverse("customer-list"), actions)
        self.assertIn("Show code", actions)
        for preserved in ("Price tier", "Payment terms", "Wholesale", customer.get_price_tier_display()):
            self.assertIn(preserved, html)
