"""FloatingField and Switch hardcode "bootstrap5/..." and so escape the pack."""

from django_tabler.crispy.layout import FloatingField, Switch

from tests.crispy_tabler.helpers import render_layout


def test_floating_field_and_switch_templates_follow_the_pack():
    assert FloatingField.template == "%s/layout/floating_field.html"
    assert Switch.template == "%s/layout/switch.html"


def test_they_render_with_crispy_bootstrap5_absent(settings):
    settings.INSTALLED_APPS = [
        a for a in settings.INSTALLED_APPS if a != "crispy_bootstrap5"
    ]
    html = render_layout(FloatingField("email"), Switch("checkbox"))
    assert "form-floating" in html and "form-switch" in html
