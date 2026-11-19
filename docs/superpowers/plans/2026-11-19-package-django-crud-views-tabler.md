# Package as django-crud-views-tabler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn this repo into the publishable distribution `django-crud-views-tabler` (packages `crud_views_tabler` +
`django_tabler`), with nox matrix, GitHub Actions CI, Read the Docs, a Render demo and a publish workflow, all
mirroring `../django-crud-views`.

**Architecture:** Copy upstream's tooling file by file and adapt names and paths: hatchling + sdist allowlist checked
by `scripts/check_dist.py`, nox sessions that test the *installed* distribution, hash-pinned CI requirements, mkdocs
on Read the Docs, `render.yaml` + API-driven `demo.yml`. Until django-crud-views 1.0.0rc1 is on PyPI, every
non-local install takes crud-views from its GitHub `main`.

**Tech Stack:** Python 3.12–3.15, Django 5.2/6.0/6.1, hatchling, nox (uv backend), pytest + pytest-django,
ruff, pre-commit, bump-my-version, mkdocs (readthedocs theme), GitHub Actions, Codecov, Render, gunicorn, whitenoise,
django-ratelimit.

**Spec:** `docs/superpowers/specs/2026-11-19-package-django-crud-views-tabler-design.md` (Task 6 moves it to
`superpowers/specs/`).

**Upstream reference (read-only):** `/home/alex/projects/alex/django-crud-views`. "Port X" below means: copy the
upstream file, rename `crud_views*`/`examples/bootstrap5`/`project.` to this repo's names, drop what refers to
features this plan excludes (Django 4.2, crispy/manage floor sessions, JS, Sonar, readme-examples).

## Global Constraints

- Distribution name `django-crud-views-tabler`; version `0.1.0`; license MIT; author Alexander Jacob (as upstream).
- Repo URL `https://github.com/jacob-consulting/django-crud-views-tabler`; docs
  `https://django-crud-views-tabler.readthedocs.io/en/latest/`.
- `requires-python = ">=3.12"`. Matrix: Python 3.12, 3.13, 3.14, 3.15 × Django 5.2, 6.0, 6.1 (12 rows, none skipped).
- Runtime dependencies: `django>=5.2`, `django-crud-views>=0.30`, `crispy-bootstrap5>=2026.9`, plus whatever `src/`
  imports directly. No `crispy` extra. Nothing example-only.
- Until crud-views 1.0.0rc1 is on PyPI: nox, CI and Render install
  `django-crud-views[workflow,polymorphic,guardian,ordered] @ git+https://github.com/jacob-consulting/django-crud-views@main`.
  Local dev keeps `[tool.uv.sources]` sibling paths.
- `publish.yml` must refuse to publish while the declared crud-views floor is below `1.0.0rc1`.
- Tests always run against the installed distribution, never `src/` on the path.
- `django_tabler` never imports `crud_views`. App code under `example/` never imports either package.
- Nothing from `~/projects/tabler/` (licensed archives) enters the repo, wheel or sdist.
- `../django-crud-views` and `../django-crud-views-extensions` are read-only. A crud-views problem found here is
  worked around and logged in the findings log in the same commit (CLAUDE.md convention).
- Ruff: upstream's configuration (line length 120, `select = ["E","F","I","UP","B","C4","SIM","RUF"]`).

## Review Focus

1. **A wheel without templates or static files.** `pip install` of the wheel must render pages; Task 2's
   `check_dist.py` requires named template/static members, not just an allowlist.
2. **Tests silently importing the checkout.** A packaging defect hides when `src/` is importable; Task 3 asserts the
   installed origin of both packages before each suite.
3. **The demo restarting on a database that already has data.** `seed_demo` refuses then and would fail the start
   command; Task 7 starts with `seed_demo --reset` and guards `seed_demo_showcase`, and tests `--reset` on an empty
   database.
4. **DEBUG=False with manifest static storage.** A template that references a static path missing from the manifest
   500s only in the demo; Task 7 renders the login page and a crud_views list under `settings_demo` after
   `collectstatic`.
5. **A tag pushed before crud-views 1.0.0rc1 exists.** The release would install a git `main` nobody can reproduce;
   Task 5's floor guard fails the publish job, with a test.

---

### Task 1: Ruff and pre-commit, one reformatting commit

**Files:**
- Modify: `pyproject.toml` (add `[tool.ruff]`, `[tool.ruff.format]`, `[tool.ruff.lint]`, per-file ignores)
- Create: `.pre-commit-config.yaml` (port upstream, ruff `v0.17.1`), `.git-blame-ignore-revs`
- Modify: every `*.py` touched by `ruff format` / `ruff check --fix`

- [ ] **Step 1:** Add the ruff sections from upstream `pyproject.toml`. `extend-exclude = ["superpowers/**",
  "docs/superpowers/**"]`; per-file ignores `"tests/**"`, `"example/**"`, `"**/migrations/*"` = `["RUF012"]`.
- [ ] **Step 2:** Run `uvx ruff@0.17.1 format .` then `uvx ruff@0.17.1 check --fix .`.
- [ ] **Step 3:** Fix what `ruff check .` still reports by hand. Do not add blanket ignores; a per-line `noqa`
  needs a reason comment.
- [ ] **Step 4:** Verify nothing changed behaviourally: `task test` passes (all three suites and the check).
- [ ] **Step 5:** Commit as "Style: ruff format and fixes"; then write that commit's hash into
  `.git-blame-ignore-revs` with a comment, add `.pre-commit-config.yaml`, commit "Lint: pre-commit config, blame
  ignore".

### Task 2: Packaging

**Files:**
- Modify: `pyproject.toml`, `src/crud_views_tabler/__init__.py`, `src/django_tabler/__init__.py`, `.gitignore`
  (add `.nox/`, `coverage*.xml`, `.coverage`, `site/`)
- Create: `LICENSE` (MIT, as upstream), `CHANGELOG.md`, `scripts/check_dist.py` (port)
- Move: `src/django_tabler/tests.py` → `tests/django_tabler/test_django_tabler.py`; create
  `tests/django_tabler/__init__.py`, `tests/django_tabler/settings.py`
- Delete: `src/tabler_test.egg-info/`
- Test: `tests/django_tabler/test_package.py`

**Interfaces:**
- Produces: `crud_views_tabler.__version__ == django_tabler.__version__ == "0.1.0"`; extras `examples`, `test`,
  `dev`; `scripts/check_dist.py <dist-dir>` exits 0/1; test settings module `tests.django_tabler.settings`.

- [ ] **Step 1: Write the failing test** `tests/django_tabler/test_package.py`:

```python
from importlib.metadata import version

import crud_views_tabler
import django_tabler


def test_versions_match_distribution():
    assert version("django-crud-views-tabler") == crud_views_tabler.__version__ == django_tabler.__version__


def test_django_tabler_does_not_import_crud_views():
    # run in a subprocess: python -I -c "import django_tabler, sys; ..." after django.setup() with
    # tests.django_tabler.settings; assert "crud_views" not in sys.modules
    ...
```

  The second test's body: a subprocess that sets `DJANGO_SETTINGS_MODULE=tests.django_tabler.settings`, runs
  `django.setup()`, imports every module under `django_tabler` (`pkgutil.walk_packages`, skipping
  `django_tabler.crispy` only if it needs crispy apps not installed in those settings), and asserts no
  `crud_views*` key in `sys.modules`.
- [ ] **Step 2:** Move `src/django_tabler/tests.py`. `tests/django_tabler/settings.py` = the crispy settings plus
  `django.contrib.messages`, `django.contrib.sessions` and whatever the moved tests need (they ran under the
  example's settings before; find out by running them).
- [ ] **Step 3: Run to verify failure:** `uv run --group test pytest tests/django_tabler --ds tests.django_tabler.settings`
  → FAIL (`PackageNotFoundError: django-crud-views-tabler`).
- [ ] **Step 4: Rewrite `pyproject.toml`** from upstream's shape with the Global Constraints values:
  - classifiers: Development Status 3 - Alpha, Framework Django 5.2/6/6.0/6.1, Python 3.12–3.15; `[project.urls]`.
  - `examples` = `django-crud-views[workflow,polymorphic,guardian,ordered]`, `django-crud-views-extensions>=0.3.3`,
    `pygments`. `test` = upstream's `test` list minus `polib`/`django-pipeline`, plus `crispy-bootstrap5==2026.9`
    (the parity pin; keep `CRISPY_BOOTSTRAP5_VERSION` in sync). `dev` = upstream's `dev`.
  - Remove `[dependency-groups]`; local `uv sync --extra examples --extra test --extra dev` replaces it (update
    `Taskfile.yaml` `install`, and `test`'s `uv run --group test` → plain `uv run`, accordingly). Keep `[tool.uv.sources]`.
  - hatchling: wheel `packages = ["src/crud_views_tabler", "src/django_tabler"]`; sdist `only-include` = `src`,
    `tests`, `docs`, `example`, `noxfile.py`, `README.md`, `CHANGELOG.md`, `LICENSE`, `pyproject.toml`; exclude
    `example/db.sqlite3`, `example/media`, `__pycache__`.
  - `[tool.bumpversion]` as upstream, files: `pyproject.toml`, both `__init__.py`, `README.md`, `docs/index.md`
    ("Current version: {version}"; the README/docs lines arrive in Task 6, so add those two entries there).
  - `[tool.coverage.*]` as upstream with `source = ["crud_views_tabler", "django_tabler"]`, no `fail_under`.
- [ ] **Step 5: `scripts/check_dist.py`:** port; `WHEEL_PACKAGES = {"crud_views_tabler", "django_tabler"}`,
  `SDIST_ALLOWED` matches `only-include`. Add `WHEEL_REQUIRED` — fail if any is missing:
  `django_tabler/templates/django_tabler/base.html`, `django_tabler/templates/crispy_tabler/field.html`,
  `django_tabler/static/django_tabler/layout-switch.js`, `crud_views_tabler/templates/crud_views_tabler/page.html`,
  `crud_views_tabler/static/crud_views_tabler/crud_views_tabler.css`,
  `crud_views_tabler/static/crud_views_tabler/tabler-adapters.js`. No `tests.py`, `*.pyc` or `__pycache__` in the
  wheel.
- [ ] **Step 6: Verify:** `uv sync --extra examples --extra test --extra dev`; the Step 3 command passes;
  `uv build --out-dir /tmp/…/dist && python scripts/check_dist.py /tmp/…/dist` exits 0; `task test` passes.
- [ ] **Step 7: Commit** "Package: django-crud-views-tabler 0.1.0, hatchling, check_dist".

### Task 3: One test runner and the nox sessions

**Files:**
- Create: `example/pytest.ini`, `noxfile.py`
- Modify: `Taskfile.yaml` (`test`), `pyproject.toml` (`[tool.pytest.ini_options]` if needed)

**Interfaces:**
- Consumes: Task 2 extras and `scripts/check_dist.py`.
- Produces: nox sessions `tests-<py>(django='<dj>')`, `examples-<py>(django='<dj>')`, `package`, `docs` (docs
  session added in Task 6). Coverage files `coverage-py<py>-dj<dj>.xml`. Constants in `noxfile.py`:
  `PYTHON_VERSIONS = ["3.12", "3.13", "3.14", "3.15"]`, `DJANGO_VERSIONS = ["5.2", "6.0", "6.1"]`,
  `CRUD_VIEWS = "django-crud-views[workflow,polymorphic,guardian,ordered] @ git+https://github.com/jacob-consulting/django-crud-views@main"`.

- [ ] **Step 1:** `example/pytest.ini`: `DJANGO_SETTINGS_MODULE = config.settings`, `pythonpath = .`,
  `addopts = --strict-markers`, `python_files = tests.py test_*.py`.
- [ ] **Step 2: Verify** the example's tests pass under pytest from `example/`:
  `cd example && uv run pytest` — same test count as `manage.py test dashboard sales catalog roastery shipping
  showcase` (compare the numbers; a lower count means a file pattern is missing).
- [ ] **Step 3: `noxfile.py`** (port upstream's `tests`, `examples`, `package`):
  - `tests`: `session.install(f"django~={django}.0", CRUD_VIEWS, ".[test]")` in **one** call (so the git
    crud-views is the one resolved); run the installed-origin check for both `crud_views_tabler` and
    `django_tabler` with `PYTHONPATH=""`; then three pytest runs — `tests/crispy_tabler --ds
    tests.crispy_tabler.settings`, `tests/crud_views_tabler --ds tests.crud_views_tabler.settings`,
    `tests/django_tabler --ds tests.django_tabler.settings` — with `--cov --cov-append`, the last one writing
    `--cov-report=xml:coverage-py{py}-dj{dj}.xml`.
  - `examples`: install `f"django~={django}.0"`, `CRUD_VIEWS`, `".[examples,test]"` in one call; in `example/`:
    `pytest`, then `python manage.py check --fail-level WARNING`.
  - `package`: as upstream.
  - A comment at `CRUD_VIEWS`: remove when crud-views 1.0.0rc1 is on PyPI (and then raise the floor, Task 5).
- [ ] **Step 4:** `Taskfile.yaml`: `test` runs the three package suites + example pytest + check through `uv run`
  (fast local path, sibling checkouts); add `test:matrix` → `uvx nox`.
- [ ] **Step 5: Verify:** `uvx nox -s "tests-3.14(django='6.1')" "examples-3.14(django='6.1')" package` passes;
  the origin check prints a `site-packages` path.
- [ ] **Step 6: Commit** "Tests: pytest for the example, nox sessions".

### Task 4: Pass the whole matrix

**Files:** whatever the failures point at (expected: `src/**`, `example/**`, tests, possibly migrations); the findings
log for crud-views-caused issues.

- [ ] **Step 1: Run** `uvx nox -s tests examples` (all 24 sessions). Record failures per row in the commit
  message or a scratch list.
- [ ] **Step 2: Fix** in order: Python 3.12/3.13 syntax and semantics (deferred annotations, PEP 758 `except`,
  newer stdlib APIs), then Django 5.2/6.0 API differences, then 6.1-generated migrations that do not load on 5.2.
  Prefer code that works on all rows over version branches; a version branch needs a comment naming the version.
- [ ] **Step 3: Verify:** all 24 sessions pass (Python 3.15 rows may need `uv python install 3.15`; if 3.15 is
  unavailable locally, say so in the task report — CI runs it with `allow-prereleases`).
- [ ] **Step 4: Commit** per fix group ("Compat: Python 3.12 …", "Compat: Django 5.2 …").

### Task 5: CI workflows and the release floor guard

**Files:**
- Create: `.github/workflows/{tests,lint,docs,publish}.yml`, `.github/requirements/ci.in`,
  `.github/requirements/ci.txt`, `codecov.yml`, `scripts/check_release_floor.py`
- Test: `tests/django_tabler/test_release_floor.py`

**Interfaces:**
- Produces: `scripts/check_release_floor.py [pyproject.toml]` → exit 0 when the `django-crud-views` requirement's
  lower bound is `>= 1.0.0rc1`, else exit 1 with a message naming the floor. Uses `tomllib` and
  `packaging.requirements`/`packaging.version`.

- [ ] **Step 1: Write the failing test** (`tmp_path` pyproject files, run the script via `subprocess` with
  `sys.executable`):

```python
@pytest.mark.parametrize(("spec", "ok"), [
    ("django-crud-views>=0.30", False),
    ("django-crud-views>=1.0.0rc1", True),
    ("django-crud-views>=1.0.0", True),
    ("django-crud-views (>=1.0.0rc1)", True),
    ("django-crud-views", False),
])
def test_release_floor(tmp_path, spec, ok): ...
```

  Also: the repo's own `pyproject.toml` fails the guard today (asserts exit code 1), so the test documents the
  current pre-release state; the release commit flips this assertion.
- [ ] **Step 2: Run** `uv run pytest tests/django_tabler/test_release_floor.py --ds tests.django_tabler.settings` → FAIL.
- [ ] **Step 3: Implement** `scripts/check_release_floor.py`.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Workflows** (port upstream, pin the same action SHAs/versions):
  - `tests.yml`: push to main + PRs; matrix `python-version: ["3.12","3.13","3.14","3.15"]`,
    `allow-prereleases: true`; `nox -s` the three `tests-…` and three `examples-…` sessions of the row; Codecov
    upload as upstream.
  - `lint.yml`: ruff format check, ruff check, `nox -s package`.
  - `docs.yml`: `mkdocs build --strict` with hashed `docs/requirements.txt` (file lands in Task 6; this workflow is
    added here and goes green after Task 6).
  - `publish.yml`: tags `v*`; jobs tests, docs, lint, then `publish` (environment `pypi`, `id-token: write`) whose
    first step is `python scripts/check_release_floor.py`, then build, `check_dist.py`, `pypa/gh-action-pypi-publish`.
  - `ci.in` as upstream (nox, uv, ruff `>=0.17.4,<0.18`, build) plus `packaging`; compile `ci.txt` with the command
    in its header.
  - `codecov.yml` as upstream, `after_n_builds: 4`.
- [ ] **Step 6: Verify:** `uvx actionlint` (or `actionlint` via `go run`/docker if not installed) on the four
  workflows reports nothing; `uvx nox -s package` passes.
- [ ] **Step 7: Commit** "CI: tests, lint, docs, publish workflows; release floor guard".

### Task 6: Docs restructure, Read the Docs, README

**Files:**
- Move: `docs/crud_views_upstream_findings_roastery.md`, `docs/crud_views_upstream_questions.md`,
  `docs/crud_views_upstream_status.md`, `docs/crud_views_tooltips.md` → `dev/`; `docs/superpowers/` →
  `superpowers/`
- Create: `mkdocs.yml`, `.readthedocs.yaml`, `docs/requirements.in`, `docs/requirements.txt`, and the pages below
- Move/adapt: `docs/crud_views_tabler.md` → `docs/theme_internals.md`; `docs/crispy_tabler_coverage.md` →
  `docs/crispy_tabler.md` (merged with a usage section)
- Modify: `README.md`, `CLAUDE.md`, `noxfile.py` (add `docs` session), `pyproject.toml` (bumpversion README/docs
  entries, mkdocs extra paths in ruff exclude if needed), `example/config/views.py` (`THEME_DOC_URL`),
  `example/dashboard/tests.py:572`, `scripts/vendor_templates.py` and any other reference to moved paths

**Interfaces:**
- Produces: `THEME_DOC_URL = "https://django-crud-views-tabler.readthedocs.io/en/latest/theme_internals/"`.

- [ ] **Step 1: Update the failing assertion first:** `example/dashboard/tests.py:572` expects the new
  `THEME_DOC_URL`; run it → FAIL; change `THEME_DOC_URL` → PASS.
- [ ] **Step 2: Move the files** with `git mv`; fix every reference (`grep -rn "docs/crud_views_upstream\|docs/crud_views_tooltips\|docs/superpowers\|docs/crud_views_tabler\|docs/crispy_tabler_coverage" .`
  must return only historical mentions inside `dev/` and `superpowers/`).
- [ ] **Step 3: mkdocs:** port `mkdocs.yml` (site_name "Django CRUD Views Tabler", readthedocs theme,
  awesome-pages, same extensions, `repo_url` the new repo, `edit_uri: blob/main/docs/`), `.readthedocs.yaml`,
  `docs/requirements.in/.txt` (same as upstream). Links from docs to `dev/` files are absolute GitHub URLs.
- [ ] **Step 4: Pages** (content from CLAUDE.md, the README and the moved docs; each page shows real settings/template
  snippets from `example/`):
  `index.md` (what it is, a screenshot, "Current version: 0.1.0", links), `installation.md` (pip, `INSTALLED_APPS`
  order with `crud_views_tabler` before `crud_views`, crispy settings, `CRUD_VIEWS_EXTENDS`), `branding.md`
  (`django_tabler/includes/*` overrides, `nav_menu.html` with `nav_layout`), `layouts.md` (layout switch,
  `layout_defaults.html`, the primary-colour gap), `icons.md` (`{% load tabler %}`, `tabler:<name>`, W001, adding
  paths), `crispy_tabler.md`, `theme_internals.md`, `demo.md` (URL from `vars.DEMO_URL` placeholder, demo accounts),
  `development.md` (local setup with sibling checkouts, `task`, nox, vendoring, release steps incl. raising the
  crud-views floor and removing `CRUD_VIEWS`, the account setup list from Task 8).
- [ ] **Step 5:** `noxfile.py` `docs` session: install `-r docs/requirements.txt`, `mkdocs build --strict`.
- [ ] **Step 6: README** for PyPI: what it is, `pip install django-crud-views-tabler`, minimal settings, links to
  docs/demo/repo, "Current version: 0.1.0", "Run the example" (the current Task/uv section). Add the two
  bumpversion entries.
- [ ] **Step 7: CLAUDE.md:** new name, paths (`dev/`, `superpowers/`), commands (`uv sync --extra …`, nox), ruff
  instead of "no linter", the matrix, the git-main crud-views rule.
- [ ] **Step 8: Verify:** `uvx nox -s docs` passes (strict); `task test` passes; `uvx nox -s package` passes
  (`docs` stays in the sdist, `dev/` and `superpowers/` do not).
- [ ] **Step 9: Commit** "Docs: user guide on Read the Docs; internal notes to dev/, specs to superpowers/".

### Task 7: Render demo

**Files:**
- Create: `example/config/settings_demo.py`, `example/config/urls_demo.py`, `example/config/boot.py`,
  `example/config/ratelimit.py` (all ported from upstream `examples/bootstrap5/project/`), `requirements/demo.txt`,
  `render.yaml`, `.github/workflows/demo.yml`
- Test: `example/config/test_demo.py`, `example/config/test_boot.py`, `example/config/test_ratelimit.py` (ported),
  plus the additions below; `example/dashboard/tests.py` (reset on empty DB)
- Modify: `noxfile.py` (`examples` also installs `-r requirements/demo.txt`), `example/pytest.ini` if test discovery
  needs `config/test_*.py`

**Interfaces:**
- Produces: `config.settings_demo` (requires env `SECRET_KEY`; reads `RENDER_EXTERNAL_HOSTNAME`),
  `config.urls_demo.urlpatterns` (local patterns minus `admin/`), header `X-Demo-Boot`, `DEMO_WRITE_RATES = ("30/m",
  "300/d")`.

- [ ] **Step 1: Port the tests** (`config.` instead of `project.`), plus:
  - `test_seed_demo_reset_on_empty_database`: `call_command("seed_demo", "--reset")` on an empty test DB succeeds
    and creates users alex/sam/kim.
  - `test_demo_renders_with_manifest_storage`: with `settings_demo` values (`DEBUG=False`, whitenoise manifest
    storage) after `call_command("collectstatic", interactive=False)` into a `tmp_path` `STATIC_ROOT`, GET
    `/accounts/login/` → 200, and logged in as a seeded user, GET a crud_views list page (e.g. the customer list)
    → 200.
  - `test_admin_not_mounted`: under `urls_demo`, `/admin/` → 404.
- [ ] **Step 2: Run** `cd example && uv run pytest config` → FAIL (modules missing).
- [ ] **Step 3: Implement** the four modules as upstream. `settings_demo` also sets `ALLOWED_HOSTS`/
  `CSRF_TRUSTED_ORIGINS` from `RENDER_EXTERNAL_HOSTNAME` only (not the local Cloudflare host), `CRUD_VIEWS_MANAGE_ACCESS_TRACE = False`.
- [ ] **Step 4: `requirements/demo.txt`:** gunicorn>=23, whitenoise>=6.9, django-ratelimit>=4.1, and the
  `CRUD_VIEWS` git requirement with the same "remove at 1.0.0rc1" comment.
- [ ] **Step 5: `render.yaml`:** port; service `django-crud-views-tabler-demo`; build
  `pip install ".[examples]" -r requirements/demo.txt && cd example && python manage.py collectstatic --noinput`;
  start `cd example && python manage.py migrate --noinput && python manage.py cv_manage_group && python manage.py
  seed_demo --reset && (python manage.py shell -c "import sys; from showcase.models import ShowcaseItem;
  sys.exit(0 if ShowcaseItem.objects.exists() else 1)" || python manage.py seed_demo_showcase) && gunicorn
  config.wsgi --workers 1 --bind 0.0.0.0:$PORT`; `healthCheckPath: /accounts/login/`; env
  `DJANGO_SETTINGS_MODULE=config.settings_demo`, `SECRET_KEY` generated, `PYTHON_VERSION=3.14`.
- [ ] **Step 6: `demo.yml`:** port; smoke test uses `/accounts/login/`. The `workflow_dispatch` deploy deploys the
  dispatched ref's commit (`$GITHUB_SHA`), so running it on `main` puts the demo live before v0.1.0.
- [ ] **Step 7: Verify:** `cd example && uv run pytest` passes; a manual run:
  `SECRET_KEY=x RENDER_EXTERNAL_HOSTNAME=localhost DJANGO_SETTINGS_MODULE=config.settings_demo` with a fresh
  `DATABASES` file runs the render.yaml start command twice in a row (second run proves the restart path) and
  `curl -I localhost:$PORT/accounts/login/` shows 200 and `X-Demo-Boot`.
- [ ] **Step 8: Commit** "Demo: Render blueprint, demo settings, deploy workflow".

### Task 8: History scan and the transfer (stops for the user)

**Files:** none in the repo; a report in the scratchpad.

- [ ] **Step 1: Scan** all history (`git log --all --name-only --format=` and `git rev-list --all | git ls-tree -r`)
  for: files under any `tabler-*/` path, `*.zip`, `*.woff*`, `*.png`/`*.jpg`/`*.svg` outside `example/static/acme/`,
  `tabler*.css`/`tabler*.js` copies of the dist, and anything from `~/projects/tabler/` by content hash
  (`git hash-object` the archive files, compare with all blob hashes).
- [ ] **Step 2: Secrets:** `uvx gitleaks detect --log-opts=--all` (or docker); note the Django dev default
  `SECRET_KEY` in `example/config/settings.py` as expected-and-harmless if the demo overrides it.
- [ ] **Step 3: Report to the user and stop.** Any hit means the user decides about rewriting history before going
  public.
- [ ] **Step 4 (user steps, list them in `docs/development.md`, done in Task 6):** rename to
  `django-crud-views-tabler`, transfer to `jacob-consulting`, `git remote set-url origin
  git@github.com:jacob-consulting/django-crud-views-tabler.git`, make public; Read the Docs project; Codecov token
  `CODECOV_TOKEN`; PyPI trusted publisher (environment `pypi`, workflow `publish.yml`); Render service from
  `render.yaml`, secrets `RENDER_API_KEY`, `RENDER_SERVICE_ID`, variable `DEMO_URL`.

## Release (not part of this plan's execution)

When crud-views 1.0.0rc1 is on PyPI: remove `CRUD_VIEWS` from `noxfile.py` and `requirements/demo.txt`, raise the floor
to `django-crud-views>=1.0.0rc1`, flip the repo-state assertion in `test_release_floor.py`, update CHANGELOG, `bump-my-version`
to the release version, push the tag.
