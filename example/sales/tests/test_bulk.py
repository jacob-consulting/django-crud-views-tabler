"""Bulk actions on all orders (django-crud-views #392): "Mark roasted" and "Cancel" run the orders' django-fsm
transitions, so orders in the wrong state show as blocked on the review page and history is written as on the
workflow page."""

from crud_views_workflow.models import WorkflowInfo
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from lxml import html as lxml_html

from sales.models import Order, OrderState

from .test_orders import OrderTestCase


def history(order):
    return WorkflowInfo.objects.filter(
        workflow_object_pk=str(order.pk), workflow_object_content_type=ContentType.objects.get_for_model(Order)
    )


def text(element):
    return " ".join(element.text_content().split())


class OrderBulkTests(OrderTestCase):
    def doc(self, response):
        self.assertEqual(response.status_code, 200)
        return lxml_html.fromstring(response.content.decode())

    def post(self, action, orders, stage="review", **data):
        url = reverse(f"orders-{action}")
        return self.client.post(url, {"cv_bulk_stage": stage, "cv_bulk_ids": [o.pk for o in orders], **data})

    def test_list_offers_the_two_actions(self):
        self.login()
        doc = self.doc(self.client.get(reverse("orders-list")))
        (toolbar,) = doc.cssselect("form[data-cv-bulk]")
        actions = [b.get("data-cv-bulk-action") for b in toolbar.cssselect("button[data-cv-bulk-action]")]
        self.assertEqual(actions, ["bulk_roast", "bulk_cancel"])
        self.assertEqual(
            [text(b) for b in toolbar.cssselect("button[data-cv-bulk-action]")], ["Mark roasted", "Cancel orders"]
        )
        boxes = doc.cssselect("table tbody input[data-cv-bulk-item]")
        self.assertEqual(len(boxes), 20)  # one page

    def test_card_view_offers_the_actions(self):
        self.login()
        doc = self.doc(self.client.get(reverse("orders-card")))
        (toolbar,) = doc.cssselect("form[data-cv-bulk]")
        self.assertEqual(len(toolbar.cssselect("button[data-cv-bulk-action]")), 2)
        cards = doc.cssselect("main [data-order-card]")
        self.assertEqual(len(cards), 12)
        for card in cards:
            (cell,) = card.xpath("ancestor::div[contains(@class, 'position-relative')][1]")
            self.assertEqual(len(cell.cssselect("input[data-cv-bulk-item]")), 1)

    def test_roast_runs_the_transition_when_all_are_confirmed(self):
        self.login("kim")  # a roaster: roast_order, no change_order
        orders = [self.make_order(state=OrderState.CONFIRMED) for _ in range(2)]
        response = self.post("bulk_roast", orders)
        self.assertRedirects(response, reverse("orders-list"), fetch_redirect_response=False)
        for order in orders:
            order.refresh_from_db()
            self.assertEqual(order.state, OrderState.ROASTED)
            self.assertEqual(list(history(order).values_list("transition", flat=True)), ["wf_roast"])
        doc = self.doc(self.client.get(reverse("orders-list")))
        self.assertEqual([text(a) for a in doc.cssselect(".alert")], ["2 orders marked roasted."])

    def test_roast_shows_blocked_orders(self):
        self.login()
        confirmed = self.make_order(state=OrderState.CONFIRMED)
        draft = self.make_order(state=OrderState.DRAFT)
        doc = self.doc(self.post("bulk_roast", [confirmed, draft]))
        (blocked,) = doc.cssselect("main form.cv-form .alert-warning")
        self.assertIn(f"{draft}: Only confirmed orders can be roasted; this one is draft.", text(blocked))
        self.assertIn("To process: 1", text(doc.cssselect("main form.cv-form")[0]))
        confirmed.refresh_from_db()
        self.assertEqual(confirmed.state, OrderState.CONFIRMED)  # nothing written until confirmed
        # confirm: only the eligible order moves
        data = {"cv_bulk_blocked_ids": [draft.pk]}
        response = self.post("bulk_roast", [confirmed], stage="execute", **data)
        self.assertEqual(response.status_code, 302)
        confirmed.refresh_from_db()
        draft.refresh_from_db()
        self.assertEqual((confirmed.state, draft.state), (OrderState.ROASTED, OrderState.DRAFT))

    def test_cancel_asks_for_a_reason(self):
        self.login()
        orders = [self.make_order(state=OrderState.DRAFT), self.make_order(state=OrderState.CONFIRMED)]
        shipped = self.make_order(state=OrderState.SHIPPED)
        doc = self.doc(self.post("bulk_cancel", [*orders, shipped]))
        form = doc.cssselect("main form.cv-form")[0]
        self.assertTrue(form.cssselect("textarea[name=comment]"))
        self.assertIn("Only draft and confirmed orders can be cancelled; this one is shipped.", text(form))
        # the reason is required
        response = self.post("bulk_cancel", orders, stage="execute", cv_bulk_blocked_ids=[shipped.pk])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.filter(pk__in=[o.pk for o in orders], state=OrderState.CANCELLED).count(), 0)
        response = self.post(
            "bulk_cancel", orders, stage="execute", cv_bulk_blocked_ids=[shipped.pk], comment="Customer called"
        )
        self.assertEqual(response.status_code, 302)
        for order in orders:
            order.refresh_from_db()
            self.assertEqual(order.state, OrderState.CANCELLED)
            self.assertEqual(history(order).get().comment, "Customer called")
        shipped.refresh_from_db()
        self.assertEqual(shipped.state, OrderState.SHIPPED)

    def test_roasters_may_not_cancel(self):
        self.login("kim")
        order = self.make_order(state=OrderState.DRAFT)
        self.assertEqual(self.post("bulk_cancel", [order]).status_code, 403)

    def test_sam_cannot_touch_other_customers_orders(self):
        self.login("sam")
        theirs = self.make_order(customer=self.other, state=OrderState.DRAFT)
        doc = self.doc(self.post("bulk_cancel", [theirs]))
        # out of his scope: the generic "unavailable" entry, without the order's name
        (blocked,) = doc.cssselect("main form.cv-form .alert-warning")
        self.assertNotIn(str(theirs), text(blocked))
        response = self.post("bulk_cancel", [theirs], stage="execute", comment="x")
        self.assertEqual(response.status_code, 200)  # all blocked: the review again, nothing written
        theirs.refresh_from_db()
        self.assertEqual(theirs.state, OrderState.DRAFT)
        self.assertFalse(history(theirs).exists())
