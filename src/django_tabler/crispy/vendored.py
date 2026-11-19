"""Provenance of the vendored templates."""

import re

CRISPY_BOOTSTRAP5_VERSION = "2026.9"
"""The crispy-bootstrap5 release the templates were copied from (scripts/vendor_templates.py).

Each vendored template's first line names it; the vendoring script refuses another installed release.
"""

CRISPY_BOOTSTRAP5_COMPATIBLE = ("2026.3", "2026.9")
"""crispy-bootstrap5 releases whose templates and ``bootstrap5.py`` are byte-identical to the vendored release.

2026.3 is the newest release that installs on Django 4.2 (2026.9 requires Django >= 5.2), so the pack runs unchanged
there. tests/crispy_tabler/test_pack_parity.py proves the identity against whichever release is installed; add a
release here only when that test passes with it.
"""

HAND_EDITED = (
    "field.html",
    "layout/uneditable_input.html",
    "layout/formactions.html",
    "layout/fieldset.html",
    "layout/radioselect_inline.html",
    "layout/checkboxselectmultiple_inline.html",
)
"""Templates edited by hand after vendoring; a re-run of the vendoring script would silently revert them."""

INCLUDE_PREFIX = re.compile(r"""(['"])bootstrap5/""")
"""The quoted include prefix the vendoring script rewrites to ``crispy_tabler/``."""

UPSTREAM_SHA256 = {
    # The crispy-bootstrap5 originals of the hand-edited templates, and bootstrap5.py (FloatingField, Switch are
    # subclassed in django_tabler.crispy.layout), as vendored. The parity test compares the installed files with them.
    "field.html": "1c6d91cfb43dd8909234f977c7934c9d9cc787fba77c33dec505d7717dfc1b99",
    "layout/uneditable_input.html": "c5c85803e8560c72004f1b96d706b7b4858fdd5293fea91be1deb0da69b754d0",
    "layout/formactions.html": "573dc3549fa68cdbe17cdfaa85b56661ae93d998c672ec5ec476d5093efd2a7a",
    "layout/fieldset.html": "91784e751ac70f476ce3f1e6896ac0932506841dbbd0cf0d15292ae2141a66c0",
    "layout/radioselect_inline.html": "7b71f5aad4dd0b72f2ff2bfbe6ffb4c904ef3517ad53f010d4582e481243f824",
    "layout/checkboxselectmultiple_inline.html": "7b71f5aad4dd0b72f2ff2bfbe6ffb4c904ef3517ad53f010d4582e481243f824",
    "bootstrap5.py": "1ad443567a543685475661401139e6ad593264f63e1d84a6c19180cf45b8d134",
}
