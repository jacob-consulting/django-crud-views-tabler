"""Fail if a built wheel or sdist contains anything outside its allowlist, or a wheel lacks its templates/static.

Usage: python scripts/check_dist.py dist/

Ported from django-crud-views. The repository carries planning and tooling folders (superpowers/, dev/, .superpowers/,
...) that must never reach PyPI. Rather than list what to keep out, this checks every archive member against what may
go in, so a new folder at the repository root fails the build until someone decides where it belongs. A wheel without
its templates or static files would install fine and render nothing, so their presence is checked too.
"""

import sys
import tarfile
import zipfile
from pathlib import Path

# Top-level entries allowed in the sdist, below its "<name>-<version>/" prefix. Keep in sync with
# [tool.hatch.build.targets.sdist] only-include in pyproject.toml; hatchling adds PKG-INFO and .gitignore itself.
SDIST_ALLOWED = {
    "src",
    "tests",
    "docs",
    "example",
    "noxfile.py",
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
    "pyproject.toml",
    "PKG-INFO",
    ".gitignore",
}

# Top-level entries allowed in the wheel: the two packages plus the .dist-info directory.
WHEEL_PACKAGES = {"crud_views_tabler", "django_tabler"}

# One witness per template/static tree: a wheel that misses these was built without its package data.
WHEEL_REQUIRED = [
    "django_tabler/templates/django_tabler/base.html",
    "django_tabler/templates/crispy_tabler/field.html",
    "django_tabler/static/django_tabler/layout-switch.js",
    "crud_views_tabler/templates/crud_views_tabler/page.html",
    "crud_views_tabler/static/crud_views_tabler/crud_views_tabler.css",
    "crud_views_tabler/static/crud_views_tabler/tabler-adapters.js",
]


def sdist_violations(path: Path) -> list[str]:
    with tarfile.open(path) as tar:
        names = tar.getnames()
    bad = []
    for name in names:
        parts = name.split("/", 2)
        if len(parts) < 2 or not parts[1]:
            continue  # the "<name>-<version>/" root itself
        if parts[1] not in SDIST_ALLOWED or "__pycache__" in name.split("/"):
            bad.append(name)
    return bad


def wheel_violations(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as whl:
        names = whl.namelist()
    bad = []
    for name in names:
        top = name.split("/", 1)[0]
        if top.endswith(".dist-info"):
            continue
        if (
            top not in WHEEL_PACKAGES
            or "__pycache__" in name.split("/")
            or name.endswith(".pyc")
            or name.rsplit("/", 1)[-1] == "tests.py"
        ):
            bad.append(name)
    bad += [f"missing: {name}" for name in WHEEL_REQUIRED if name not in names]
    return bad


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    dist = Path(argv[1])
    sdists = sorted(dist.glob("*.tar.gz"))
    wheels = sorted(dist.glob("*.whl"))
    if not sdists or not wheels:
        print(f"expected at least one sdist and one wheel in {dist}/", file=sys.stderr)
        return 1

    failed = False
    for path, check in [(p, sdist_violations) for p in sdists] + [(p, wheel_violations) for p in wheels]:
        bad = check(path)
        if bad:
            failed = True
            print(f"FAIL {path.name}: {len(bad)} problem(s):")
            for name in bad:
                print(f"     {name}")
        else:
            print(f"ok   {path.name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
