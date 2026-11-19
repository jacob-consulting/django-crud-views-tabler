# Package as django-crud-views-tabler: design

Date: 2026-11-19

## Intent

This repository ("tabler-test", "Acme Admin") becomes the public, PyPI-published distribution
**django-crud-views-tabler**, the Tabler theme for django-crud-views. One distribution ships both packages under
`src/`: `crud_views_tabler` (the theme) and `django_tabler` (page shell, layouts, icons, crispy pack
`crispy_tabler`). The example (Acme Roasters) becomes the public demo.

Why: the theme is ready to be used outside this repo. It should be maintained the same way as django-crud-views, so
the same habits, workflows and release steps apply to both repositories and fixes in one port to the other by copying
files.

Success: a tag `v0.1.0` on `jacob-consulting/django-crud-views-tabler` runs the full matrix, builds the docs, lints,
publishes to PyPI, and deploys the demo to Render, with docs live on Read the Docs.

## Goals

- Packaging, testing, CI, docs and demo mirror django-crud-views (`../django-crud-views`), file by file where possible.
- Supported versions: the upstream matrix **plus Django 6.1, minus Django 4.2**:
  Python 3.12, 3.13, 3.14, 3.15 × Django 5.2, 6.0, 6.1 (12 rows, none skipped).
- The example's tests run on every row of the matrix (an `examples` nox session, as upstream).
- The repo is renamed and transferred to `jacob-consulting/django-crud-views-tabler` with its full history, and made
  public.

## Non-goals

- No change to what the theme renders. Code changes are only those the wider version range forces.
- No JS test suite (two small JS files today), no README-on-three-OSes workflow (upstream's `readme-examples.yml`),
  no SonarCloud. Can be added later.
- No crispy floor session (upstream's `crispy_floor`) or manage-report floor session for now.

## Anti-goals

- Shipping licensed Tabler archive files (`~/projects/tabler/`) or secrets, in the wheel, the sdist, or the public
  history.
- Publishing a release that only works with an unreleased django-crud-views: PyPI release waits for crud-views 0.31.
- Patching or forking django-crud-views or django-crud-views-extensions (both stay read-only for this repo).
- `django_tabler` code importing `crud_views` (the package boundary stays, even though both ship together).

## Constraints and facts found

- Today: `requires-python = ">=3.14"`, `django>=6.1,<6.2`, setuptools build, project name `tabler-test`, no
  LICENSE/CHANGELOG/`__version__`, no linter. The GitHub repo `alexander-jacob/tabler-test` is **private**.
- django-crud-views on PyPI is 0.30.0; the sibling checkout is ~206 commits ahead and the theme needs unreleased
  features (ViewSet Navigation #381, navbar class keys #384/#386). django-crud-views-extensions 0.3.3 on PyPI equals
  its checkout's HEAD.
- django-crud-views `main` still reports version 0.30.0 (`origin/main:pyproject.toml`), although it carries the
  features the theme needs.
- The crispy pack is vendored from crispy-bootstrap5 2026.9 and `test_pack_parity.py` pins that version.
  crispy-bootstrap5 2026.9 and django-crispy-forms 2.7 both require Django >=5.2. This, and Django 4.2's end of
  security support (April 2026), is why 4.2 is dropped. `LoginRequiredMiddleware` (Django 5.1+) therefore needs no
  fallback.
- Migrations under `example/*/migrations/` were generated on Django 6.1 and must load on 5.2.
- Tests today: two pytest suites with their own settings (`tests/crispy_tabler`, `tests/crud_views_tabler`), the
  example apps on Django's test runner, and `src/django_tabler/tests.py` (would ship in the wheel).
- `docs/` holds internal material: the upstream findings log, upstream questions/status, the tooltip notes, and
  `docs/superpowers/` (31 spec/plan files). The findings log references commits of this repo.

## Approaches

- **A. Mirror upstream's tooling file by file (chosen).** hatchling, nox with uv, pip + hash-pinned requirement files
  in CI, mkdocs with the readthedocs theme, ruff + pre-commit, bump-my-version, `render.yaml` + `demo.yml`. Same
  habits in both repos; workflow fixes port by copying. Costs a one-off ruff reformat and a switch from setuptools.
- **B. uv-native** (`uv build`, `uv run` in CI, mkdocs-material). Leaner and closer to this repo's uv/Taskfile
  habits, but drifts from upstream so every CI fix is solved twice. Rejected for that reason.

## Decisions (made with the user)

1. **Matrix:** upstream's plus Django 6.1, minus Django 4.2 (the crispy pack cannot run there, see Constraints);
   the example on every row.
2. **crud-views is a hard dependency.** `pip install django-crud-views-tabler` installs django-crud-views. The
   `crispy` extra is dropped (crud-views already requires django-crispy-forms and crispy-bootstrap5).
3. **Unreleased upstream:** until crud-views 0.31 is on PyPI, nox sessions and the Render build install
   django-crud-views from `git+https://github.com/jacob-consulting/django-crud-views@main`. Local development keeps
   the sibling path sources (`[tool.uv.sources]`). The first PyPI release waits for crud-views 0.31; then the git
   install is removed. *Builder's call (from the review):* because upstream `main` still says 0.30.0, the package
   declares `django-crud-views>=0.30` meanwhile and the release commit raises it to `>=0.31`; `publish.yml` refuses
   to publish when the declared floor is below 0.31.
4. **Repo:** rename and transfer this repo, full history, to `jacob-consulting/django-crud-views-tabler`, then make
   it public, after a history scan for licensed Tabler files and secrets.
5. **Approach A.**

## Design

### Packaging (`pyproject.toml`)

- `name = "django-crud-views-tabler"`, `version = "0.1.0"`, description, author, `license = MIT` + `LICENSE` file,
  `readme`, classifiers (Django 5.2/6.0/6.1, Python 3.12–3.15), `[project.urls]` pointing at
  `jacob-consulting/django-crud-views-tabler` and `django-crud-views-tabler.readthedocs.io`.
- `requires-python = ">=3.12"`; dependencies: `django>=5.2`, `django-crud-views>=0.30` (raised to
  `>=0.31` at release, decision 3), `crispy-bootstrap5>=2026.9` (the vendored baseline) (plus whatever `src/` imports
  directly; nothing example-only).
- Extras mirroring upstream's shape: `examples` (pygments, django-crud-views-extensions, and the crud-views extras the
  example needs: `workflow,polymorphic,guardian,ordered`), `test`, `dev` (ruff, pre-commit, bump-my-version, mkdocs
  set).
- hatchling: wheel packages `src/crud_views_tabler`, `src/django_tabler`; sdist `only-include` allowlist
  (src, tests, docs, example, noxfile.py, README.md, CHANGELOG.md, LICENSE, pyproject.toml) enforced by a ported
  `scripts/check_dist.py`. Templates and static files must be in the wheel.
- `__version__` in both `__init__.py` files; bump-my-version updates pyproject, both `__init__.py`, README and
  `docs/index.md` ("Current version: …"), commits and tags `v{version}`.
- `CHANGELOG.md` started at 0.1.0.
- The `src/tabler_test.egg-info` leftover is deleted.

### Version compatibility work

Make the code, tests and example pass on every matrix row. Known: 6.1-generated migrations must load on 5.2. Anything else found while running the matrix is fixed in this repo, or, if it is a
crud-views problem, logged in `docs/crud_views_upstream_findings_roastery.md` per the existing convention.

### Tests and nox (`noxfile.py`)

- One runner: pytest. The example apps' Django `TestCase` tests run under pytest-django with the example's settings
  (`example/` on the path); `src/django_tabler/tests.py` moves to `tests/django_tabler/`.
- Sessions, ported from upstream:
  - `tests(python, django)`: installs `django~={django}.0` and the built package (not the checkout; the
    installed-origin assertion from upstream), runs the package suites (`tests/`) with coverage, one XML report per
    session.
  - `examples(python, django)`: installs the package with `examples,test`, runs the example's tests.
  - `package`: builds wheel + sdist and runs `check_dist.py`.
  - `docs`: `mkdocs build --strict` (optional locally, CI has its own job).
- Both test sessions install crud-views from git `main` until 0.31 (decision 3).
- `Taskfile.yaml` `test` keeps working for local use (it may call nox or pytest directly).

### Lint

- ruff with upstream's configuration (line length 120, same rule selection, same per-file ignores adapted to
  `example/`); `.pre-commit-config.yaml` as upstream. One reformatting commit applies `ruff format` to the whole repo
  before other changes, so later diffs stay readable. `CLAUDE.md`'s "no linter" line is updated.

### CI (`.github/workflows/`)

- `tests.yml` (push to main, PRs): matrix over Python, runs the `tests` and `examples` sessions for all four Django
  versions in each row, uploads coverage to Codecov.
- `lint.yml`: ruff format check, ruff check, `nox -s package`.
- `docs.yml`: `mkdocs build --strict` on PRs and tags.
- `publish.yml` (tags `v*`): tests, docs, lint, then PyPI upload via trusted publishing in a `pypi` environment, as
  upstream. It must not publish while the dependency is still the git URL.
- `demo.yml`: deploy a tag's commit to Render through the API, a daily data wipe, and a manual trigger, as upstream.
  *Builder's call:* the manual trigger may deploy `main`, so the demo can go live once the repo is public, before
  v0.1.0.
- `.github/requirements/ci.in` + hash-pinned `ci.txt`; `docs/requirements.in` + `requirements.txt`, as upstream.
- `codecov.yml` as upstream, `after_n_builds: 4`; coverage is advisory (no `fail_under` until a baseline exists).

### Docs (Read the Docs)

- mkdocs, readthedocs theme, awesome-pages, `.readthedocs.yaml` as upstream.
- `docs/` becomes the published user guide. Minimum content for 0.1.0: index (what it is, screenshots, current
  version), installation and `INSTALLED_APPS` order, settings (`CRUD_VIEWS_EXTENDS`, crispy pack), branding overrides
  (`django_tabler/includes/*.html`), layouts and the layout switch, icons, the crispy pack, theme internals (from
  `crud_views_tabler.md`, `crispy_tabler_coverage.md`), the demo, and a development page.
- Internal notes move out of the docs build into `dev/` (findings log, upstream questions/status, tooltip notes).
  `docs/superpowers/` moves to `superpowers/` at the repo root, as upstream. References to these paths (CLAUDE.md,
  the findings log, the vendoring script) are updated.

### Demo (Render)

- `render.yaml` as upstream: free plan, `autoDeploy: false`, build installs `.[examples]` + a
  `requirements/demo.txt` (gunicorn, whitenoise), `collectstatic`; start runs `migrate`, `cv_manage_group`,
  `seed_demo`, `seed_demo_showcase`, then gunicorn. Fresh SQLite on every start.
- `example/config/settings_demo.py` modelled on upstream's: `DEBUG=False`, `SECRET_KEY` from env, host from
  `RENDER_EXTERNAL_HOSTNAME`, secure cookies, whitenoise, `CRUD_VIEWS_MANAGE_ACCESS_TRACE = False`.
- The demo accounts (alex/sam/kim, password `demo`) are shown on the sign-in page or the docs' demo page. The local
  Cloudflare tunnel host stays in the local settings.

### Repo transfer

1. Scan the full history for files from the Tabler archives (anything not in `django_tabler.icons` form, archive
   paths, images) and for secrets. Findings go to the user before anything else; rewriting history is the user's call.
2. Rename the repo to `django-crud-views-tabler`, transfer to `jacob-consulting`, update the local remote.
3. Make it public; set up Read the Docs, Codecov, the PyPI trusted publisher, and the Render service + secrets
   (`RENDER_API_KEY`, `RENDER_SERVICE_ID`, variable `DEMO_URL`). These are account steps for the user; the
   implementation documents them in the development docs.

### README and project docs

README rewritten for PyPI (what it is, install, minimal settings, links to docs and demo, "Current version: …").
`CLAUDE.md` updated for the new layout, commands and paths.

## Order of work

1. Ruff reformat commit; rename, packaging, dependencies, LICENSE/CHANGELOG/version.
2. Tests onto pytest; nox sessions; version compatibility fixes until the matrix is green locally.
3. Lint config, CI workflows, Codecov.
4. Docs restructure and Read the Docs config.
5. Render demo.
6. History scan, then transfer and go public (user steps).
7. Publish workflow ready; the first release follows the crud-views 0.31 release.

## Left to the builder

- Exact test file moves and pytest configuration (`pytest.ini_options`, `--ds` per suite or conftest-based).
- Whether `nox` replaces the commands in `Taskfile.yaml` `test` or sits next to them.
- Exact wording and page structure of the user docs, within the minimum content above.
- Whether the demo needs upstream's rate limiting (`django-ratelimit`); add it if writes from the public are a concern.
