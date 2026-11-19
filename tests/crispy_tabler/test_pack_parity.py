import hashlib
from pathlib import Path

import crispy_bootstrap5
from crispy_forms.utils import render_crispy_form

import django_tabler
from django_tabler.crispy.vendored import CRISPY_BOOTSTRAP5_VERSION
from tests.crispy_tabler.forms import CoverageForm

BS5_ROOT = Path(crispy_bootstrap5.__file__).parent / "templates" / "bootstrap5"
PACK_ROOT = Path(django_tabler.__file__).parent / "templates" / "crispy_tabler"


def _names(root: Path, *, skip: tuple[str, ...] = ()) -> set[str]:
    if not root.is_dir():
        return set()
    return {
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and p.relative_to(root).parts[0] not in skip
    }


def bs5_names() -> set[str]:
    return _names(BS5_ROOT)


def pack_names() -> set[str]:
    # widget/ holds templates with no Bootstrap counterpart (added later).
    return _names(PACK_ROOT, skip=("widget",))


def pack_files() -> list[Path]:
    files = sorted(PACK_ROOT.rglob("*.html"))
    assert files, f"no templates under {PACK_ROOT}"  # never pass vacuously
    return files


def test_every_bootstrap5_template_has_a_counterpart():
    assert bs5_names() - pack_names() == set()


def test_the_pack_adds_nothing_unexpected():
    assert pack_names() - bs5_names() == set()


def test_no_template_resolves_to_the_bootstrap5_pack():
    """A leaked include/extends is always a path: the pack prefix plus a slash.

    The bare package name is allowed (provenance headers name crispy-bootstrap5).
    """
    offenders = [p for p in pack_files() if "bootstrap5/" in p.read_text()]
    assert offenders == []


def test_every_template_records_its_provenance():
    for p in pack_files():
        rel = p.relative_to(PACK_ROOT).as_posix()
        if rel.startswith("widget/"):
            continue  # originals of this package, not vendored
        expected = f"{{# vendored from crispy-bootstrap5 {CRISPY_BOOTSTRAP5_VERSION}: {rel} #}}"
        assert p.read_text().splitlines()[0] == expected, rel


def test_a_form_renders_through_the_pack_without_touching_bootstrap5(settings):
    settings.INSTALLED_APPS = [a for a in settings.INSTALLED_APPS if a != "crispy_bootstrap5"]
    html = render_crispy_form(CoverageForm())
    assert "form-control" in html


def test_vendored_templates_match_the_installed_crispy_bootstrap5_byte_for_byte():
    """Every vendored template is the installed one plus header and include rewrite (scripts/vendor_templates.py).

    The hand-edited templates cannot match; their installed upstream originals must still be the ones vendored, by
    hash. This is what makes CRISPY_BOOTSTRAP5_COMPATIBLE safe: a release with changed templates fails here.
    """
    from django_tabler.crispy.vendored import HAND_EDITED, INCLUDE_PREFIX, UPSTREAM_SHA256

    checked = 0
    for rel in sorted(bs5_names()):
        upstream = (BS5_ROOT / rel).read_bytes()
        if rel in HAND_EDITED:
            assert hashlib.sha256(upstream).hexdigest() == UPSTREAM_SHA256[rel], rel
            continue
        expected = f"{{# vendored from crispy-bootstrap5 {CRISPY_BOOTSTRAP5_VERSION}: {rel} #}}\n"
        expected += INCLUDE_PREFIX.sub(r"\1crispy_tabler/", upstream.decode("utf-8"))
        assert (PACK_ROOT / rel).read_bytes().decode("utf-8") == expected, rel
        checked += 1
    assert checked > 30  # never pass vacuously


def test_subclassed_layout_objects_match_the_vendored_crispy_bootstrap5():
    # django_tabler.crispy.layout subclasses FloatingField and Switch from this module.
    from django_tabler.crispy.vendored import UPSTREAM_SHA256

    source = (Path(crispy_bootstrap5.__file__).parent / "bootstrap5.py").read_bytes()
    assert hashlib.sha256(source).hexdigest() == UPSTREAM_SHA256["bootstrap5.py"]
