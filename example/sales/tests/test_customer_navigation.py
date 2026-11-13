"""Integration checks for the private customer section navigation experiment."""

import re
from html import escape, unescape

from django.urls import reverse

from sales.permissions import grant_customer
from .test_customers import SalesTestCase


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

