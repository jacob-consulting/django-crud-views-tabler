from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from crud_views.lib.crispy import CrispyDeleteForm


class DangerSubmit(Submit):
    """A submit button styled as a destructive action (crispy's Submit is always btn-primary)."""

    field_classes = "btn btn-danger"


class TablerDeleteForm(CrispyDeleteForm):
    """CrispyDeleteForm with a full-width confirmation and a red Delete button."""

    @property
    def helper(self):
        helper = FormHelper()
        helper.layout = Layout(
            "confirm",
            FormActions(DangerSubmit("delete", "Delete"), self.get_cancel_button()),
        )
        return helper
