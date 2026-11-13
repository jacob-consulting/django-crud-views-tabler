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

## Restart and compare — verified 2026-11-13

Both independently owned servers are running after tested stop/restart cycles. Compare
baseline http://localhost:8633/customer/4/detail/ with experiment
http://127.0.0.1:8634/customer/4/detail/ (Café Rue Mouffe). Sign in separately on both hosts using
the demo accounts documented in CLAUDE.md: alex (Owner), sam (Account managers), kim (Roasters),
password `demo`. These are synthetic demo credentials. Maintainer feedback remains pending.

Start baseline in its own terminal:

```bash
cd /home/alex/projects/workspaces/customer-navigation-06-33/tabler-test-baseline
unset UV_PROJECT_ENVIRONMENT PYTHONPATH DJANGO_SETTINGS_MODULE
.venv/bin/python example/manage.py runserver localhost:8633 --noreload
```

Start experiment in another terminal:

```bash
cd /home/alex/projects/workspaces/customer-navigation-06-33/tabler-test
unset UV_PROJECT_ENVIRONMENT PYTHONPATH DJANGO_SETTINGS_MODULE
.venv/bin/python example/manage.py runserver 127.0.0.1:8634 --noreload
```

The direct executable was launched with its own cwd and environment, stdout/stderr appended to
`<checkout>/.local/customer-navigation-06-33/server.log`. Process records are in the adjacent
`server.json`; local evidence is excluded through the repository's local Git exclude file.
No uv wrapper or autoreloader owns the listener. Commands above are reproducible foreground alternatives.

| Server | Previous PID | Current PID | /proc start ticks | Restart UTC | Bound socket |
| --- | --- | --- | --- | --- | --- |
| Baseline | 1516658 | 1517988 | 424418163 | 2026-11-13 10:07:10 | 127.0.0.1:8633 |
| Experiment | 1516674 | 1518019 | 424418328 | 2026-11-13 10:07:11 | 127.0.0.1:8634 |

Before stopping a process, rediscover the listener with `ss -ltnp '( sport = :8633 or sport = :8634 )'`.
Match its PID to `server.json`, `/proc/<pid>/cwd`, `/proc/<pid>/cmdline` (the absolute checkout's
`.venv/bin/python`, `example/manage.py`, `runserver`, exact bind, `--noreload`) and field 22 of
`/proc/<pid>/stat` (start ticks). A matching old PID alone is insufficient. If anything conflicts, stop
and report; never signal an unknown port occupant. Only after all identities match, send SIGTERM to
that PID. Verify its listener disappears, then run the corresponding command above. For detached
operation, use the same direct command with stdout/stderr appended to the same log and record the
new PID/start identity in `server.json`. Check the listener belongs to it and GET the login page.
If a server has disappeared, start it only after the same port-free check. Do not reset or reseed data.

Both recorded processes were verified against cwd/cmdline/start ticks and their actual `ss` listeners,
stopped one at a time, restarted and checked by HTTP. A first bind probe encountered TCP TIME_WAIT;
checking for no listener and using SO_REUSEADDR for the probe resolved that harness issue without
signalling any other process. Baseline presentation and distinct data remained available after restart.
Leave both live for the human checkpoint; after evaluation stop only these verified owned processes
unless the maintainer asks to retain them. Preserve all worktrees, environments and data.

Use the repository's documented demo logins in CLAUDE.md. Keep baseline on localhost and experiment
on 127.0.0.1, or use separate browser profiles: different ports alone do not isolate cookies.
Before evaluation, sign in as different roles simultaneously and confirm each page's current user;
logging out of one must leave the other signed in. Then compare the same named customer and role.
Actual Chromium verification at 10:10:28 UTC signed baseline in as Sam and experiment as Alex in the
same browser context, logged baseline out and switched it to Alex, and confirmed experiment remained
Alex. The separate host cookies, not merely the ports, provide isolation.

## Plan 03 comparison evidence

Compared product revisions: experiment `a31c96baf63f4131704ce3578a547dbbd7216503`, baseline
`4f8d0326d63d7974029b7243b1ddbe63cadb625a`. Later runbook-only commits do not change that product.
Both started from seed 633 on 2026-11-13. At 10:11 UTC browser checks created one experiment-only
address named `Phase 06.33 browser check` for customer 4 and confirmed Order #1072 (PK 72).
Baseline still has no such address and Order #1072 remains Draft. This intentional synthetic data
difference proves independence; compare layout with that status difference in mind.

Broad example command: `uv run --no-sync python example/manage.py test django_tabler dashboard sales catalog roastery shipping showcase --parallel 2`
passed 240 tests in 45.819s (47.09s wall), exit 0. System check with `--fail-level WARNING` passed in
0.57s wall. Focused navigation command with `--parallel 2` passed 17 tests in 7.543s (8.68s wall), exit 0.
`--no-sync` preserves the verified existing environment; no package installation was performed.
Shared theme 83 / crispy pack 34 passing results from Plan 01 were reused: `git diff 22dbdcc a31c96b -- src tests/crud_views_tabler tests/crispy_tabler pyproject.toml uv.lock`
was empty, and no relevant unresolved regression remained.

Cached Playwright/Chromium 149.0.7827.55 rendered all 13 approved routes on both hosts at 1280×900 and
375×900. Experiment identity/bar precedes heading/actions; all four links are visible, have the correct
current marker, and wrap at y=184/224 at 375px, with no page or navigation horizontal overflow. At
320px the detail bar also wraps and page width remains 320. Normal clicks and keyboard Tab/Enter
retain customer 4. Show code loads, order badge/actions remain, and real delete modals exclude repeated
identity/nav while keeping the underlying page. Filter, pagination, form save, workflow and Alex/Sam/Kim
role/grant checks were exercised. Written route/timestamp observations and limits are in the upstream
`06.33-EVALUATION.md`; temporary browser files are local, not committed assets.

Suggested flow: compare Details → Orders → Order #1072 → edit/workflow → Addresses → delete/Cancel →
Subscriptions, then narrow to 375px. Sam can access customer 4 but receives 403 for customer 16; Kim
can read both but cannot create an address. Existing narrow order progress labels are cramped equally
in baseline and experiment; the bar does not introduce that presentation limitation.

## Verification commands

Run from the experiment checkout, with the environment unsets above:

```bash
uv run python example/manage.py check --fail-level WARNING
uv run python example/manage.py test sales.tests.test_customer_navigation.CustomerNavigationTests.test_detail_links_follow_same_customer --verbosity 2
uv run python example/manage.py test sales.tests.test_customer_navigation sales.tests.test_customers --parallel 2
uv run --group test pytest tests/crud_views_tabler --ds tests.crud_views_tabler.settings
uv run --group test pytest tests/crispy_tabler
```

The detail tracer passed in 1.461s, then passed its post-commit feedback gate in 1.544s.
Shared theme: 83 passed in 3.62s; crispy pack: 34 passed in 0.17s. All exit 0.
After duplicate-action removal, navigation plus customer regressions: 32 passed in 9.590s with two workers, exit 0.
The existing locked pytest runner is serial (no xdist dependency); Django broad checks use two workers.
The expected preimplementation tracer failed only because the new wrapper was absent; the duplicate-action
test failed before removal on the old action arrays. These are test-first checks, not outstanding defects.

## Boundaries

The implemented experiment covers all 13 approved full-page routes; no subscription detail route exists.
Customer create/update, top-level collections, full-page delete,
modal contents and unrelated custom actions are excluded. No new routes, dependencies, schema,
generic navigation API, AJAX, embedded children, counts or unsaved-change warning.
Existing full detail properties/summary and document title are preserved. The three replacement actions
are removed only from CustomerDetailView's two action arrays; ViewSet button definitions remain.
No source reset, dependency edits, main merge or upstream product changes are authorized.
Keep this branch and baseline even after favorable feedback. User comparison remains a separate gate.
