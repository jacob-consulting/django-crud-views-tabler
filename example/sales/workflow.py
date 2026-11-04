"""Run an order transition outside the workflow view (seed data, later the subscription run), with its history row.

Mirrors what ``WorkflowView.cv_form_valid`` does for a submitted step; upstream has no public helper for this.
"""

from crud_views_workflow.models import WorkflowInfo
from django.contrib.contenttypes.models import ContentType
from django.db import transaction


def run_transition(order, name: str, user, comment: str | None = None, when=None) -> WorkflowInfo:
    """Call ``order.<name>()``, save the order and record the step; ``when`` backdates the history row."""
    with transaction.atomic():
        state_old = order.state
        data = getattr(order, name)(by=user, comment=comment)
        order.save()
        info = WorkflowInfo.objects.create(
            transition=name,
            state_old=state_old,
            state_new=order.state,
            comment=comment,
            user=user,
            data=data,
            workflow_object_pk=str(order.pk),
            workflow_object_content_type=ContentType.objects.get_for_model(order),
        )
        if when is not None:
            WorkflowInfo.objects.filter(pk=info.pk).update(timestamp=when)
    return info
