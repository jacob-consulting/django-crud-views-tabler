from datetime import date, datetime

from crud_views.lib.resource import Resource
from django.utils.translation import gettext_lazy as _
from pydantic import BaseModel
from sales.models import Order
from sales.permissions import customers_for

from .courier import fetch_shipments


class TrackingEvent(BaseModel):  # plain pydantic model: events are not rows of their own
    at: datetime
    description: str
    location: str
    icon: str


class Shipment(Resource):
    tracking_number: str
    order_number: int
    order_pk: int
    customer_pk: int
    customer_name: str
    carrier: str
    status: str
    shipped_at: datetime
    eta: date
    events: list[TrackingEvent]

    class Meta:
        verbose_name = _("shipment")
        verbose_name_plural = _("shipments")
        app_label = "shipping"
        pk_field = "tracking_number"

    def __str__(self) -> str:
        return self.tracking_number

    @property
    def is_delivered(self) -> bool:
        return self.status == "delivered"

    @classmethod
    def cv_get_items(cls, request, **url_kwargs):
        """The courier's shipments, limited to the orders of customers the user may view (Guardian grants)."""
        orders = Order.objects.filter(customer__in=customers_for(request.user))
        return [cls.model_validate(row) for row in fetch_shipments(orders)]
