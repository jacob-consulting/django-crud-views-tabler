"""Per-customer access. Account managers hold no model-level view permission on customers: Guardian grants decide."""

from guardian.core import ObjectPermissionChecker
from guardian.shortcuts import assign_perm, get_objects_for_user, remove_perm


def grant_customer(user, customer, actions=("view", "change")):
    """Give ``user`` object-level permissions on ``customer`` (view and change unless told otherwise)."""
    for action in actions:
        assign_perm(f"sales.{action}_customer", user, customer)


def revoke_customer(user, customer, actions=("view", "change")):
    """Take ``user``'s object-level permissions on ``customer`` away again."""
    for action in actions:
        remove_perm(f"sales.{action}_customer", user, customer)


def sync_owner_grants(customer, previous_owner=None):
    """Make the account manager's grants follow ``Customer.owner``.

    The new owner gets view and change; the previous owner loses theirs (only theirs: other users' grants, such as the
    creator's, stay). Model-level permissions (Owner, Roasters) are untouched either way.
    """
    if customer.owner_id:
        grant_customer(customer.owner, customer)
    if previous_owner is not None and previous_owner.pk != customer.owner_id:
        revoke_customer(previous_owner, customer)


def can_on_customer(user, action, customer) -> bool:
    """Model-level permission (Owner, Roasters) or an object grant (account managers)."""
    return user.has_perm(f"sales.{action}_customer") or ObjectPermissionChecker(user).has_perm(
        f"{action}_customer", customer
    )


def customers_for(user, action="view"):
    """The customers ``user`` may ``action``: all of them with the model-level permission, else the granted ones.

    Access is a Guardian object grant, never a filter on ``Customer.owner``; the customer views keep the account
    manager's grants in step with the owner (``sync_owner_grants``).
    """
    from .models import Customer

    return get_objects_for_user(user, f"sales.{action}_customer", Customer, accept_global_perms=True)
