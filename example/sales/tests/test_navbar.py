"""The customer's object navbar (upstream #381): identity and sections on the customer's and every nested page."""

import re
from html import unescape

from catalog.models import Subscription
from django.urls import reverse
from django.utils.html import strip_tags

from sales.models import Address, Customer, CustomerSubscription

from .test_orders import OrderTestCase
from .test_subscriptions import TODAY

SECTIONS = ("customer-detail", "order-list", "subscription-list", "address-list")
LABELS = ["Details", "Orders", "Subscriptions", "Addresses"]

# url name -> (kwargs kind, the one active section)
NESTED_PAGES = {
    "order-list": ("customer", "Orders"),
    "order-create": ("customer", "Orders"),
    "order-detail": ("order", "Orders"),
    "order-update": ("order", "Orders"),
    "order-workflow": ("order", "Orders"),
    "order-duplicate": ("order", "Orders"),
    "order-packing_slip": ("order", "Orders"),
    "address-list": ("customer", "Addresses"),
    "address-create": ("customer", "Addresses"),
    "address-detail": ("address", "Addresses"),
    "address-update": ("address", "Addresses"),
    "subscription-list": ("customer", "Subscriptions"),
    "subscription-create": ("customer", "Subscriptions"),
    "subscription-update": ("subscription", "Subscriptions"),
}


def section_urls(customer):
    return [reverse("customer-detail", kwargs={"pk": customer.pk})] + [
        reverse(name, kwargs={"customer_pk": customer.pk}) for name in SECTIONS[1:]
    ]


def navbar(response):
    """None without a bar, else {"label", "items": [(text, href, active)]}."""
    html = response.content.decode()
    nav = re.search(r'<nav aria-label="Sections for ([^"]*)">(.*?)</nav>', html, re.S)
    if nav is None:
        return None
    items = [
        (strip_tags(body).strip(), href, "aria-current" in rest)
        for href, rest, body in re.findall(
            r'<a class="nav-link[^"]*" href="([^"]+)"([^>]*)>(.*?)</a>', nav.group(2), re.S
        )
    ]
    return {"label": unescape(nav.group(1)), "items": items}


def tabs_end(html):
    """End of the section links (the breadcrumb is a <nav> too, before them)."""
    return html.index("</nav>", html.index('<nav aria-label="Sections for'))


def header(html):
    return html[html.index('class="page-header') : html.index('class="page-body')]


def active(bar):
    return [text for text, _href, is_active in bar["items"] if is_active]


class CustomerNavbarTests(OrderTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.weekly = Subscription.objects.first()

    def build(self, customer):
        """The kwargs of every endpoint kind for one customer, with a fresh address, order and subscription."""
        address = Address.objects.create(
            customer=customer, label="Spare", street="1 Main St", zip_code="10115", city="Berlin", country="DE"
        )
        order = self.make_order(customer=customer)
        sub = CustomerSubscription.objects.create(
            customer=customer, product=self.weekly, started_on=TODAY, next_delivery=TODAY, is_active=True
        )
        return {
            "customer": {"customer_pk": customer.pk},
            "address": {"customer_pk": customer.pk, "pk": address.pk},
            "order": {"customer_pk": customer.pk, "pk": order.pk},
            "subscription": {"customer_pk": customer.pk, "pk": sub.pk},
        }

    def detail(self, customer):
        return self.client.get(reverse("customer-detail", kwargs={"pk": customer.pk}))

    def test_customer_detail_shows_four_sections(self):
        self.login()
        bar = navbar(self.detail(self.mine))
        self.assertEqual(bar["label"], str(self.mine))
        self.assertEqual([text for text, _href, _active in bar["items"]], LABELS)
        self.assertEqual([href for _text, href, _active in bar["items"]], section_urls(self.mine))
        self.assertEqual(active(bar), ["Details"])

    def test_update_page_has_the_bar_without_an_active_item(self):
        self.login()
        bar = navbar(self.client.get(reverse("customer-update", kwargs={"pk": self.mine.pk})))
        self.assertEqual(len(bar["items"]), 4)
        self.assertEqual(active(bar), [])

    def test_nested_pages_mark_their_section(self):
        self.login()
        fixtures = self.build(self.mine)
        for name, (kind, section) in NESTED_PAGES.items():
            with self.subTest(page=name):
                response = self.client.get(reverse(name, kwargs=fixtures[kind]))
                self.assertEqual(response.status_code, 200)
                bar = navbar(response)
                self.assertEqual(bar["label"], str(self.mine))
                self.assertEqual(active(bar), [section])

    def test_pages_without_a_customer_have_no_bar(self):
        self.login()
        for name in ("customer-list", "customer-create", "orders-list", "orders-create", "subscriptions-list"):
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertIsNone(navbar(response))
                self.assertNotContains(response, "cv-navbar")
                self.assertNotContains(response, "<h1")

    def test_child_buttons_are_gone(self):
        self.login()
        html = self.detail(self.mine).content.decode()
        for key in ("orders", "subscriptions", "addresses"):
            self.assertNotIn(f'cv-key="{key}"', html)
        self.assertIn('cv-key="update"', html)

    def test_bar_is_hidden_in_print(self):
        self.login()
        fixtures = self.build(self.mine)
        html = self.client.get(reverse("order-packing_slip", kwargs=fixtures["order"])).content.decode()
        start = html.index('class="page-header d-print-none')
        self.assertLess(start, html.index('class="cv-tabler-owner'))
        self.assertLess(html.index('class="cv-tabler-owner'), html.index('class="page-body'))
        self.assertIn('class="cv-tabler-navbar d-print-none', html)

    def test_detail_buttons_sit_below_the_tabs(self):
        self.login()
        html = self.detail(self.mine).content.decode()
        page = header(html)
        end = tabs_end(page)
        for key in ("update", "delete"):
            with self.subTest(key=key):
                self.assertGreater(page.index(f'cv-key="{key}"'), end)
        self.assertNotIn("cv-key=", page[page.index("<h1") : end])

    def test_show_code_sits_below_the_tabs(self):
        self.login()
        html = self.client.get(reverse("order-list", kwargs={"customer_pk": self.mine.pk})).content.decode()
        page = header(html)
        end = tabs_end(page)
        self.assertGreater(page.index('href="#code-panel"'), end)
        self.assertGreater(page.index('cv-key="create"'), end)

    def test_heading_that_repeats_the_tab_is_left_out(self):
        self.login()
        fixtures = self.build(self.mine)
        for name in ("customer-detail", "order-list", "subscription-list", "address-list"):
            with self.subTest(page=name):
                kwargs = {"pk": self.mine.pk} if name == "customer-detail" else fixtures["customer"]
                page = header(self.client.get(reverse(name, kwargs=kwargs)).content.decode())
                self.assertNotIn("<h2", page)
                self.assertIn("page-subtitle", page)
                self.assertGreater(page.index('href="#code-panel"'), tabs_end(page))

    def test_heading_that_says_more_than_the_tab_stays(self):
        self.login()
        fixtures = self.build(self.mine)
        for name, kind in (("order-detail", "order"), ("order-update", "order"), ("address-create", "customer")):
            with self.subTest(page=name):
                page = header(self.client.get(reverse(name, kwargs=fixtures[kind])).content.decode())
                self.assertIn("<h2", page)

    def test_state_badge_stays_in_the_view_title(self):
        self.login()
        fixtures = self.build(self.mine)
        html = self.client.get(reverse("order-detail", kwargs=fixtures["order"])).content.decode()
        page = header(html)
        self.assertNotIn("badge", page[page.index("<h1") : page.index("</h1>")])
        self.assertIn("badge", page[page.index("<h2") : page.index("</h2>")])

    def test_visible_items_match_what_the_user_may_open(self):
        for username in ("alex", "sam", "kim"):
            self.login(username)
            for customer in (self.mine, self.other):
                urls = section_urls(customer)
                responses = {url: self.client.get(url) for url in urls}
                openable = [url for url in urls if responses[url].status_code == 200]
                for url in openable:
                    with self.subTest(user=username, customer=str(customer), page=url):
                        bar = navbar(responses[url])
                        self.assertIsNotNone(bar)
                        self.assertEqual([href for _text, href, _active in bar["items"]], openable)

    def test_name_with_markup_is_escaped(self):
        self.login()
        customer = Customer.objects.create(name="<b>A & B</b>")
        html = self.detail(customer).content.decode()
        owner = html[html.index("<h1") : tabs_end(html)]
        self.assertEqual(owner.count("&lt;b&gt;A &amp; B&lt;/b&gt;"), 2)  # the page's h1 and the landmark's label
        title = html[html.index("<title>") : html.index("</title>")]
        self.assertIn(" · &lt;b&gt;A &amp; B&lt;/b&gt; · ", title)
        self.assertNotIn("<b>A", html)

    def test_empty_section_stays_visible(self):
        self.login()
        customer = Customer.objects.create(name="No subscriptions yet")
        self.assertFalse(customer.subscriptions.exists())
        self.assertIn("Subscriptions", [text for text, _href, _active in navbar(self.detail(customer))["items"]])

    def test_invalid_nested_form_keeps_the_bar(self):
        self.login()
        response = self.client.post(reverse("order-create", kwargs={"customer_pk": self.mine.pk}), {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(active(navbar(response)), ["Orders"])

    def test_modal_delete_has_no_bar(self):
        self.login()
        url = reverse("customer-delete", kwargs={"pk": self.mine.pk})
        response = self.client.get(url, headers={"X-CV-Modal": "true"})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(navbar(response))
        self.assertNotContains(response, "cv-navbar")
        self.assertNotContains(response, "<h1")
