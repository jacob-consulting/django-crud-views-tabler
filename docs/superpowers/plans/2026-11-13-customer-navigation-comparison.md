# Customer navigation comparison — Phase 06.33

## Isolation established 2026-11-13

Product work belongs only to `/home/alex/projects/workspaces/customer-navigation-06-33/tabler-test`, branch
`experiment/customer-section-navigation-06-33`. No merge into tabler-test/main is authorized.
Upstream planning belongs to `/home/alex/projects/workspaces/cv-phase-06-33/django-crud-views`,
branch `gsd/phase-06.33`; product and tracking commits are separate.

| Checkout | Revision at setup | Role |
| --- | --- | --- |
| /home/alex/projects/alex/tabler-test | 4f8d0326d63d7974029b7243b1ddbe63cadb625a | Clean source main, preserved |
| /home/alex/projects/workspaces/customer-navigation-06-33/tabler-test | 4f8d0326d63d7974029b7243b1ddbe63cadb625a | Experiment branch |
| /home/alex/projects/workspaces/customer-navigation-06-33/tabler-test-baseline | 4f8d0326d63d7974029b7243b1ddbe63cadb625a | Detached baseline |
| /home/alex/projects/workspaces/customer-navigation-06-33/django-crud-views | 1133591a8aad7202f6f95c6a6a7fd777809de604 | Detached shared dependency |
| /home/alex/projects/workspaces/customer-navigation-06-33/django-crud-views-extensions | 667f27a966d95413ac9ec79c0cd05cac98bcbc81 | Detached shared dependency |

Core source advanced from research's ca3a81ab845e69fe3ab035d7fc885dc3008604aa to the recorded
revision: changes implement conditional queryset fields and tests/planning, with no changes to navigation,
parent resolution, access hooks or routes. This bounded source drift was inspected before setup.
The core source's dirty planning state and two unrelated .gitkeep files were preserved. No source data
was copied/reset; no source environment was used. Dependency worktrees remain read-only after creation.

## Commands executed

Created the experiment using `git worktree add -b experiment/customer-section-navigation-06-33`
at the exact downstream revision above; created the baseline and two dependencies using
`git worktree add --detach <absolute-checkout> <recorded-sha>` in their respective source repositories.
No pre-existing comparison worktree or branch was overwritten.

In **each** downstream checkout, from its own cwd:

```bash
unset UV_PROJECT_ENVIRONMENT PYTHONPATH DJANGO_SETTINGS_MODULE
uv sync --locked --group test
uv run python example/manage.py migrate
uv run python example/manage.py seed_demo --seed 633
uv run python example/manage.py check --fail-level WARNING
```

All commands exited 0 on 2026-11-13. Both seed operations ran once against fresh databases on that date.
Both system checks reported no issues. Python 3.14.7, Django 6.1.2, pytest 9.2.0; the lock is unchanged.
Do not rerun seed on these populated databases, or use reset. Fresh comparisons require new independent data.

## Verified environment assertions

Ran the following in each checkout with `uv run python example/manage.py shell -c '<code>'`:

```python
import json, sys
from pathlib import Path
from importlib.metadata import distribution
from urllib.parse import urlparse, unquote
import django_tabler
from django.conf import settings
root = Path.cwd().resolve()
assert Path(sys.prefix) == root / ".venv"
assert Path(django_tabler.__file__).is_relative_to(root / "src")
assert Path(settings.DATABASES["default"]["NAME"]).resolve() == root / "example/db.sqlite3"
assert Path(settings.MEDIA_ROOT).resolve() == root / "example/media"
for name in ("django-crud-views", "django-crud-views-extensions"):
    metadata = json.loads(distribution(name).read_text("direct_url.json"))
    path = Path(unquote(urlparse(metadata["url"]).path)).resolve()
    assert path == root.parent / name
    print(name, path)
print("CHECKOUT", root, "VENV", sys.prefix, "TABLER", django_tabler.__file__)
print("DATABASE", settings.DATABASES["default"]["NAME"], "MEDIA", settings.MEDIA_ROOT)
```

All assertions passed. For both `tabler-test` and `tabler-test-baseline`, prefix is
`<checkout>/.venv`, django_tabler imports from `<checkout>/src/django_tabler/__init__.py`,
database is `<checkout>/example/db.sqlite3`, and media root is `<checkout>/example/media`.
Thus environments, product imports, databases and media are distinct; both dependency direct_url values
resolve to the exact sibling paths in the table. No settings or dependency declaration was edited.

