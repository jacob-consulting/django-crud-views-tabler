import random
from importlib import import_module

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction

# Each app listed here has a ``seed.py`` with ``seed(rng, world)``, run in dependency order. ``shipping`` has none:
# its shipments are derived from the orders.
SEED_APPS = ["dashboard", "catalog", "sales", "roastery"]

DEMO_USERNAMES = ("alex", "sam", "kim")
DEMO_GROUPS = ("Owner", "Account managers", "Roasters")

REFUSAL = "Demo data already present; use --reset to rebuild."


def delete_demo_data() -> None:
    """Wipe the demo apps' tables whole, rows you added included (never ``admin`` or other users), children first."""
    from catalog.models import Category, FlavorNote, Origin, Product
    from crud_views_workflow.models import WorkflowInfo
    from guardian.models import GroupObjectPermission, UserObjectPermission
    from roastery.models import CuppingScore, CuppingSession, GreenLot, RoastBatch
    from sales.models import Address, Customer, CustomerSubscription, Order

    demo_models = [Customer, Address, Order, Product, GreenLot]
    cts = ContentType.objects.get_for_models(*demo_models).values()
    WorkflowInfo.objects.filter(workflow_object_content_type=ContentType.objects.get_for_model(Order)).delete()
    UserObjectPermission.objects.filter(content_type__in=cts).delete()
    GroupObjectPermission.objects.filter(content_type__in=cts).delete()
    RoastBatch.objects.all().delete()  # PROTECTs lot, roaster; links to orders
    CuppingScore.objects.all().delete()  # PROTECTs taster
    CuppingSession.objects.all().delete()
    Order.objects.all().delete()  # lines cascade; PROTECTs customer and, via lines, products
    CustomerSubscription.objects.all().delete()  # PROTECTs the subscription product
    Customer.objects.all().delete()  # addresses cascade
    Product.objects.all().delete()  # child rows cascade; Beans.green_lot is SET_NULL
    GreenLot.objects.all().delete()
    Category.objects.all().delete()
    FlavorNote.objects.all().delete()
    Origin.objects.all().delete()
    get_user_model().objects.filter(username__in=DEMO_USERNAMES).delete()
    Group.objects.filter(name__in=DEMO_GROUPS).delete()


class Command(BaseCommand):
    help = "Seed the Acme Roasters demo data (demo accounts alex, sam, kim; password demo)."

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=42, help="Random seed, for repeatable data.")
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Wipe the demo tables entirely first, including rows you added yourself (not admin), then rebuild.",
        )

    def handle(self, *args, seed, reset, **options):
        User = get_user_model()
        if User.objects.filter(username__in=DEMO_USERNAMES).exists() and not reset:
            self.stdout.write(REFUSAL)
            return
        rng = random.Random(seed)
        world: dict = {}
        with transaction.atomic():
            if reset:
                delete_demo_data()
            for app in SEED_APPS:
                import_module(f"{app}.seed").seed(rng, world)
        self.stdout.write(self.style.SUCCESS(f"Seeded the demo data for: {', '.join(SEED_APPS)}."))
