"""Layout objects whose Bootstrap originals cannot be fixed from a template."""

from crispy_forms.bootstrap import UneditableField as BootstrapUneditableField
from crispy_bootstrap5.bootstrap5 import FloatingField as BootstrapFloatingField
from crispy_bootstrap5.bootstrap5 import Switch as BootstrapSwitch


class UneditableField(BootstrapUneditableField):
    """Read-only value rendered with Tabler's form-control-plaintext.

    The crispy_forms original sets the Bootstrap 2 class "uneditable-input"
    on the widget in Python, which a template cannot remove.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Swap the class in place so a css_class argument is kept.
        self.attrs["class"] = self.attrs["class"].replace(
            "uneditable-input", "form-control-plaintext"
        )


class FloatingField(BootstrapFloatingField):
    """FloatingField that follows CRISPY_TEMPLATE_PACK.

    The crispy_bootstrap5 original hardcodes "bootstrap5/layout/...", and
    LayoutObject.get_template_name only substitutes the pack for a "%s".
    """

    template = "%s/layout/floating_field.html"


class Switch(BootstrapSwitch):
    """Switch that follows CRISPY_TEMPLATE_PACK, for the same reason."""

    template = "%s/layout/switch.html"
