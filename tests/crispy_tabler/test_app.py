def test_app_is_installed_and_pack_is_selected():
    from crispy_forms.utils import TEMPLATE_PACK
    from django.apps import apps

    assert apps.is_installed("crispy_tabler")
    assert str(TEMPLATE_PACK) == "crispy_tabler"


def test_vendored_version_matches_the_installed_crispy_bootstrap5():
    from importlib.metadata import version

    from crispy_tabler.vendored import CRISPY_BOOTSTRAP5_VERSION

    assert version("crispy-bootstrap5") == CRISPY_BOOTSTRAP5_VERSION
