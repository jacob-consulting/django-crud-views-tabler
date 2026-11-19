import json
import re
from datetime import timedelta
from decimal import Decimal
from html import escape, unescape

import django
from catalog.models import Beans, Equipment, Origin
from crud_views_widget_typeahead.lookups import get_lookup
from crud_views_workflow.models import WorkflowInfo
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags

from sales.models import Address, Customer, Order, OrderLine, OrderState
from sales.permissions import grant_customer

from .test_customers import SalesTestCase


def page_heading(response):
    return re.search(r'<h[1-6]\b[^>]*class="page-title"[^>]*>(.*?)</h[1-6]>', response.content.decode(), re.S).group(1)


def history(order):
    return WorkflowInfo.objects.filter(
        workflow_object_pk=str(order.pk), workflow_object_content_type=ContentType.objects.get_for_model(Order)
    )


class OrderTestCase(SalesTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        origin = Origin.objects.first()
        cls.huila = Beans.objects.create(
            name="Test Huila", slug="t-huila", sku="T-1", price=Decimal("16.50"), origin=origin
        )
        cls.cerrado = Beans.objects.create(
            name="Test Cerrado", slug="t-cerrado", sku="T-2", price=Decimal("12.80"), origin=origin
        )
        cls.dripper = Equipment.objects.create(
            name="Test dripper", slug="t-dripper", sku="T-3", price=Decimal("28.00"), brand="Hario"
        )
        cls.tier_b = Customer.objects.filter(kind="wholesale", price_tier="B").first()
        cls.mine = cls.granted.first()  # one of Sam's customers

    @staticmethod
    def order_kwargs(order):
        return {"customer_pk": order.customer_id, "pk": order.pk}

    def make_order(self, customer=None, state=OrderState.DRAFT, lines=True):
        order = Order.objects.create(customer=customer or self.tier_b, state=state)
        if lines:
            OrderLine.objects.create(order=order, product=self.huila, quantity=2, grind="filter", bag_size="250g")
        return order

    @staticmethod
    def lines_post(prefix, rows, initial=0):
        data = {
            f"{prefix}-TOTAL_FORMS": str(len(rows)),
            f"{prefix}-INITIAL_FORMS": str(initial),
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
        }
        for i, row in enumerate(rows):
            data.update({f"{prefix}-{i}-{key}": value for key, value in row.items()})
        return data

    def order_post(self, customer, rows, prefix="lines-None-0", **fields):
        data = {"ship_to": str(customer.addresses.first().pk), "requested_roast_date": "", "notes": "", **fields}
        return {**data, **self.lines_post(prefix, rows)}


class OrderFormTests(OrderTestCase):
    def test_order_lines_use_compact_layout_with_product_metadata(self):
        self.login()
        order = self.make_order()
        urls = (
            reverse("order-create", kwargs={"customer_pk": self.tier_b.pk}),
            reverse("order-update", kwargs=self.order_kwargs(order)),
        )
        for url in urls:
            with self.subTest(url=url):
                html = self.client.get(url).content.decode()
                self.assertEqual(html.count('class="row cv-formset-compact-headings"'), 1)
                self.assertIn("cv-formset-row-compact", html)
                self.assertIn('<legend class="cv-tabler-section-legend">', html)
                for field in ("product", "quantity"):
                    self.assertRegex(html, rf'<label[^>]*for="id_lines-[^"]+-{field}"')
                # finding 20: upstream's QuerysetConditions disables grind and bag size unless the row's product is
                # coffee
                for field in ("grind", "bag_size"):
                    cell = re.search(
                        rf'<div[^>]*cv-data-toggle-group[^>]*>\s*<div id="div_id_lines-[^"]+-0-{field}"', html
                    )
                    self.assertIsNotNone(cell, field)
                    self.assertIn('cv-data-toggle-kind="queryset"', cell.group(0))
                    self.assertIn("cv-data-toggle-disable-only", cell.group(0))
                    values = json.loads(unescape(re.search(r'cv-data-toggle-values="([^"]*)"', cell.group(0)).group(1)))
                    self.assertIn(str(self.huila.pk), values)
                    self.assertNotIn(str(self.dripper.pk), values)
                self.assertNotIn("data-beans", html)
                self.assertNotIn("cv-queryset-condition-error", html)

    def test_invalid_order_line_keeps_compact_row_and_error(self):
        self.login()
        url = reverse("order-create", kwargs={"customer_pk": self.tier_b.pk})
        rows = [{"product": self.huila.pk, "quantity": "0"}]
        response = self.client.post(url, self.order_post(self.tier_b, rows))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("cv-formset-row-compact", html)
        if django.VERSION >= (5, 0):  # Django 5.0 adds aria-invalid to widgets with errors
            self.assertRegex(html, r'name="lines-None-0-0-quantity" value="0"[^>]*aria-invalid="true"')
        else:
            self.assertRegex(html, r'name="lines-None-0-0-quantity" value="0"')
        self.assertIn("Ensure this value is greater than or equal to 1.", html)

    def test_nested_create_heading_names_customer(self):
        self.tier_b.name = "Roast <script>alert(1)</script> & Co"
        self.tier_b.save(update_fields=["name"])
        self.login()
        response = self.client.get(reverse("order-create", kwargs={"customer_pk": self.tier_b.pk}))
        self.assertEqual(response.status_code, 200)
        heading = page_heading(response)
        self.assertEqual(
            " ".join(unescape(strip_tags(heading)).split()), "New order for Roast <script>alert(1)</script> & Co"
        )
        self.assertIn(escape(self.tier_b.name), heading)
        self.assertNotIn("<script>", heading)

    def test_invalid_nested_create_keeps_customer_heading(self):
        self.tier_b.name = "Roast <script>alert(1)</script> & Co"
        self.tier_b.save(update_fields=["name"])
        self.login()
        response = self.client.post(
            reverse("order-create", kwargs={"customer_pk": self.tier_b.pk}),
            self.order_post(self.tier_b, [], requested_roast_date="not-a-date"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("requested_roast_date", response.context["form"].errors)
        heading = page_heading(response)
        self.assertEqual(
            " ".join(unescape(strip_tags(heading)).split()), "New order for Roast <script>alert(1)</script> & Co"
        )
        self.assertIn(escape(self.tier_b.name), heading)
        self.assertNotIn("<script>", heading)

    def test_line_formset_creates_lines_and_totals(self):
        self.login()
        url = reverse("order-create", kwargs={"customer_pk": self.tier_b.pk})
        self.assertContains(self.client.get(url), 'name="lines-None-0-TOTAL_FORMS"')
        rows = [
            {"product": self.huila.pk, "grind": "filter", "bag_size": "250g", "quantity": "2"},
            {"product": self.cerrado.pk, "grind": "espresso", "bag_size": "1kg", "quantity": "3"},
            {"product": self.dripper.pk, "grind": "", "bag_size": "", "quantity": "1"},
        ]
        response = self.client.post(url, self.order_post(self.tier_b, rows))
        self.assertEqual(response.status_code, 302)
        order = Order.objects.latest("number")
        self.assertRedirects(response, reverse("order-detail", kwargs=self.order_kwargs(order)))
        self.assertEqual(order.customer, self.tier_b)
        self.assertEqual(order.state, OrderState.DRAFT)
        self.assertEqual(order.lines.count(), 3)
        # 2 x 16.50 + 3 x 12.80 + 1 x 28.00 = 99.40; tier B is -12 %: 11.928 -> 11.93
        self.assertEqual(order.subtotal, Decimal("99.40"))
        self.assertEqual(order.discount_amount, Decimal("11.93"))
        self.assertEqual(order.total, Decimal("87.47"))
        self.assertEqual(order.total, order.subtotal - order.discount_amount)

    def test_non_beans_line_clears_grind_and_bag(self):
        self.login()
        url = reverse("order-create", kwargs={"customer_pk": self.tier_b.pk})
        rows = [{"product": self.dripper.pk, "grind": "espresso", "bag_size": "1kg", "quantity": "1"}]
        self.assertEqual(self.client.post(url, self.order_post(self.tier_b, rows)).status_code, 302)
        line = Order.objects.latest("number").lines.get()
        self.assertEqual((line.grind, line.bag_size), ("", ""))
        self.assertEqual(line.unit_price, Decimal("28.00"))

    def test_line_form_clears_grind_and_bag_for_non_beans(self):
        # the form clears them itself (upstream's conditional group), not only OrderLine.save()
        from sales.forms import OrderLineForm

        form = OrderLineForm(
            None, data={"product": self.dripper.pk, "grind": "espresso", "bag_size": "1kg", "quantity": "1"}
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual((form.cleaned_data["grind"], form.cleaned_data["bag_size"]), ("", ""))
        form = OrderLineForm(
            None, data={"product": self.huila.pk, "grind": "espresso", "bag_size": "1kg", "quantity": "1"}
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual((form.cleaned_data["grind"], form.cleaned_data["bag_size"]), ("espresso", "1kg"))

    def test_update_edits_lines(self):
        self.login()
        order = self.make_order()
        line = order.lines.get()
        prefix = f"lines-{order.pk}-0"
        url = reverse("order-update", kwargs=self.order_kwargs(order))
        self.assertContains(self.client.get(url), f'name="{prefix}-TOTAL_FORMS"')
        rows = [
            {"id": line.pk, "product": self.huila.pk, "grind": "whole", "bag_size": "1kg", "quantity": "5"},
            {"product": self.dripper.pk, "quantity": "1"},
        ]
        data = {**self.order_post(order.customer, [], notes="Ring twice."), **self.lines_post(prefix, rows, initial=1)}
        self.assertEqual(self.client.post(url, data).status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.notes, "Ring twice.")
        self.assertEqual(sorted(order.lines.values_list("quantity", flat=True)), [1, 5])

    def test_confirmed_order_cannot_be_emptied(self):
        self.login()
        order = self.make_order(state=OrderState.CONFIRMED)
        line = order.lines.get()
        prefix = f"lines-{order.pk}-0"
        url = reverse("order-update", kwargs=self.order_kwargs(order))
        rows = [{"id": line.pk, "product": self.huila.pk, "quantity": "2", "DELETE": "on"}]
        data = {**self.order_post(order.customer, []), **self.lines_post(prefix, rows, initial=1)}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A confirmed order needs at least one line item.")
        self.assertEqual(order.lines.count(), 1)
        # a draft may be emptied
        draft = self.make_order()
        rows = [{"id": draft.lines.get().pk, "product": self.huila.pk, "quantity": "2", "DELETE": "on"}]
        prefix = f"lines-{draft.pk}-0"
        data = {**self.order_post(draft.customer, []), **self.lines_post(prefix, rows, initial=1)}
        self.assertEqual(
            self.client.post(reverse("order-update", kwargs=self.order_kwargs(draft)), data).status_code, 302
        )

    def test_ship_to_is_limited_to_the_customers_addresses(self):
        # Sam holds view_address model-wide: the form must not offer (or accept) other customers' addresses
        self.login("sam")
        url = reverse("order-create", kwargs={"customer_pk": self.mine.pk})
        form = self.client.get(url).context["form"]
        self.assertEqual(set(form.fields["ship_to"].queryset), set(self.mine.addresses.all()))
        foreign = Address.objects.exclude(customer=self.mine).first()
        rows = [{"product": self.huila.pk, "quantity": "1"}]
        response = self.client.post(url, self.order_post(self.mine, rows, ship_to=str(foreign.pk)))
        self.assertEqual(response.status_code, 200)
        self.assertIn("ship_to", response.context["form"].errors)

    def test_create_form_uses_the_datepicker(self):
        self.login()
        html = self.client.get(reverse("order-create", kwargs={"customer_pk": self.tier_b.pk})).content.decode()
        self.assertRegex(
            html,
            r'name="requested_roast_date"[^>]*xdsoft-datetime-config|xdsoft-datetime-config[^>]*name="requested_roast_date"',
        )


class OrderWorkflowTests(OrderTestCase):
    def workflow(self, order, transition, comment=""):
        url = reverse("order-workflow", kwargs=self.order_kwargs(order))
        return self.client.post(url, {"transition": transition, "comment": comment})

    def test_confirm_without_lines_is_refused(self):
        self.login()
        order = self.make_order(lines=False)
        response = self.workflow(order, "wf_confirm")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Add at least one line item before confirming the order.")
        order.refresh_from_db()
        self.assertEqual(order.state, OrderState.DRAFT)
        self.assertFalse(history(order).exists())

    def test_workflow_happy_path(self):
        self.login()
        order = self.make_order()
        for transition, state in (
            ("wf_confirm", "confirmed"),
            ("wf_roast", "roasted"),
            ("wf_ship", "shipped"),
            ("wf_deliver", "delivered"),
        ):
            response = self.workflow(order, transition)
            self.assertRedirects(response, reverse("order-detail", kwargs=self.order_kwargs(order)))
            order.refresh_from_db()
            self.assertEqual(order.state, state)
        self.assertIsNotNone(order.shipped_at)
        self.assertEqual(
            list(history(order).order_by("timestamp").values_list("transition", flat=True)),
            ["wf_confirm", "wf_roast", "wf_ship", "wf_deliver"],
        )
        html = self.client.get(reverse("order-detail", kwargs=self.order_kwargs(order))).content.decode()
        self.assertIn("data-order-history", html)
        self.assertIn("Mark delivered", html)

    def test_cancel_needs_a_comment(self):
        self.login()
        order = self.make_order()
        self.assertEqual(self.workflow(order, "wf_cancel").status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.state, OrderState.DRAFT)
        self.assertEqual(self.workflow(order, "wf_cancel", "Duplicate order").status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.state, OrderState.CANCELLED)

    def test_blocked_confirm_shows_disabled_button_with_reason(self):
        self.login()
        order = self.make_order(lines=False)
        html = self.client.get(reverse("order-workflow", kwargs=self.order_kwargs(order))).content.decode()
        self.assertRegex(html, r'<button[^>]*name="transition"[^>]*value="wf_confirm"[^>]*disabled')
        self.assertIn("Add at least one line item before confirming the order.", html)

    def test_workflow_page_uses_buttons(self):
        self.login()
        html = self.client.get(reverse("order-workflow", kwargs=self.order_kwargs(self.make_order()))).content.decode()
        self.assertNotIn('type="radio"', html)
        self.assertIn('value="wf_cancel"', html)

    def test_transition_buttons_use_variant_and_icon(self):
        # upstream #362: button mode reads the transition's custom["variant"] and custom["icon"]
        self.login()
        html = self.client.get(reverse("order-workflow", kwargs=self.order_kwargs(self.make_order()))).content.decode()
        buttons = dict(re.findall(r'<button[^>]*value="(wf_\w+)"[^>]*>(.*?)</button>', html, re.S))
        tags = {name: tag for tag, name in re.findall(r'(<button[^>]*value="(wf_\w+)"[^>]*>)', html)}
        self.assertIn('class="btn btn-success', tags["wf_confirm"])
        self.assertIn("<svg", buttons["wf_confirm"])
        self.assertIn("Confirm", buttons["wf_confirm"])
        self.assertIn('class="btn btn-danger', tags["wf_cancel"])
        self.assertIn("<svg", buttons["wf_cancel"])
        self.assertIn("Cancel order", buttons["wf_cancel"])
        self.assertIn('<span aria-hidden="true">*</span>', buttons["wf_cancel"])  # comment required

    def test_model_hook_refuses_confirm_without_lines(self):
        with self.assertRaisesMessage(ValidationError, "Add at least one line item"):
            self.make_order(lines=False).workflow_check_transition("wf_confirm", user=self.sam)

    def test_detail_shows_steps_and_transition_buttons(self):
        self.login()
        order = self.make_order()
        html = self.client.get(reverse("order-detail", kwargs=self.order_kwargs(order))).content.decode()
        self.assertIn("steps steps-counter", html)
        self.assertRegex(html, r'class="step-item active"[^>]*>Draft<')
        self.assertIn('data-transition="wf_confirm"', html)
        self.assertIn(
            f'href="{reverse("order-workflow", kwargs=self.order_kwargs(order))}" data-transition="wf_cancel"', html
        )
        self.assertIn('class="badge bg-secondary-lt"', html)  # the theme's light workflow badge

    def test_shipped_order_edit_is_disabled_and_forbidden(self):
        self.login()
        order = self.make_order(state=OrderState.SHIPPED)
        html = self.client.get(reverse("order-list", kwargs={"customer_pk": order.customer_id})).content.decode()
        row = re.search(rf"<tr\b(?:(?!</tr>).)*>{order.number}</a>(?:(?!</tr>).)*</tr>", html, re.S).group(0)
        self.assertRegex(
            row,
            r'<button[^>]*cv-key="update"[^>]*data-cv-disabled="state"|<button[^>]*data-cv-disabled="state"[^>]*cv-key="update"',
        )
        for name in ("order-update", "order-delete"):
            url = reverse(name, kwargs=self.order_kwargs(order))
            self.assertEqual(self.client.get(url).status_code, 403, name)
            self.assertEqual(self.client.post(url, {"confirm": "on"}).status_code, 403, name)
        self.assertTrue(Order.objects.filter(pk=order.pk).exists())
        for state in (OrderState.DELIVERED, OrderState.CANCELLED):
            other = self.make_order(state=state)
            for name in ("order-update", "order-delete"):
                url = reverse(name, kwargs=self.order_kwargs(other))
                self.assertEqual(self.client.get(url).status_code, 403, (state, name))
                self.assertEqual(self.client.post(url, {"confirm": "on"}).status_code, 403, (state, name))
            self.assertTrue(Order.objects.filter(pk=other.pk).exists(), state)

    def test_seeded_orders_cover_every_state_with_history(self):
        self.assertEqual(set(Order.objects.values_list("state", flat=True)), set(OrderState.values))
        delivered = Order.objects.filter(state=OrderState.DELIVERED).first()
        self.assertEqual(history(delivered).count(), 4)
        self.assertIsNotNone(delivered.shipped_at)


class SeedHistoryTests(OrderTestCase):
    def test_seed_history_is_backdated(self):
        shipped = Order.objects.filter(state=OrderState.SHIPPED).first()
        steps = history(shipped).order_by("timestamp")
        self.assertLess(steps.last().timestamp, timezone.now() - timedelta(minutes=4))
        self.assertLessEqual(steps.first().timestamp, shipped.created_at + timedelta(days=1))


class OrderPageTests(OrderTestCase):
    def test_top_level_create_keeps_generic_heading(self):
        self.login()
        response = self.client.get(reverse("orders-create"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(" ".join(unescape(strip_tags(page_heading(response))).split()), "New order")

    def test_top_level_list_and_create(self):
        self.login()
        response = self.client.get(reverse("orders-list"), {"per_page": 100})
        self.assertEqual(response.status_code, 200)
        shown = {o.pk for o in response.context["table"].data}
        self.assertEqual(shown, set(Order.objects.values_list("pk", flat=True)))
        self.assertGreater(len({o.customer_id for o in response.context["table"].data}), 1)

        # sam: only the orders of customers granted to him
        self.login("sam")
        response = self.client.get(reverse("orders-list"), {"per_page": 100})
        self.assertEqual(response.status_code, 200)
        customers = {o.customer_id for o in response.context["table"].data}
        self.assertTrue(customers)
        self.assertLessEqual(customers, set(self.granted.values_list("pk", flat=True)))
        self.assertEqual(len(response.context["table"].data), Order.objects.filter(customer__in=self.granted).count())

        # "new order" picks the customer and continues in the nested editor
        html = self.client.get(reverse("orders-create")).content.decode()
        self.assertIn("data-cv-typeahead-select", html)
        response = self.client.post(
            reverse("orders-create"), {"customer": str(self.mine.pk), "requested_roast_date": ""}
        )
        order = Order.objects.latest("number")
        self.assertRedirects(response, reverse("order-update", kwargs=self.order_kwargs(order)))
        self.assertEqual((order.customer, order.state), (self.mine, OrderState.DRAFT))
        self.assertEqual(order.ship_to, self.mine.addresses.get(is_default=True))
        # ... and refuses a customer not granted to him
        response = self.client.post(reverse("orders-create"), {"customer": str(self.other.pk)})
        self.assertEqual(response.status_code, 200)
        self.assertIn("customer", response.context["form"].errors)

    def test_view_only_grant_cannot_place_orders(self):
        viewable = Customer.objects.filter(owner=None, kind="consumer").first()
        grant_customer(self.sam, viewable, actions=("view",))
        self.login("sam")
        before = Order.objects.count()
        response = self.client.post(
            reverse("orders-create"), {"customer": str(viewable.pk), "requested_roast_date": ""}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("You may not place orders for this customer.", response.context["form"].errors["customer"])
        self.assertEqual(Order.objects.count(), before)

    def test_product_delete_names_the_blocking_order_lines(self):
        self.login()
        order = self.make_order()
        response = self.client.get(reverse("product-delete", kwargs={"pk": self.huila.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["has_protected_objects"])
        # entries are {"obj": instance, "url": None} since upstream #307/#316
        labels = [str(entry["obj"]) for entry in response.context["protected_objects"]]
        self.assertTrue(labels)
        self.assertIn(str(order.lines.get()), labels)
        self.assertContains(response, escape(labels[0]))

    def test_customer_with_orders_is_protected(self):
        self.login()
        customer = self.make_order().customer
        url = reverse("customer-delete", kwargs={"pk": customer.pk})
        self.assertContains(self.client.get(url), "alert")
        self.assertEqual(self.client.post(url, {"confirm": "on"}).status_code, 200)
        self.assertTrue(Customer.objects.filter(pk=customer.pk).exists())

    def test_packing_slip_context_button(self):
        self.login()
        order = self.make_order()
        OrderLine.objects.create(order=order, product=self.dripper, quantity=1)
        slip = reverse("order-packing_slip", kwargs=self.order_kwargs(order))
        self.assertEqual(slip, f"/customer/{order.customer_id}/order/{order.pk}/packing-slip/")
        self.assertContains(self.client.get(reverse("order-detail", kwargs=self.order_kwargs(order))), f'href="{slip}')
        html = self.client.get(slip).content.decode()
        lines = html[html.index("data-packing-lines") :]
        self.assertIn("Test Huila", lines)
        self.assertIn("Test dripper", lines)
        self.assertIn("data-print", html)

    def test_duplicate_order(self):
        self.login()
        source = self.make_order(state=OrderState.DELIVERED)
        OrderLine.objects.create(order=source, product=self.dripper, quantity=3)
        url = reverse("order-duplicate", kwargs=self.order_kwargs(source))
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url, {"requested_roast_date": ""})
        copy = Order.objects.latest("number")
        self.assertNotEqual(copy.pk, source.pk)
        self.assertEqual(
            [str(message) for message in get_messages(response.wsgi_request)], [f"Created {copy} from {source}"]
        )
        destination = reverse("order-detail", kwargs=self.order_kwargs(copy))
        self.assertRedirects(response, destination, fetch_redirect_response=False)
        self.assertContains(self.client.get(destination), escape(f"Created {copy} from {source}"))
        self.assertEqual(copy.state, OrderState.DRAFT)
        self.assertEqual(copy.customer, source.customer)
        pick = lambda o: sorted(o.lines.values_list("product_id", "quantity", "grind", "bag_size"))  # noqa: E731
        self.assertEqual(pick(copy), pick(source))

    def test_order_numbers_start_at_1001(self):
        self.assertEqual(Order.objects.order_by("number").first().number, 1001)
        self.assertEqual(self.make_order().number, Order.objects.order_by("-number")[1].number + 1)


class OrderRoleTests(OrderTestCase):
    def test_sam_cannot_reach_other_customers_orders(self):
        self.login("sam")
        theirs = self.make_order(customer=self.other)
        mine = self.make_order(customer=self.mine)
        self.assertEqual(self.client.get(reverse("order-list", kwargs={"customer_pk": self.other.pk})).status_code, 403)
        for name in ("order-detail", "order-update", "order-workflow", "order-packing_slip", "order-duplicate"):
            self.assertEqual(self.client.get(reverse(name, kwargs=self.order_kwargs(theirs))).status_code, 403, name)
            # cross-parent: Sam's customer in the URL, someone else's order
            cross = {"customer_pk": self.mine.pk, "pk": theirs.pk}
            self.assertEqual(self.client.get(reverse(name, kwargs=cross)).status_code, 404, name)
        self.assertEqual(
            self.client.post(reverse("order-create", kwargs={"customer_pk": self.other.pk}), {}).status_code, 403
        )
        # POSTs are refused as well, and change nothing
        count = Order.objects.count()
        for kwargs, expected in (
            (self.order_kwargs(theirs), 403),
            ({"customer_pk": self.mine.pk, "pk": theirs.pk}, 404),
        ):
            self.assertEqual(
                self.client.post(reverse("order-workflow", kwargs=kwargs), {"transition": "wf_confirm"}).status_code,
                expected,
            )
            self.assertEqual(
                self.client.post(reverse("order-duplicate", kwargs=kwargs), {"requested_roast_date": ""}).status_code,
                expected,
            )
        theirs.refresh_from_db()
        self.assertEqual(theirs.state, OrderState.DRAFT)
        self.assertEqual(Order.objects.count(), count)
        self.assertFalse(history(theirs).exists())
        # his own customer's orders open, and he may take the steps
        self.assertEqual(self.client.get(reverse("order-detail", kwargs=self.order_kwargs(mine))).status_code, 200)
        url = reverse("order-workflow", kwargs=self.order_kwargs(mine))
        self.assertEqual(self.client.post(url, {"transition": "wf_confirm"}).status_code, 302)
        # but not delete them
        self.assertEqual(self.client.get(reverse("order-delete", kwargs=self.order_kwargs(mine))).status_code, 403)

    def test_customer_lookup_is_restricted(self):
        request = RequestFactory().get("/")
        request.user = self.sam
        lookup = get_lookup("sales.customers")
        self.assertEqual(set(lookup.get_queryset(request)), set(self.granted))
        request.user = self.world["users"]["alex"]
        self.assertEqual(lookup.get_queryset(request).count(), Customer.objects.count())

    def test_kim_only_roasts(self):
        self.login("kim")
        confirmed = self.make_order(state=OrderState.CONFIRMED)
        draft = self.make_order()
        detail = reverse("order-detail", kwargs=self.order_kwargs(confirmed))
        html = self.client.get(detail).content.decode()
        self.assertIn('data-transition="wf_roast"', html)
        self.assertNotIn('data-transition="wf_cancel"', html)
        self.assertNotIn(f'href="{reverse("order-update", kwargs=self.order_kwargs(confirmed))}', html)
        # no step to take on a draft: the workflow action is disabled, its URL refused
        self.assertEqual(self.client.get(reverse("order-workflow", kwargs=self.order_kwargs(draft))).status_code, 403)
        self.assertEqual(
            self.client.post(
                reverse("order-workflow", kwargs=self.order_kwargs(confirmed)),
                {"transition": "wf_cancel", "comment": "no"},
            ).status_code,
            200,
        )
        confirmed.refresh_from_db()
        self.assertEqual(confirmed.state, OrderState.CONFIRMED)
        response = self.client.post(
            reverse("order-workflow", kwargs=self.order_kwargs(confirmed)), {"transition": "wf_roast"}
        )
        self.assertEqual(response.status_code, 302)
        confirmed.refresh_from_db()
        self.assertEqual(confirmed.state, OrderState.ROASTED)
        # read-only otherwise
        self.assertEqual(self.client.get(reverse("orders-list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("orders-create")).status_code, 403)
        self.assertEqual(self.client.get(reverse("order-update", kwargs=self.order_kwargs(draft))).status_code, 403)
        self.assertEqual(self.client.get(reverse("order-duplicate", kwargs=self.order_kwargs(draft))).status_code, 403)

    def test_nav_has_orders_for_every_role(self):
        for username in ("alex", "sam", "kim"):
            self.login(username)
            self.assertContains(
                self.client.get(reverse("dashboard:index")), reverse("orders-list"), msg_prefix=username
            )
