"""Demo accounts for Acme Roasters. Every app's ``seed.py`` has this signature; ``seed_demo`` calls them in order."""

import random
from datetime import timedelta

from crud_views.lib.settings import crud_views_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.utils import timezone

GROUPS = ("Owner", "Account managers", "Roasters")

# The Owner group gets every permission of these apps. Later apps append theirs (roles are refined per app).
OWNER_APPS = ["auth", "catalog", "sales", "roastery", "showcase"]

# username -> (first name, last name, group, days since sign-up)
ACCOUNTS = {
    "alex": ("Alex", "Acme", "Owner", 300),
    "sam": ("Sam", "Sellers", "Account managers", 180),
    "kim": ("Kim", "Kettle", "Roasters", 90),
}

# Members of the crud_views manage group may open the manage pages (upstream #361); only the Owner is one.
MANAGE_MEMBERS = ("alex",)


def seed(rng: random.Random, world: dict) -> None:
    User = get_user_model()
    groups = {name: Group.objects.get_or_create(name=name)[0] for name in GROUPS}
    groups["Owner"].permissions.set(Permission.objects.filter(content_type__app_label__in=OWNER_APPS))
    now = timezone.now()
    users = {}
    for username, (first, last, group, days) in ACCOUNTS.items():
        user = User(
            username=username,
            first_name=first,
            last_name=last,
            email=f"{username}@acme-roasters.example",
            date_joined=now - timedelta(days=days, hours=rng.randint(0, 23)),
        )
        user.set_password("demo")
        user.save()
        user.groups.add(groups[group])
        users[username] = user
    manage_group = Group.objects.get_or_create(name=crud_views_settings.manage_group)[0]
    manage_group.user_set.add(*(users[name] for name in MANAGE_MEMBERS))
    world["users"] = users
