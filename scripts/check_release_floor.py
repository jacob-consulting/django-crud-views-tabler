"""Fail unless pyproject.toml requires django-crud-views >= 1.0.0rc1 and nothing installs it from git any more.

Usage: python scripts/check_release_floor.py [pyproject.toml]

The git installs it looks for, next to pyproject.toml: CRUD_VIEWS in noxfile.py (the test matrix) and the line in
requirements/demo.txt (the Render demo). While either is there, the tests run against code PyPI users cannot get.

Until django-crud-views 1.0.0rc1 is on PyPI the theme declares a lower floor and its tests install crud-views from
GitHub main. A release made then would depend on code no PyPI user can install, so publish.yml runs this first.
"""

import sys
import tomllib
from pathlib import Path

from packaging.requirements import Requirement
from packaging.version import Version

PACKAGE = "django-crud-views"
MINIMUM = Version("1.0.0rc1")
GIT_SOURCE = "git+https://github.com/jacob-consulting/django-crud-views"
GIT_INSTALL_FILES = ["noxfile.py", "requirements/demo.txt"]


def floor(spec: str) -> Version | None:
    """The highest lower bound (>=, >, ==, ~=) in a requirement's specifier, or None if it has none."""
    bounds = [Version(s.version) for s in Requirement(spec).specifier if s.operator in (">=", ">", "==", "~=")]
    return max(bounds, default=None)


def main(argv: list[str]) -> int:
    path = Path(argv[1] if len(argv) > 1 else "pyproject.toml")
    dependencies = tomllib.loads(path.read_text())["project"].get("dependencies", [])
    specs = [d for d in dependencies if Requirement(d).name == PACKAGE]
    if not specs:
        print(f"FAIL {path}: no {PACKAGE} requirement")
        return 1
    found = floor(specs[0])
    if found is None or found < MINIMUM:
        print(f"FAIL {path}: {PACKAGE} floor is {found or 'unset'} ({specs[0]!r}), the release needs >= {MINIMUM}")
        return 1
    git_files = [name for name in GIT_INSTALL_FILES if _mentions_git_source(path.parent / name)]
    if git_files:
        print(f"FAIL {path.parent}: {PACKAGE} still installed from {GIT_SOURCE} in {', '.join(git_files)}")
        return 1
    print(f"ok   {path}: {PACKAGE} floor {found}, no git installs")
    return 0


def _mentions_git_source(path: Path) -> bool:
    return path.is_file() and GIT_SOURCE in path.read_text()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
