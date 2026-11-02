from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import NewUserForm

User = get_user_model()


def _month_starts(now, count):
    """First day of each of the last `count` months, oldest first."""
    year, month = now.year, now.month
    starts = []
    for _ in range(count):
        starts.append(now.replace(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0))
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return starts[::-1]


def index(request):
    now = timezone.now()
    last_30 = now - timedelta(days=30)
    previous_30 = now - timedelta(days=60)

    totals = User.objects.aggregate(
        total=Count("pk"),
        active=Count("pk", filter=Q(is_active=True)),
        staff=Count("pk", filter=Q(is_staff=True)),
        superusers=Count("pk", filter=Q(is_superuser=True)),
        staff_only=Count("pk", filter=Q(is_staff=True, is_superuser=False)),
        members=Count("pk", filter=Q(is_staff=False, is_superuser=False)),
        new=Count("pk", filter=Q(date_joined__gte=last_30)),
        new_before=Count("pk", filter=Q(date_joined__gte=previous_30, date_joined__lt=last_30)),
        logged_in=Count("pk", filter=Q(last_login__gte=last_30)),
    )

    months = _month_starts(now, 12)
    joined = dict(
        User.objects.filter(date_joined__gte=months[0])
        .annotate(month=TruncMonth("date_joined"))
        .values_list("month")
        .annotate(n=Count("pk"))
        .values_list("month", "n")
    )
    signups = {
        "labels": [m.strftime("%b") for m in months],
        "values": [joined.get(m, 0) for m in months],
    }
    roles = {
        "labels": ["Superusers", "Staff", "Members"],
        "values": [totals["superusers"], totals["staff_only"], totals["members"]],
    }

    return render(request, "dashboard/index.html", {
        "totals": totals,
        "new_delta": totals["new"] - totals["new_before"],
        "signups": signups,
        "roles": roles,
        "recent_logins": User.objects.filter(last_login__isnull=False).order_by("-last_login")[:5],
    })


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
    return render(request, "dashboard/user_list.html", {
        "page": page,
        "query": query,
        "form": form or NewUserForm(),
        "show_form": form is not None,
    }, status=400 if form is not None else 200)


@require_POST
@permission_required("auth.add_user", raise_exception=True)
def user_create(request):
    form = NewUserForm(request.POST)
    if not form.is_valid():
        return user_list(request, form=form)
    user = form.save()
    messages.success(request, f"User “{user.get_username()}” was created.")
    return redirect("dashboard:users")
