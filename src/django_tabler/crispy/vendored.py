"""Provenance of the vendored templates."""

CRISPY_BOOTSTRAP5_VERSION = "2026.9"
"""The crispy-bootstrap5 release the templates were copied from.

The parity test compares this value to the installed ``crispy-bootstrap5``
distribution, so raising the test pin without re-vendoring fails loudly.
"""

CRISPY_BOOTSTRAP5_COMPATIBLE = ("2026.3", "2026.9")
"""crispy-bootstrap5 releases whose templates and ``bootstrap5.py`` are byte-identical to the vendored release.

Checked 2026-11-19. 2026.3 is the newest release that installs on Django 4.2 (2026.9 requires Django >= 5.2), so the
pack runs unchanged there. Add a release here only after diffing its templates with the vendored ones.
"""
