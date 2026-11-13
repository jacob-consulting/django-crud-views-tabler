"""Integration checks for the private customer section navigation experiment."""

import re
from copy import deepcopy
from html import escape, unescape
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.conf import settings
from django.test import RequestFactory, override_settings
from django.template import Context, Template
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from catalog.models import Subscription
from config.templatetags.acme_nav import customer_navigation
from sales.models import Address, Customer, CustomerSubscription, OrderState
from sales.permissions import can_on_customer, grant_customer
from .test_customers import SalesTestCase
from .test_orders import OrderTestCase

from crud_views.lib.view.buttons import ChildContextButton, ParentContextButton, SiblingContextButton
from crud_views.lib.view.context import ViewContext


class ContextButtonContractTests(OrderTestCase):
    """Characterize the pinned candidate on real reached views, without changing registration."""

    item = '<a data-candidate href="{{ cv_url }}">{{ cv_action_label }}</a>'

    def candidate(self, response, button):
        view = response.context["view"]
        data = button.get_context(ViewContext(view=view, object=getattr(view, "object", None)))
        rendered = Template("{% load crud_views %}{% cv_render_context_action candidate %}").render(
            Context({"view": view, "request": view.request, "candidate": data})
        ) if data["cv_access"] else ""
        return data, rendered

    def test_sibling_candidate_does_not_replace_customer_read_check(self):
        user = get_user_model().objects.create_user(username="button-change-only")
        user.user_permissions.add(*Permission.objects.filter(
            content_type__app_label="sales", codename__in=("add_address", "view_order")))
        grant_customer(user, self.mine, actions=("change",))
        self.client.force_login(user)
        response = self.client.get(reverse("address-create", kwargs={"customer_pk": self.mine.pk}))
        self.assertEqual(response.status_code, 200)
        data, rendered = self.candidate(response, SiblingContextButton(
            key="orders", sibling_name="order", template_code=self.item))
        denied = self.client.get(data["cv_url"])
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(customer_navigation(response.context)["links"], [])
        parent, parent_html = self.candidate(response, ParentContextButton(
            key="customer", key_target="detail", template_code=self.item))
        self.assertFalse(parent["cv_access"])
        self.assertEqual(parent_html, "")
        # The candidate checks child permission only; the real destination also requires customer read.
        self.assertTrue(data["cv_access"])
        self.assertIn(f'href="{data["cv_url"]}"', rendered)

    def test_per_button_templates_flow_through_real_action_container(self):
        self.login("sam")
        response = self.client.get(reverse("customer-detail", kwargs={"pk": self.mine.pk}))
        view = response.context["view"]
        templates = deepcopy(settings.TEMPLATES)
        templates[0]["APP_DIRS"] = False
        templates[0]["OPTIONS"]["loaders"] = [
            ("django.template.loaders.locmem.Loader", {"candidate-item.html": self.item}),
            "django.template.loaders.filesystem.Loader", "django.template.loaders.app_directories.Loader",
        ]
        with override_settings(TEMPLATES=templates):
            for override in ({"template": "candidate-item.html"}, {"template_code": self.item}):
                button = ChildContextButton(key="candidate", child_name="order", **override)
                with patch.object(view, "cv_context_buttons", [button]), patch.object(
                    view, "cv_context_actions", ["candidate"]
                ):
                    group = view.cv_get_context_action_group(view.object)
                    self.assertEqual(len(group.inline), 1)
                    self.assertEqual(group.menu, [])
                    html = Template("{% load crud_views %}{% cv_context_actions object %}").render(
                        Context({"view": view, "request": view.request, "object": view.object}))
                    self.assertEqual(html.count("data-candidate"), 1)
                    self.assertIn(reverse("order-list", kwargs={"customer_pk": self.mine.pk}), html)

    def test_empty_collection_candidate_stays_reachable(self):
        customer = Customer.objects.create(name="Empty button customer", kind="consumer")
        grant_customer(self.sam, customer, actions=("view",))
        self.login("sam")
        response = self.client.get(reverse("customer-detail", kwargs={"pk": customer.pk}))
        for child in ("order", "address", "subscription"):
            data, rendered = self.candidate(response, ChildContextButton(
                key=child, child_name=child, template_code=self.item))
            self.assertTrue(data["cv_access"])
            self.assertIn(data["cv_url"], rendered)
            destination = self.client.get(data["cv_url"])
            self.assertEqual(destination.status_code, 200)
            self.assertEqual(len(destination.context["table"].data), 0)

    def test_child_and_parent_candidates_match_granted_roles_and_missing_reads(self):
        cases = [(name, self.world["users"][name]) for name in ("alex", "sam", "kim")]
        permissions = ("view_order", "view_address", "view_customersubscription")
        for missing in permissions:
            user = get_user_model().objects.create_user(username=f"button-{missing}")
            user.user_permissions.add(*Permission.objects.filter(
                content_type__app_label="sales", codename__in=[p for p in permissions if p != missing]))
            grant_customer(user, self.mine, actions=("view",))
            cases.append((missing, user))
        for actor, user in cases:
            self.client.force_login(user)
            for customer in (self.mine, self.other):
                with self.subTest(actor=actor, customer=customer.pk):
                    response = self.client.get(reverse("customer-detail", kwargs={"pk": customer.pk}))
                    if response.status_code == 403:
                        self.assertNotContains(response, "data-customer-navigation", status_code=403)
                        continue
                    self.assertEqual(response.status_code, 200)
                    links = {link["url"] for link in customer_navigation(response.context)["links"]}
                    for child in ("order", "address", "subscription"):
                        data, rendered = self.candidate(response, ChildContextButton(
                            key=child, child_name=child, template_code=self.item))
                        self.assertEqual(data["cv_access"], data["cv_url"] in links)
                        self.assertEqual(bool(rendered), data["cv_access"])
                        destination = self.client.get(data["cv_url"])
                        self.assertEqual(destination.status_code, 200 if data["cv_access"] else 403)
                        if data["cv_access"]:
                            parent, html = self.candidate(destination, ParentContextButton(
                                key="customer", key_target="detail", template_code=self.item))
                            self.assertTrue(parent["cv_access"])
                            self.assertIn(reverse("customer-detail", kwargs={"pk": customer.pk}), html)

    def test_exact_route_activity_is_not_section_activity(self):
        self.login()
        order = self.make_order(customer=self.mine)
        for action in ("detail", "update", "workflow"):
            response = self.client.get(reverse(f"order-{action}", kwargs=self.order_kwargs(order)))
            self.assertEqual(response.status_code, 200)
            data, rendered = self.candidate(response, SiblingContextButton(
                key="orders", sibling_name="order", template_code=self.item))
            self.assertFalse(data["cv_is_active"])
            self.assertIn(data["cv_url"], rendered)
            link = next(link for link in customer_navigation(response.context)["links"] if link["title"] == "Orders")
            self.assertTrue(link["active"])


class NavigationAssertions:
    """Assertions scoped to the added body region, independent of document titles."""

    navigation_layout = "header"

    def navigation(self, response, customer, active=None, titles=None):
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        header = html.split('<div class="page-header d-print-none">', 1)[1].split('<main ', 1)[0]
        self.assertEqual(html.count("data-customer-identity"), 1)
        identity = re.search(r'<div\b[^>]*data-customer-identity[^>]*>(.*?)</div>', header, re.S)
        self.assertIsNotNone(identity)
        self.assertIn(escape(customer.name), identity.group(1))
        self.assertIn(f">{escape(customer.initials)}</span>", identity.group(1))
        self.assertLess(identity.end(), header.index('class="row g-2 align-items-center"'))
        match = re.search(r'<nav\b[^>]*data-customer-navigation[^>]*>(.*?)</nav>', html, re.S)
        body = match.group(1) if match else ""
        links = [(unescape(url), title) for url, title in
                 re.findall(r'<a\b[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', body)]
        destinations = {
            "Details": reverse("customer-detail", kwargs={"pk": customer.pk}),
            "Orders": reverse("order-list", kwargs={"customer_pk": customer.pk}),
            "Addresses": reverse("address-list", kwargs={"customer_pk": customer.pk}),
            "Subscriptions": reverse("subscription-list", kwargs={"customer_pk": customer.pk}),
        }
        titles = list(destinations) if titles is None else titles
        self.assertEqual(html.count("data-customer-navigation"), int(bool(titles)))
        self.assertEqual(links, [(destinations[title], title) for title in titles])
        self.assertEqual(body.count('aria-current="page"'), int(active is not None))
        if active:
            self.assertRegex(body, rf'<a[^>]*aria-current="page"[^>]*>{active}</a>')
        if titles:
            self.assertIsNotNone(match)
            self.assertIn('aria-label="Customer sections"', match.group(0))
            self.assertIn("flex-wrap", match.group(0))
            self.assertNotIn("data-customer-identity", match.group(0))
            if self.navigation_layout == "header":
                self.assertIn(match.group(0), header)
                self.assertLess(header.index("data-customer-identity"), header.index("data-customer-navigation"))
                self.assertLess(header.index("</nav>"), header.index('class="row g-2 align-items-center"'))
            else:
                self.assertNotIn("data-customer-navigation", header)
                main = html.split("<main ", 1)[1].split("</main>", 1)[0]
                card = re.search(r'<div data-customer-navigation-card class="card mb-3">\s*'
                                 r'<div class="card-header">(.*?)</div>\s*</div>', main, re.S)
                self.assertIsNotNone(card)
                self.assertIn(match.group(0), card.group(1))
                self.assertEqual(main.count("data-customer-navigation-card"), 1)
        else:
            self.assertIsNone(match)
            self.assertNotIn("data-customer-navigation-card", html)
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

class NavigationAccessTests(NavigationAssertions, OrderTestCase):
    def actor(self, name, permissions, customer=None, actions=("view",)):
        user = get_user_model().objects.create_user(username=name)
        user.user_permissions.add(*Permission.objects.filter(content_type__app_label="sales", codename__in=permissions))
        if customer is not None:
            grant_customer(user, customer, actions=actions)
        self.client.force_login(user)
        return user

    def test_seeded_roles_and_ungranted_customer(self):
        for username in ("alex", "sam", "kim"):
            self.login(username)
            for customer in (self.mine, self.other):
                with self.subTest(actor=username, customer=customer.pk):
                    response = self.client.get(reverse("customer-detail", kwargs={"pk": customer.pk}))
                    if username == "sam" and customer == self.other:
                        self.assertEqual(response.status_code, 403)
                        self.no_navigation(response)
                        self.assertNotIn(escape(customer.name), response.content.decode())
                        for name in ("order-list", "address-list", "subscription-list"):
                            denied = self.client.get(reverse(name, kwargs={"customer_pk": customer.pk}))
                            self.assertEqual(denied.status_code, 403)
                            self.no_navigation(denied)
                    else:
                        for url, title in self.navigation(response, customer, active="Details"):
                            self.navigation(self.client.get(url), customer, active=title)

    def test_each_missing_child_read_permission_hides_only_that_section(self):
        sections = [("view_order", "Orders", "order-list"),
                    ("view_address", "Addresses", "address-list"),
                    ("view_customersubscription", "Subscriptions", "subscription-list")]
        for missing, hidden, route in sections:
            with self.subTest(missing=missing):
                user = self.actor(missing, [perm for perm, _, _ in sections if perm != missing], self.mine)
                self.assertFalse(user.has_perm(f"sales.{missing}"))
                response = self.client.get(reverse("customer-detail", kwargs={"pk": self.mine.pk}))
                visible = [title for title in ("Details", "Orders", "Addresses", "Subscriptions") if title != hidden]
                for url, title in self.navigation(response, self.mine, active="Details", titles=visible):
                    self.navigation(self.client.get(url), self.mine, active=title, titles=visible)
                denied = self.client.get(reverse(route, kwargs={"customer_pk": self.mine.pk}))
                self.assertEqual(denied.status_code, 403)
                self.no_navigation(denied)

    def test_empty_authorized_customer_keeps_all_collection_links(self):
        customer = Customer.objects.create(name="Empty navigation customer", kind="consumer")
        self.actor("empty-reader", ["view_order", "view_address", "view_customersubscription"], customer)
        response = self.client.get(reverse("customer-detail", kwargs={"pk": customer.pk}))
        for url, title in self.navigation(response, customer, active="Details"):
            destination = self.client.get(url)
            self.navigation(destination, customer, active=title)
            if title != "Details":
                self.assertEqual(len(destination.context["table"].data), 0)

    def test_change_only_forms_keep_identity_without_empty_navigation(self):
        actor = self.actor("change-only", ["add_address", "change_address"], self.mine, actions=("change",))
        self.assertTrue(can_on_customer(actor, "change", self.mine))
        self.assertFalse(can_on_customer(actor, "view", self.mine))
        for name, kwargs in (
            ("address-create", {"customer_pk": self.mine.pk}),
            ("address-update", {"customer_pk": self.mine.pk, "pk": self.mine.addresses.first().pk}),
        ):
            response = self.client.get(reverse(name, kwargs=kwargs))
            self.navigation(response, self.mine, titles=[])
            self.assertNotContains(response, 'aria-label="Customer sections"')
        for name, kwargs in [("customer-detail", {"pk": self.mine.pk})] + [
            (name, {"customer_pk": self.mine.pk}) for name in ("order-list", "address-list", "subscription-list")
        ]:
            denied = self.client.get(reverse(name, kwargs=kwargs))
            self.assertEqual(denied.status_code, 403)
            self.no_navigation(denied)

    def test_inaccessible_owning_section_is_not_fabricated(self):
        self.actor("address-writer", ["add_address"], self.mine, actions=("view", "change"))
        response = self.client.get(reverse("address-create", kwargs={"customer_pk": self.mine.pk}))
        self.navigation(response, self.mine, titles=["Details"])
        self.assertEqual(self.client.get(reverse("address-list", kwargs={"customer_pk": self.mine.pk})).status_code, 403)

    def test_mismatched_child_and_ungranted_customer_do_not_leak(self):
        self.login("sam")
        order = self.make_order(customer=self.other)
        subscription = CustomerSubscription.objects.create(
            customer=self.other, product=Subscription.objects.first(), next_delivery=timezone.localdate()
        )
        cases = [("order-detail", order), ("order-update", order), ("order-workflow", order),
                 ("address-detail", self.other.addresses.first()), ("subscription-update", subscription)]
        for name, obj in cases:
            for customer, status in ((self.other, 403), (self.mine, 404)):
                with self.subTest(route=name, status=status):
                    response = self.client.get(reverse(name, kwargs={"customer_pk": customer.pk, "pk": obj.pk}))
                    self.assertEqual(response.status_code, status)
                    self.no_navigation(response)
                    self.assertNotIn(escape(self.other.name), response.content.decode())
                    self.assertNotIn(escape(str(obj)), response.content.decode())


class NavigationPreservationTests(NavigationAssertions, OrderTestCase):
    def test_filtered_paginated_orders_keep_rows_actions_and_section_switching(self):
        self.login("sam")
        for _ in range(25):
            self.make_order(customer=self.mine)
        foreign = self.make_order(customer=self.other)
        self.make_order(customer=self.mine, state=OrderState.SHIPPED)
        url = reverse("order-list", kwargs={"customer_pk": self.mine.pk})
        response = self.client.get(url, {"state": "draft", "page": 2})
        links = dict((title, url) for url, title in self.navigation(response, self.mine, active="Orders"))
        table = response.context["table"]
        self.assertEqual(table.page.number, 2)
        self.assertEqual(len(table.page.object_list), 10)
        self.assertTrue(table.page.has_previous())
        records = [row.record for row in table.page.object_list]
        self.assertTrue(all(row.customer_id == self.mine.pk and row.state == "draft" for row in records))
        self.assertNotIn(foreign.pk, [row.pk for row in table.data])
        self.assertTrue(all(row.customer_id == self.mine.pk and row.state == "draft" for row in table.data))
        for record in records:
            for name in ("order-detail", "order-update"):
                self.assertContains(response, reverse(name, kwargs=self.order_kwargs(record)))
        self.assertEqual(response.context["filter"].form.cleaned_data["state"], "draft")
        self.assertNotIn("?", links["Addresses"])
        self.navigation(self.client.get(links["Addresses"]), self.mine, active="Addresses")

    def test_child_create_update_validation_save_and_redirect(self):
        self.login("sam")
        create_url = reverse("address-create", kwargs={"customer_pk": self.mine.pk})
        invalid = self.client.post(create_url, {})
        self.navigation(invalid, self.mine, active="Addresses")
        self.assertTrue(invalid.context["form"].errors)
        data = {"label": "Navigation depot", "street": "Hafenweg 3", "zip_code": "20457",
                "city": "Hamburg", "country": "DE"}
        response = self.client.post(create_url, data)
        address = Address.objects.get(label=data["label"])
        self.assertEqual(address.customer_id, self.mine.pk)
        self.assertEqual(response.status_code, 302)
        self.navigation(self.client.get(response.url), self.mine, active="Addresses")
        update_url = reverse("address-update", kwargs={"customer_pk": self.mine.pk, "pk": address.pk})
        invalid = self.client.post(update_url, {**data, "street": ""})
        self.navigation(invalid, self.mine, active="Addresses")
        self.assertIn("street", invalid.context["form"].errors)
        response = self.client.post(update_url, {**data, "label": "Updated navigation depot"})
        self.assertEqual(response.status_code, 302)
        address.refresh_from_db()
        self.assertEqual(address.label, "Updated navigation depot")
        self.navigation(self.client.get(response.url), self.mine, active="Addresses")

    def test_editable_order_update_and_locked_order_denial(self):
        self.login("sam")
        order = self.make_order(customer=self.mine)
        self.assertTrue(order.is_editable)
        prefix = f"lines-{order.pk}-0"
        line = order.lines.get()
        data = {**self.order_post(self.mine, [], notes="Navigation edit"),
                **self.lines_post(prefix, [{"id": line.pk, "product": self.huila.pk,
                                           "quantity": "3", "grind": "whole", "bag_size": "1kg"}], initial=1)}
        url = reverse("order-update", kwargs=self.order_kwargs(order))
        invalid = self.client.post(url, {**data, f"{prefix}-0-quantity": "0"})
        self.navigation(invalid, self.mine, active="Orders")
        self.assertContains(invalid, "Ensure this value is greater than or equal to 1.")
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("order-detail", kwargs=self.order_kwargs(order)))
        order.refresh_from_db()
        self.assertEqual(order.notes, "Navigation edit")
        self.assertEqual(order.lines.get().quantity, 3)
        locked = self.make_order(customer=self.mine, state=OrderState.SHIPPED)
        self.assertFalse(locked.is_editable)
        for method in (self.client.get, self.client.post):
            denied = method(reverse("order-update", kwargs=self.order_kwargs(locked)), data)
            self.assertEqual(denied.status_code, 403)
            self.no_navigation(denied)

    def test_authorized_and_denied_workflow_transitions(self):
        self.login("sam")
        order = self.make_order(customer=self.mine)
        self.assertIn("wf_confirm", [t.name for t in order.get_available_user_state_transitions(self.sam)])
        order.workflow_check_transition("wf_confirm", user=self.sam)
        url = reverse("order-workflow", kwargs=self.order_kwargs(order))
        self.navigation(self.client.get(url), self.mine, active="Orders")
        response = self.client.post(url, {"transition": "wf_confirm"})
        self.assertRedirects(response, reverse("order-detail", kwargs=self.order_kwargs(order)))
        order.refresh_from_db()
        self.assertEqual(order.state, OrderState.CONFIRMED)
        self.login("kim")
        kim = self.world["users"]["kim"]
        self.assertNotIn("wf_cancel", [t.name for t in order.get_available_user_state_transitions(kim)])
        self.navigation(self.client.post(url, {"transition": "wf_cancel", "comment": "Denied"}),
                        self.mine, active="Orders")
        order.refresh_from_db()
        self.assertEqual(order.state, OrderState.CONFIRMED)
        self.assertIn("wf_roast", [t.name for t in order.get_available_user_state_transitions(kim)])
        order.workflow_check_transition("wf_roast", user=kim)
        self.assertEqual(self.client.post(url, {"transition": "wf_roast"}).status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.state, OrderState.ROASTED)
        draft = self.make_order(customer=self.mine)
        self.assertFalse(draft.workflow_has_any_possible_transition(kim))
        denied = self.client.get(reverse("order-workflow", kwargs=self.order_kwargs(draft)))
        self.assertEqual(denied.status_code, 403)
        self.no_navigation(denied)


class CustomerNavigationTests(NavigationAssertions, SalesTestCase):
    def test_identity_and_sections_are_independent(self):
        self.login("sam")
        customer = self.granted.first()
        response = self.client.get(reverse("customer-detail", kwargs={"pk": customer.pk}))
        self.navigation(response, customer, active="Details")
        self.assertTemplateUsed(response, "project/customer_navigation/identity.html")
        self.assertTemplateUsed(response, "project/customer_navigation/sections.html")

    def test_partials_render_data_independently_and_escape_identity(self):
        customer = self.granted.first()
        customer.name = '<script>alert("identity")</script> & Coffee'
        data = {"customer_nav": {"customer": customer, "links": [
            {"title": "Details", "url": "/customer/1/detail/", "active": True}]}}
        identity = render_to_string("project/customer_navigation/identity.html", data)
        sections = render_to_string("project/customer_navigation/sections.html", data)
        self.assertIn(escape(customer.name), identity)
        self.assertNotIn(customer.name, identity)
        self.assertNotIn("data-customer-navigation", identity)
        self.assertNotIn("data-customer-identity", sections)
        self.assertIn('aria-current="page"', sections)
        self.assertIn('href="/customer/1/detail/"', sections)
        data["customer_nav"]["links"] = []
        self.assertIn("data-customer-identity", render_to_string("project/customer_navigation/identity.html", data))
        self.assertEqual(render_to_string("project/customer_navigation/sections.html", data).strip(), "")

    def test_page_resolves_navigation_once(self):
        self.login("sam")
        # Patch the tag node's resolved callable, not a disconnected module alias.
        from django.template.library import SimpleNode
        original = SimpleNode.render
        calls = []

        def observe(node, context):
            if node.func is customer_navigation:
                calls.append(node)
            return original(node, context)

        with patch.object(SimpleNode, "render", observe):
            response = self.client.get(reverse("customer-detail", kwargs={"pk": self.granted.first().pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(calls), 1)

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
        links = self.navigation(response, customer, active="Details")
        match = re.search(r'<nav\b[^>]*data-customer-navigation[^>]*>(.*?)</nav>', header, re.S)
        self.assertIsNotNone(match)
        navigation = match.group(0)
        self.assertIn('aria-label="Customer sections"', navigation)
        self.assertIn("flex-wrap", navigation)
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
