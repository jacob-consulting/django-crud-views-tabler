def test_app_is_installed_and_pack_is_selected():
    from crispy_forms.utils import TEMPLATE_PACK
    from django.apps import apps

    assert apps.is_installed("django_tabler")
    assert str(TEMPLATE_PACK) == "crispy_tabler"


def test_installed_crispy_bootstrap5_is_template_compatible():
    # 2026.3 (the newest release on Django 4.2) and 2026.9 have byte-identical templates; test_pack_parity.py compares
    # the vendored templates with the installed ones, whichever of the two it is.
    from importlib.metadata import version

    from django_tabler.crispy.vendored import CRISPY_BOOTSTRAP5_COMPATIBLE, CRISPY_BOOTSTRAP5_VERSION

    assert version("crispy-bootstrap5") in CRISPY_BOOTSTRAP5_COMPATIBLE
    assert CRISPY_BOOTSTRAP5_VERSION in CRISPY_BOOTSTRAP5_COMPATIBLE
