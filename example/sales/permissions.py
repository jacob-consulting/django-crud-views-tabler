"""Per-customer access. Account managers hold no model-level view permission on customers: Guardian grants decide."""

from guardian.core import ObjectPermissionChecker
from guardian.shortcuts import assign_perm


def grant_customer(user, customer, actions=("view", "change")):
    """Give ``user`` object-level permissions on ``customer`` (view and change unless told otherwise)."""
    for action in actions:
        assign_perm(f"sales.{action}_customer", user, customer)


def can_on_customer(user, action, customer) -> bool:
    """Model-level permission (Owner, Roasters) or an object grant (account managers)."""
    return user.has_perm(f"sales.{action}_customer") or ObjectPermissionChecker(user).has_perm(
        f"{action}_customer", customer
    )
