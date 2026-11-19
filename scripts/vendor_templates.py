#!/usr/bin/env python3
"""Vendor the crispy-bootstrap5 template pack into django_tabler.

Usage (from the repo root, with the test extra installed):

    uv run python scripts/vendor_templates.py [--force]

Copies every template of the installed crispy-bootstrap5 into
src/django_tabler/templates/crispy_tabler/ and applies exactly two changes
per file: the quoted ``bootstrap5/`` include prefix becomes ``crispy_tabler/``,
and one provenance comment is prepended. Everything else stays byte-identical
so a later re-vendor can be diffed against upstream.

Files under widget/ are pack-owned (no Bootstrap counterpart) and are never
touched. Six templates were hand-edited after vendoring (HAND_EDITED below); the
script refuses to run while it would overwrite them, unless --force is given.
After a forced run, review the git diff and re-apply those edits.
"""

import re
import sys
from importlib.metadata import version
from pathlib import Path

import crispy_bootstrap5

from django_tabler.crispy.vendored import CRISPY_BOOTSTRAP5_VERSION

SRC = Path(crispy_bootstrap5.__file__).parent / "templates" / "bootstrap5"
DEST = Path(__file__).resolve().parent.parent / "src/django_tabler/templates/crispy_tabler"
# Templates edited by hand after vendoring; a re-run would silently revert them.
HAND_EDITED = (
    "field.html",
    "layout/uneditable_input.html",
    "layout/formactions.html",
    "layout/fieldset.html",
    "layout/radioselect_inline.html",
    "layout/checkboxselectmultiple_inline.html",
)
INCLUDE_PREFIX = re.compile(r"""(['"])bootstrap5/""")


def main(argv: list[str]) -> int:
    installed = version("crispy-bootstrap5")
    if installed != CRISPY_BOOTSTRAP5_VERSION:
        print(
            f"installed crispy-bootstrap5 {installed} != vendored.py "
            f"{CRISPY_BOOTSTRAP5_VERSION}; update vendored.py first",
            file=sys.stderr,
        )
        return 1
    if "--force" not in argv:
        clobbered = [rel for rel in HAND_EDITED if (SRC / rel).is_file()]
        if clobbered:
            print(
                "refusing to overwrite hand-edited templates:\n  "
                + "\n  ".join(clobbered)
                + "\nre-run with --force to overwrite them, then re-apply the edits from git history.",
                file=sys.stderr,
            )
            return 1
    count = 0
    for src in sorted(p for p in SRC.rglob("*") if p.is_file()):
        rel = src.relative_to(SRC).as_posix()
        text = src.read_bytes().decode("utf-8")
        text = INCLUDE_PREFIX.sub(r"\1crispy_tabler/", text)
        # The header records the pack-relative path (not "bootstrap5/<rel>"), so it
        # never contains the "bootstrap5/" prefix the self-containment test forbids.
        header = f"{{# vendored from crispy-bootstrap5 {installed}: {rel} #}}\n"
        out = DEST / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes((header + text).encode("utf-8"))
        count += 1
    print(f"vendored {count} templates into {DEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
