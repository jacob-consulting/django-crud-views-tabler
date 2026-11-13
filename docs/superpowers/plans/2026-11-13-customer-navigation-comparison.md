# Customer navigation comparison — Phase 06.33

## Accepted comparison and outcome — 2026-11-13

The maintainer's exact responses were **"pass"**, then **"keep downstream"**. Task05-02 is accepted
with no requested correction or additional evidence. No preferred placement or personal device/browser
inspection was stated. Keep the existing header selection and isolated experiment branch; this outcome
does not authorize an upstream API, merge, push, deletion or issue closure. Earlier pending-review text
below is retained as the historical checkpoint record.

Continuation verified both local server records against PID/cwd/full command/start ticks and listeners:
experiment1710334/start425361517 on9000; baseline1517988/start424418163 on8633. Both matched and stayed
running. Actual Chromium at13:33:49–50UTC confirmed customer4 Details200 on both hosts, served header
identity/navigation before heading in the experiment, and no experimental markers on baseline.
The selector remains byte-identical to committed header. No restart or product/data changes were needed.
The checkpoint command `uv run --no-sync python example/manage.py test sales.tests.test_customer_navigation_layouts --parallel 2`
passed37 tests in20.407s with clean system checks. Previous full evidence remains at product1f85d3f;
this continuation adds only live availability/selection and the required layout regression check.

Theme-controlled composition remains useful downstream, with the explicit route/access helper retained
for the demonstrated pinned sibling-permission mismatch. Both layouts and the documented comparison
procedure stay available. The outcome supplies no new reusable upstream API requirement.

## Current checkpoint — Plan 05, 2026-11-13 12:44 UTC

Both placements were inspected with real cached Chromium 149.0.7827.55 at 1280×900 and 375×900 on all
thirteen participating routes, plus 320px wrapping. The **header default is restored and served** at
http://127.0.0.1:9000/customer/4/detail/ . Original baseline remains independently available at
http://localhost:8633/customer/4/detail/ . Login reference: this repository's CLAUDE.md, Conventions.
Actual maintainer feedback, preferred layout and keep/propose/discard outcome remain pending.

Product revision for both layouts: `1f85d3f5dd56a298c3361543bb6eb79f8f4d19cb`; baseline:
`4f8d0326d63d7974029b7243b1ddbe63cadb625a`. This runbook-only update changes no product source.
Fresh focused navigation/layout/access/orders: **100 passed, 33.707s**; broad demo: **285 passed, 64.380s**;
both used `--parallel 2` and `uv run --no-sync`. System checks clean. Plan 04's shared-theme 83 and crispy-pack
34 passes are reused: `git diff 1f85d3f HEAD -- src tests/crud_views_tabler tests/crispy_tabler pyproject.toml uv.lock`
and the corresponding working-tree comparison were empty. The exact fresh check commands and evidence
are in upstream 06.33-EVALUATION.md / 06.33-VALIDATION.md; no upstream product files changed.
After exact header restoration, the standalone layout suite also passed **37 tests in20.336s** (21.52s wall).

Owned runtime records remain local in each checkout's `.local/customer-navigation-06-33/server.json`.
Baseline PID **1517988**, start ticks **424418163**, was rechecked and left unchanged. Experiment PID
**1710334**, start ticks **425361517**, serves the restored header after the verified restart at 12:44:24 UTC.
The historical PID1556992 record was stale: an identified separate development listener PID1633465 had
occupied 9000. Under the maintainer's existing explicit instruction to replace anything on that port,
its cwd/command/start identity was checked before stopping only that listener. No other port was affected.
Experiment was started direct Python as PID1705435, switched to card through PID1708531, then restored
through PID1710334. Each later restart checked recorded PID/cwd/cmdline/start ticks/listener first.
Fresh browser checks confirmed the served variant after each switch, including restored header identity,
navigation, Show code and order title/actions/CSRF. Rediscover identity on resume; these numbers can become stale.

The exact one-line switch is still the literal `header.html` → `card.html` extends change documented below.
No Python, URL or environment switch exists. The agent can assist live on port9000: preserve selector bytes,
make that one-line edit, verify ownership, restart the owned direct-python server, confirm a real page has
`data-customer-navigation-card`, and update server.json. Restore the saved header bytes and repeat the
owned restart/browser check after comparison. Temporary selector changes were not committed.
Local `05-switch.py` is a disposable, guarded helper for these two selections; inspect its identity checks
before reuse. It is excluded from git along with runtime/browser records, captures and credentials.

Current intentional synthetic data differences: experiment has addresses `Plan 05 header browser check`
and `Plan 05 card browser check` in addition to the earlier `Phase 06.33 browser check`. Header workflow
inspection advanced order50 Shipped→Delivered; card inspection advanced order72 Confirmed→Roasted.
Both submitted enabled transitions through the browser. Baseline order50 remains Shipped and order72 Draft;
none of the experiment-only addresses appears there. No reset/reseed occurred. The full route matrix,
including order72's editable form, was checked **before** its Roast transition; that edit URL now correctly
returns403. Use address/subscription forms or order Create to inspect current forms, and order72 workflow
as Alex for its remaining permitted transition. Kim cannot access that now-Roasted workflow screen.

Desktop/narrow placement and wrapping, same-customer links/current section, keyboard Tab/Enter, Show code,
filters, live top-level page2, form validation/save, granted/denied roles and workflow, modal open/Cancel and
excluded pages were observed. Card puts navigation after heading/actions and before filters/content;
header puts it above heading/actions. At375px Details content begins at y420 with header versus y479 with
card (baseline y348); card therefore uses59px more vertical space than header in this measured page.
At320px both wrap into two lines; card wraps after Orders, header after Addresses. No document overflow.
The pre-existing crowded order progress labels remain in both versions; native focus is visible but faint.
Only Chromium emulation was checked; physical devices, other engines and formal accessibility audit were not.

Local evidence files use the `05-` prefix. `05-card-before-transition.json` contains the successful full
route/viewport matrix and interaction records before the state mutation. Its final harness assertion expected
Kim's workflow GET to stay200 while the concurrent Roast mutation made it403. Follow-up `05-card-final.json`
and `05-card-mutations.json` confirm the actual denial and unchanged forbidden-transition state; no product
fix was needed. A redundant full rerun then correctly hit403 on order72 edit. Historical `05-card.json`
contains that stopped attempt, not the canonical full matrix. A standalone layout-suite attempt while the
temporary card selector was active failed the explicit committed-header assertion; run automated default
restoration checks after returning the selector to header. No packages or tests were changed to hide these facts.

Maintainer review remains a blocking human step. Compare orientation, section switching, template control,
narrow-screen height/wrapping, retained actions/modal behavior and ongoing maintenance. The agent can switch
the live layout on request. Record actual reservations and outcome preference before any issue publication.

## Two template placements — Plan 04 handoff

Plan 04 adds two compositions, selected **only** by the literal extends target in
`example/templates/project/crud_views.html`. The committed default is
`{% extends "project/customer_navigation/header.html" %}`. The alternative is
`{% extends "project/customer_navigation/card.html" %}`. Both use the same private helper, identity and section
partials. Header places sections below identity and above heading/actions; card leaves identity there and
places sections in a standalone card header before filters/content. Existing content cards stay separate.

The following is the later live comparison procedure, not a record of browser checks performed in Plan 04.
Use one experiment URL sequentially under the named layouts:
http://127.0.0.1:9000/customer/4/detail/ beside independent baseline
http://localhost:8633/customer/4/detail/. Earlier Plan 03 screenshots/observations and port 8634 references
below are historical. Port 9000 and the current local server records govern the new comparison.

From the experiment checkout, first verify branch `experiment/customer-section-navigation-06-33`, a clean
selector, and its literal default. Preserve the exact contents before changing anything:

```bash
git diff --exit-code -- example/templates/project/crud_views.html
cat example/templates/project/crud_views.html
cp example/templates/project/crud_views.html .local/customer-navigation-06-33/selector-before-comparison.html
```

Inspect the header variant first. Then change only the extends target and show the one-line diff:

```bash
sed -i 's@project/customer_navigation/header.html@project/customer_navigation/card.html@' example/templates/project/crud_views.html
git diff -- example/templates/project/crud_views.html
```

There is no query, environment, settings or Python placement switch. Django's default cached loader can retain
the compiled selector, and the owned server uses `--noreload`: editing the file alone does not prove which
variant a browser receives. Before each comparison, read `.local/customer-navigation-06-33/server.json`.
Verify its PID against `/proc/<pid>/cwd`, `/proc/<pid>/cmdline`, field 22 of `/proc/<pid>/stat` and
`ss -ltnp '( sport = :9000 )'`. All must identify this experiment's direct `.venv/bin/python` process,
`example/manage.py runserver 127.0.0.1:9000 --noreload` and recorded start ticks. Do not signal anything on a
mismatch. When reload is needed, terminate only that verified PID, confirm its listener has disappeared,
then restart from the same experiment cwd with the existing environment/data:

```bash
.venv/bin/python example/manage.py runserver 127.0.0.1:9000 --noreload
```

For detached operation retain the existing log destination, record the new PID/start ticks/cwd/command/revision
in the adjacent `server.json`, and verify the listener and login GET. Never reset or reseed the database.
Leave baseline localhost:8633 running independently; its own server.json is a separate process identity.
After reload, authenticate with the documented synthetic demo accounts and verify the *served* selection:
header has one `data-customer-navigation` landmark before the heading; card has it inside main under
`data-customer-navigation-card`, with one identity remaining in the page header. Check all thirteen routes,
roles and desktop/narrow widths and record variant, route, viewport, actor, revision, selector diff, timestamp
and cache/process verification. The automated test matrix is not browser evidence.

Restore the exact saved selector after comparison, check that it matches the committed header default, and
repeat the verified owned-process restart/cache check so the served page also returns to header:

```bash
cp .local/customer-navigation-06-33/selector-before-comparison.html example/templates/project/crud_views.html
git diff --exit-code -- example/templates/project/crud_views.html
cat example/templates/project/crud_views.html
```

If a pre-existing selector edit is present, preserve it and reconcile it before starting; do not overwrite it
or assume a stale saved copy is current. Do not commit temporary layout selections. The default source and
runtime restoration, fresh browser observations, actual maintainer feedback and issue outcome belong to Plan 05.

Automated verification from the experiment uses the existing environment only:

```bash
uv run --no-sync python example/manage.py test sales.tests.test_customer_navigation_layouts sales.tests.test_customer_navigation --parallel 2
uv run --no-sync --group test pytest tests/crud_views_tabler --ds tests.crud_views_tabler.settings
uv run --no-sync --group test pytest tests/crispy_tabler
```

Django uses two workers; the locked pytest environment has no xdist and remains serial. Tests override only
the selector through Django's [locmem loader](https://docs.djangoproject.com/en/6.0/ref/templates/api/#django.template.loaders.locmem.Loader)
with filesystem/app loaders retained, and use
[override_settings](https://docs.djangoproject.com/en/6.0/topics/testing/tools/#overriding-settings) for engine/cache restoration.
The test override is not a production placement setting.

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

## Live port update — 2026-11-13 10:34 UTC

At the maintainer's request, the experiment moved from 8634 to **9000**:
http://127.0.0.1:9000/customer/4/detail/ . Baseline remains on localhost:8633.
The prior source-checkout port-9000 runserver family was explicitly stopped, as
authorized, and the owned experiment PID1518019 was stopped before moving it.
New owned PID1556992 serves `127.0.0.1:9000 --noreload` from the same experiment
cwd/venv/database. Exact current start ticks/command are in the experiment's
`.local/customer-navigation-06-33/server.json`. Listener identity matched; login
GET returned200 and unauthenticated customer GET returned302. Restart using the
recorded direct-python command with port9000. Earlier browser evidence remains
historical evidence at8634; no product or database changes accompany this move.
Maintainer feedback/outcome remains pending.
