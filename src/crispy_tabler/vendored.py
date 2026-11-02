"""Provenance of the vendored templates."""

CRISPY_BOOTSTRAP5_VERSION = "2026.9"
"""The crispy-bootstrap5 release the templates were copied from.

The parity test compares this value to the installed ``crispy-bootstrap5``
distribution, so raising the test pin without re-vendoring fails loudly.
"""
