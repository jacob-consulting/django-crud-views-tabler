from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from django.db.models import F, Min, Q, Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from roastery.models import CuppingSession, GreenLot
from sales.models import CustomerSubscription, Order, OrderState
from sales.permissions import customers_for

from .forms import NewUserForm

User = get_user_model()


REVENUE_STATES = (OrderState.CONFIRMED, OrderState.ROASTED, OrderState.SHIPPED, OrderState.DELIVERED)
OPEN_STATES = (OrderState.CONFIRMED, OrderState.ROASTED)
WEEKS = 12


def _revenue(orders):
    """Sum of ``Order.total`` (lines less the customer's tier discount); ``total`` is a Python property."""
    return sum((o.total for o in orders), Decimal("0.00"))


def _sales_stats(user, today):
    """Everything derived from orders and subscriptions, restricted to the customers ``user`` may view."""
    customers = customers_for(user)
    orders = Order.objects.filter(customer__in=customers)
    week_start = today - timedelta(days=today.weekday() + 7 * (WEEKS - 1))
    since = min(week_start, today - timedelta(days=60))
    # One query: the window covers the 12 weeks and both 30-day periods; money is summed in Python.
    window = list(
        orders.filter(state__in=REVENUE_STATES, created_at__date__gte=since)
        .select_related("customer")
        .prefetch_related("lines")
    )
    current = _revenue(o for o in window if o.created_at.date() > today - timedelta(days=30))
    previous = _revenue(
        o for o in window if today - timedelta(days=60) < o.created_at.date() <= today - timedelta(days=30)
    )
    trend = ((current - previous) / previous * 100).quantize(Decimal("0.1"), ROUND_HALF_UP) if previous else None

    weekly = {week_start + timedelta(weeks=i): Decimal("0.00") for i in range(WEEKS)}
    for o in window:
        day = o.created_at.date()
        key = day - timedelta(days=day.weekday())
        if key in weekly:
            weekly[key] += o.total

    subscriptions = CustomerSubscription.objects.filter(customer__in=customers, is_active=True)
    to_roast = (
        orders.filter(state=OrderState.CONFIRMED)
        .filter(Q(requested_roast_date__isnull=True) | Q(requested_roast_date__lte=today + timedelta(days=7)))
        .select_related("customer")
        .prefetch_related("lines__product")
        .order_by(F("requested_roast_date").asc(nulls_last=True), "number")
    )
    return {
        "revenue_30d": current,
        "revenue_trend_pct": trend,
        "open_orders": orders.filter(state__in=OPEN_STATES).count(),
        "orders_waiting_to_roast": orders.filter(state=OrderState.CONFIRMED).count(),
        "orders_to_roast": to_roast,
        "active_subscriptions": subscriptions.count(),
        "next_subscription_run": subscriptions.aggregate(d=Min("next_delivery"))["d"],
        "revenue_by_week": [(f"W{d.isocalendar().week}", v) for d, v in weekly.items()],
    }


def index(request):
    """The roastery overview.

    Sales numbers (revenue, orders, subscriptions) cover only the customers the user may view
    (``sales.permissions.customers_for``), so an account manager sees their own book. Roastery numbers are shared.

    Revenue counts orders in the confirmed, roasted, shipped or delivered state (draft and cancelled orders never
    earned anything), dated by ``created_at``; "30 days" is the 30 days ending now and the trend compares it with
    the 30 days before. The weekly chart uses the same rule over the last 12 ISO weeks, Monday to Sunday, the
    current one included.
    """
    today = timezone.localdate()
    context = _sales_stats(request.user, today)
    context["today"] = today
    context["revenue_chart"] = {
        "labels": [label for label, _ in context["revenue_by_week"]],
        "values": [float(v) for _, v in context["revenue_by_week"]],
    }
    if request.user.has_perm("roastery.view_greenlot"):
        stock = GreenLot.objects.aggregate(on_hand=Sum("kg_on_hand"), purchased=Sum("kg_purchased"))
        on_hand = stock["on_hand"] or Decimal("0")
        context["green_stock_kg"] = on_hand
        context["green_stock_pct"] = round(on_hand / stock["purchased"] * 100) if stock["purchased"] else 0
        context["recent_cuppings"] = list(
            CuppingSession.objects.select_related("lot__origin").prefetch_related("scores")[:5]
        )
    return render(request, "dashboard/index.html", context)


@permission_required("auth.view_user", raise_exception=True)
def user_list(request, form=None):
    query = request.GET.get("q", "").strip()
    users = User.objects.order_by("username")
    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
        )
    page = Paginator(users, 25).get_page(request.GET.get("page"))
    return render(
        request,
        "dashboard/user_list.html",
        {
            "page": page,
            "query": query,
            "form": form or NewUserForm(),
            "show_form": form is not None,
        },
        status=400 if form is not None else 200,
    )


@require_POST
@permission_required("auth.add_user", raise_exception=True)
def user_create(request):
    form = NewUserForm(request.POST)
    if not form.is_valid():
        return user_list(request, form=form)
    user = form.save()
    messages.success(request, f"User “{user.get_username()}” was created.")
    return redirect("dashboard:users")
