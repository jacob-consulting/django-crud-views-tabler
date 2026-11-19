from datetime import date, timedelta
from html import escape
from html.parser import HTMLParser

from catalog.models import Subscription
from django.contrib.messages import get_messages
from django.urls import reverse

from sales.models import CustomerSubscription, Order, OrderState
from sales.services import run_subscriptions

from .test_customers import SalesTestCase

TODAY = date(2026, 11, 4)


class LabelText(HTMLParser):
    """Collect the text of headings or breadcrumb items, excluding their icons."""

    def __init__(self, markup, css_class):
        super().__init__()
        self.labels = []
        self.stack = []
        self.css_class = css_class
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        if self.css_class in dict(attrs).get("class", "").split():
            self.labels.append("")
        if tag not in {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }:
            self.stack.append((tag, self.css_class in dict(attrs).get("class", "").split()))

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()

    def handle_data(self, data):
        if any(selected for _, selected in self.stack) and not any(tag == "svg" for tag, _ in self.stack):
            self.labels[-1] += data


def label_text(response, css_class):
    return [" ".join(text.split()) for text in LabelText(response.content.decode(), css_class).labels]


class SubscriptionTestCase(SalesTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        CustomerSubscription.objects.all().delete()  # the seeded ones would muddy the counts
        cls.weekly = Subscription.objects.filter(interval="weekly").first()
        cls.monthly = Subscription.objects.filter(interval="monthly").first()
        cls.mine = cls.granted.first()

    def subscribe(self, customer, product=None, days=0, active=True):
        return CustomerSubscription.objects.create(
            customer=customer,
            product=product or self.weekly,
            started_on=TODAY - timedelta(days=60),
            next_delivery=TODAY + timedelta(days=days),
            is_active=active,
        )


class RunSubscriptionsTests(SubscriptionTestCase):
    def test_advance_by_interval(self):
        for interval, days in (("weekly", 7), ("biweekly", 14), ("monthly", 30)):
            product = Subscription.objects.filter(interval=interval).first()
            sub = self.subscribe(self.mine, product)
            sub.advance()
            self.assertEqual(sub.next_delivery, TODAY + timedelta(days=days), interval)

    def test_run_creates_draft_orders_for_due(self):
        due_a = self.subscribe(self.mine, days=-3)
        due_b = self.subscribe(self.other, self.monthly, days=0)
        future = self.subscribe(self.mine, days=5)
        paused = self.subscribe(self.other, days=-1, active=False)
        before = Order.objects.count()
        orders = run_subscriptions(TODAY, self.world["users"]["alex"])
        self.assertEqual(len(orders), 2)
        self.assertEqual(Order.objects.count(), before + 2)
        for order, sub in zip(orders, (due_a, due_b), strict=True):
            self.assertEqual(order.state, OrderState.DRAFT)
            self.assertEqual(order.customer, sub.customer)
            (line,) = order.lines.all()
            self.assertEqual(line.product_id, sub.product_id)
            self.assertEqual(line.quantity, sub.product.bags_per_delivery)
        for sub in (due_a, due_b, future, paused):
            sub.refresh_from_db()
        self.assertGreater(due_a.next_delivery, TODAY)
        self.assertGreater(due_b.next_delivery, TODAY)
        self.assertEqual(future.next_delivery, TODAY + timedelta(days=5))
        self.assertEqual(paused.next_delivery, TODAY - timedelta(days=1))

    def test_run_twice_creates_nothing_new(self):
        self.subscribe(self.mine, days=-20)  # weeks behind: one order, then caught up
        self.subscribe(self.other, days=0)
        alex = self.world["users"]["alex"]
        self.assertEqual(len(run_subscriptions(TODAY, alex)), 2)
        count = Order.objects.count()
        self.assertEqual(run_subscriptions(TODAY, alex), [])
        self.assertEqual(Order.objects.count(), count)


class SubscriptionViewTests(SubscriptionTestCase):
    def test_subscription_lists_use_viewset_names(self):
        self.subscribe(self.mine)
        self.login()
        # the nested list sits under the customer's header; its heading repeats the active tab, so the tab names it
        pages = (
            ("subscriptions-list", {}, ["Subscriptions"]),
            ("subscription-list", {"customer_pk": self.mine.pk}, [str(self.mine)]),
        )
        for name, kwargs, titles in pages:
            with self.subTest(name=name):
                response = self.client.get(reverse(name, kwargs=kwargs))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(label_text(response, "page-title"), titles)
                if name == "subscription-list":
                    self.assertRegex(
                        response.content.decode(), r'aria-current="true">(?:<svg.*?</svg>)?\s*Subscriptions</a>'
                    )
                breadcrumbs = label_text(response, "breadcrumb-item")
                self.assertIn("Subscriptions", breadcrumbs)
                self.assertNotIn("Customer subscriptions", breadcrumbs)

    def test_subscription_form_headers_use_viewset_name(self):
        sub = self.subscribe(self.mine)
        self.login()
        for action in ("create", "update", "delete"):
            with self.subTest(action=action):
                kwargs = {"customer_pk": self.mine.pk}
                if action != "create":
                    kwargs["pk"] = sub.pk
                response = self.client.get(reverse(f"subscription-{action}", kwargs=kwargs))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    label_text(response, "page-title"), [str(self.mine), "Subscription"]
                )  # owner h1, view title
                breadcrumbs = label_text(response, "breadcrumb-item")
                self.assertIn("Subscriptions", breadcrumbs)
                self.assertNotIn("Customer subscriptions", breadcrumbs)

    def test_subscription_delete_modal_uses_viewset_name(self):
        sub = self.subscribe(self.mine)
        self.login()
        url = reverse("subscription-delete", kwargs={"customer_pk": self.mine.pk, "pk": sub.pk})
        response = self.client.get(url, headers={"X-CV-Modal": "true"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(label_text(response, "modal-title"), ["Subscription"])

    def test_run_subscription_header_keeps_custom_label(self):
        self.login()
        response = self.client.get(reverse("subscriptions-run"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(label_text(response, "page-title"), ["Run subscriptions"])

    def test_run_view_flashes_count(self):
        self.subscribe(self.mine, days=-1)
        self.subscribe(self.other, days=0)
        self.login()
        self.assertEqual(self.client.get(reverse("subscriptions-run")).status_code, 200)
        response = self.client.post(reverse("subscriptions-run"), {"due": TODAY.isoformat()})
        self.assertRedirects(response, reverse("subscriptions-list"))
        self.assertEqual([str(m) for m in get_messages(response.wsgi_request)], ["Created 2 draft orders"])
        self.assertEqual(Order.objects.filter(notes__startswith="Subscription delivery").count(), 2)
        again = self.client.post(reverse("subscriptions-run"), {"due": TODAY.isoformat()})
        self.assertEqual([str(m) for m in get_messages(again.wsgi_request)][-1], "Created 0 draft orders")

    def test_run_is_for_alex_only(self):
        sub = self.subscribe(self.mine, days=-1)
        url = reverse("subscriptions-run")
        for username in ("sam", "kim"):
            self.login(username)
            self.assertEqual(self.client.get(url).status_code, 403, username)
            self.assertEqual(self.client.post(url, {"due": TODAY.isoformat()}).status_code, 403, username)
            html = self.client.get(reverse("subscriptions-list")).content.decode()
            self.assertNotIn(f'href="{url}"', html, username)  # the button is not a live link
        self.assertFalse(Order.objects.filter(notes__startswith="Subscription delivery").exists())
        sub.refresh_from_db()
        self.assertEqual(sub.next_delivery, TODAY - timedelta(days=1))

    def test_sam_sees_only_own_subscriptions(self):
        mine = self.subscribe(self.mine, days=2)
        theirs = self.subscribe(self.other, days=2)
        self.login("sam")
        response = self.client.get(reverse("subscriptions-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, escape(self.mine.name))
        self.assertNotContains(response, escape(self.other.name))
        self.assertEqual(list(response.context["table"].data.data), [mine])
        # the nested list of someone else's customer: 403; his own: 200
        self.assertEqual(
            self.client.get(reverse("subscription-list", kwargs={"customer_pk": self.other.pk})).status_code, 403
        )
        self.assertEqual(
            self.client.get(reverse("subscription-list", kwargs={"customer_pk": self.mine.pk})).status_code, 200
        )
        kwargs = {"customer_pk": self.other.pk, "pk": theirs.pk}
        self.assertEqual(self.client.get(reverse("subscription-update", kwargs=kwargs)).status_code, 403)
        cross = {"customer_pk": self.mine.pk, "pk": theirs.pk}  # his customer in the URL, someone else's subscription
        self.assertEqual(self.client.get(reverse("subscription-update", kwargs=cross)).status_code, 404)

    def test_sam_manages_his_customers_subscriptions(self):
        self.login("sam")
        url = reverse("subscription-create", kwargs={"customer_pk": self.mine.pk})
        data = {"product": self.weekly.pk, "started_on": "2026-11-04", "next_delivery": "2026-11-11", "is_active": "on"}
        self.assertEqual(self.client.post(url, data).status_code, 302)
        sub = CustomerSubscription.objects.get(customer=self.mine)
        self.assertEqual(
            self.client.post(
                reverse("subscription-update", kwargs={"customer_pk": self.mine.pk, "pk": sub.pk}),
                {**data, "next_delivery": "2026-11-18"},
            ).status_code,
            302,
        )
        sub.refresh_from_db()
        self.assertEqual(sub.next_delivery, date(2026, 11, 18))
        self.assertEqual(
            self.client.get(
                reverse("subscription-delete", kwargs={"customer_pk": self.mine.pk, "pk": sub.pk})
            ).status_code,
            403,
        )
        denied = reverse("subscription-create", kwargs={"customer_pk": self.other.pk})
        self.assertEqual(self.client.post(denied, data).status_code, 403)

    def test_kim_is_view_only(self):
        sub = self.subscribe(self.other, days=2)
        self.login("kim")
        self.assertEqual(self.client.get(reverse("subscriptions-list")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("subscription-list", kwargs={"customer_pk": self.other.pk})).status_code, 200
        )
        self.assertEqual(
            self.client.get(reverse("subscription-create", kwargs={"customer_pk": self.other.pk})).status_code, 403
        )
        self.assertEqual(
            self.client.get(
                reverse("subscription-update", kwargs={"customer_pk": self.other.pk, "pk": sub.pk})
            ).status_code,
            403,
        )

    def test_nav_and_customer_link(self):
        for username in ("alex", "sam", "kim"):
            self.login(username)
            self.assertContains(
                self.client.get(reverse("dashboard:index")), reverse("subscriptions-list"), msg_prefix=username
            )


class SeedSubscriptionTests(SalesTestCase):
    def test_seed_has_mixed_subscriptions(self):
        subs = CustomerSubscription.objects.all()
        self.assertGreaterEqual(subs.filter(is_active=True).count(), 10)
        self.assertTrue(subs.filter(is_active=False).exists())
        self.assertGreater(len({s.next_delivery for s in subs}), 3)
        self.assertTrue(subs.filter(customer__in=self.granted).exists())


class SubscriptionOrderEditTests(SubscriptionTestCase):
    def test_order_from_run_subscriptions_can_be_saved_unchanged(self):
        self.subscribe(self.mine, days=-1)
        alex = self.world["users"]["alex"]
        (order,) = run_subscriptions(TODAY, alex)
        line = order.lines.get()
        self.assertIsInstance(line.product, Subscription)
        self.login()
        url = reverse("order-update", kwargs={"customer_pk": order.customer_id, "pk": order.pk})
        prefix = f"lines-{order.pk}-0"
        data = {
            "ship_to": str(order.ship_to_id or order.customer.addresses.first().pk),
            "requested_roast_date": "",
            "notes": "",
            f"{prefix}-TOTAL_FORMS": "1",
            f"{prefix}-INITIAL_FORMS": "1",
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
            f"{prefix}-0-id": str(line.pk),
            f"{prefix}-0-product": str(line.product_id),
            f"{prefix}-0-grind": line.grind,
            f"{prefix}-0-bag_size": line.bag_size,
            f"{prefix}-0-quantity": str(line.quantity),
        }
        self.assertEqual(self.client.post(url, data).status_code, 302)
        self.assertEqual(order.lines.count(), 1)
        self.assertEqual(order.lines.get().product_id, line.product_id)
