"""Run subscriptions: turn the deliveries that are due into draft orders."""

from datetime import date

from django.db import transaction

from .models import CustomerSubscription, Order, OrderLine


def run_subscriptions(due: date, user) -> list[Order]:
    """Create one draft order (with one line) for every active subscription due by ``due``.

    A subscription is due when its ``next_delivery`` is on or before ``due``.

    Each subscription is advanced in the same transaction, past ``due`` (a lapsed subscription catches up with one
    order, not one per missed interval), so running again for the same date finds nothing due and returns ``[]``.
    ``user`` is the person who ran it; it is named in the order notes.
    """
    orders = []
    with transaction.atomic():
        pending = (
            CustomerSubscription.objects.select_for_update()
            .filter(is_active=True, next_delivery__lte=due)
            .select_related("customer", "product")
            .order_by("next_delivery", "pk")
        )
        for subscription in pending:
            order = Order.objects.create(
                customer=subscription.customer,
                ship_to=subscription.customer.addresses.filter(is_default=True).first(),
                requested_roast_date=subscription.next_delivery,
                notes=f"Subscription delivery ({subscription.product.name}), created by {user.get_username()}.",
            )
            OrderLine.objects.create(
                order=order, product=subscription.product, quantity=subscription.product.bags_per_delivery
            )
            while subscription.next_delivery <= due:
                subscription.advance()
            subscription.save(update_fields=["next_delivery"])
            orders.append(order)
    return orders
