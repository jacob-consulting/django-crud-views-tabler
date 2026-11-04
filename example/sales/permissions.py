"""Per-customer access. Account managers hold no model-level view permission on customers: Guardian grants decide."""

from guardian.core import ObjectPermissionChecker
from guardian.shortcuts import assign_perm, get_objects_for_user


def grant_customer(user, customer, actions=("view", "change")):
    """Give ``user`` object-level permissions on ``customer`` (view and change unless told otherwise)."""
    for action in actions:
        assign_perm(f"sales.{action}_customer", user, customer)


def can_on_customer(user, action, customer) -> bool:
    """Model-level permission (Owner, Roasters) or an object grant (account managers)."""
    return user.has_perm(f"sales.{action}_customer") or ObjectPermissionChecker(user).has_perm(
        f"{action}_customer", customer
    )


def customers_for(user, action="view"):
    """The customers ``user`` may ``action``: all of them with the model-level permission, else the granted ones.

    Grants are Guardian object permissions and independent of ``Customer.owner``, so this never filters by owner.
    """
    from .models import Customer

    return get_objects_for_user(user, f"sales.{action}_customer", Customer, accept_global_perms=True)
