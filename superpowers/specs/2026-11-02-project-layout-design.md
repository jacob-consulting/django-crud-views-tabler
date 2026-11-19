# Project layout: reusable packages in `src/`, demo in `example/`

## Intent

This repository is a proof of concept and playground for two integrations:

- `crud_views_tabler`: the Tabler theme for django-crud-views
- `crispy_tabler`: a django-crispy-forms template pack for Tabler

Today the reusable code, the shared templates and the demo apps all sit at the repository root, so it is hard to see
what is integration work and what is demo. The new layout makes that line visible and enforces it. Bringing
`crispy_tabler` into the repository makes it easier to change it and the theme together.

## Goals

- Reusable code lives in `src/`; everything specific to the demo lives in `example/`.
- A new `django_tabler` package owns the shared Tabler templates and template tags.
- `crispy_tabler` is developed from this repository, from a copy of the sibling project.
- The running app looks and behaves as it does now, including the "Acme Admin" branding.

## Non-goals

- Publishing to PyPI, versioning, changelogs or a public API for the new package.
- Settings for every option. Customization uses normal Django template overriding.
- Fixing the test failures that already exist (see Verification).
- Bringing django-crud-views into the repository. It stays a sibling path dependency.
- Rewriting historical documents under `docs/superpowers/`.

## Anti-goals

The work has failed, even if the app runs, if:

- Non-test code in `src/` imports from `example/`, or `django_tabler` imports from `crud_views_tabler` or `crud_views`.
- Any page changes in appearance or behavior.
- The existing `db.sqlite3` with its admin account and seed data is lost.
- The sibling `../crispy-tabler` checkout is modified.

## Target layout

```
pyproject.toml
uv.lock
README.md
docs/
scripts/
  vendor_templates.py         from crispy-tabler, DEST adjusted
tests/
  crispy_tabler/              crispy-tabler's pytest suite and its settings
src/
  django_tabler/
    apps.py
    icons.py                  ICONS and svg() from crud_views_tabler/icons.py
    templatetags/tabler.py    from dashboard/templatetags/tabler.py
    templates/
      django_tabler/
        base.html
        layouts/app.html
        includes/             navbar, nav_menu, brand, site_name, field, messages
      registration/login.html
  crud_views_tabler/          as today, plus templates/crud_views_tabler/page.html; a smaller icons.py; tests.py stays here
  crispy_tabler/              copied from ../crispy-tabler/src/crispy_tabler
example/
  manage.py
  db.sqlite3                  moved, still gitignored
  config/
  catalog/  customers/  dashboard/
  templates/
    django_tabler/includes/   Acme overrides: nav_menu, brand, site_name
```

## Decisions

### From the project owner

- Shared templates become part of a `django_tabler` package.
- `crud_views_tabler` stays a separate package in `src/`.
- The rest becomes an example application in `example/`.
- `crispy_tabler` is copied into `src/`.

### Made during design, open to correction

- **`config/` and `manage.py` move to `example/`.** This changes the original "keep config at root": they configure
  only the demo. The commands become `uv run python example/manage.py ...`, run from the repository root.
- **Dependency direction:** `crud_views_tabler` may depend on `django_tabler`, never the reverse. `crispy_tabler`
  depends on neither. `example/` may use all three.
- **Template namespace:** shared templates move under `django_tabler/`, so `base.html` becomes
  `django_tabler/base.html`. Every `extends` and `include` follows. `registration/login.html` keeps its path because
  Django's `LoginView` looks for it there. `CRUD_VIEWS_EXTENDS` becomes `crud_views_tabler/page.html`, moved from
  `templates/crud_views_page.html` into `crud_views_tabler`.
- **Icons:** `icons.py` is split. The generic `ICONS` and `svg()` move to `django_tabler.icons`. `TABLER_ICONS` and
  `render()`, which are specific to django-crud-views, stay in `crud_views_tabler/icons.py`, which imports from
  `django_tabler.icons`. The registered path `crud_views_tabler.icons.render` does not change. `checks.py` and
  `tests.py` import each name from wherever it now lives; no re-exports. The `{% icon %}`, `initials`, `avatar_color`
  and `form_control` tag library keeps the load name `tabler`, so `{% load tabler %}` lines do not change.
- **Acme content is split out through small override templates:**
  - `includes/site_name.html` holds the site name for the page title, brand and footer. The package default is
    "Django Tabler"; the example says "Acme Admin".
  - `includes/nav_menu.html` holds the menu items and is empty by default. The example supplies the Dashboard,
    Customers, Products and Users links.
  - `includes/brand.html` links to `/` by default. The example links to `dashboard:index` with today's icon.
  - The rest of `navbar.html` (theme toggle, user menu) stays in the package. It keeps using the `admin:` and `logout`
    URL names, which is acceptable for a playground.
- **Messages:** `layouts/app.html` must not call `{% cv_messages %}`. It gets
  `{% block messages %}{% include "django_tabler/includes/messages.html" %}{% endblock %}`, using Django's messages
  framework. `crud_views_tabler/page.html` overrides the block with `{% cv_messages %}`. The new include must produce
  the same markup that `cv_messages` produces today on non-crud pages such as the dashboard and user list.
- **Packaging:** the root `pyproject.toml` gets a setuptools build (`where = ["src"]`, with templates and static files
  as package data) and uv installs the project editable. The three packages import by their existing names. The
  project name stays `tabler-test`. `example/` is not installed; running `example/manage.py` puts it on the path.
- **Copying crispy-tabler:** a plain file copy from sibling commit `2f86558`, without its git history. Record that
  commit in `docs/crispy_tabler_coverage.md`. Remove the `crispy-tabler` entry from `[tool.uv.sources]` and the
  dependency list, and add its runtime dependencies (`django-crispy-forms`, `crispy-bootstrap5`) to the root project.
  The copy is now the working copy. Nothing is synced back automatically; syncing is a later, manual decision.
- **Tests:**
  - `crud_views_tabler/tests.py` stays in `src/` and keeps importing from `customers`, because it needs a real ViewSet
    to exercise the theme. It is the one exemption from the rule that `src/` does not import from `example/`, and it
    only runs with the example's settings. Keeping it in place also keeps the test IDs comparable with the baseline.
    Hiding the dependency, for example with `apps.get_model` or imports inside functions, is not acceptable.
  - Django's runner covers everything that runs today, from one command at the root:
    `uv run python example/manage.py test crud_views_tabler dashboard catalog customers`. If a shorter form is
    practical, the builder may provide it.
  - crispy-tabler's suite stays on pytest with its own settings, in `tests/crispy_tabler/`, run by
    `uv run --group test pytest`. Its exact `crispy-bootstrap5==2026.9` test pin and `pytest`/`pytest-django` move to
    a dependency group. If that exact pin conflicts with the runtime lock, the lock uses the same version.
- **Moves use `git mv`** so file history follows.
- **Documentation:** update `README.md` (run commands, layout, tests, the missing `seed_demo_catalog` step) and the
  current paths in `docs/crud_views_tabler.md` and `docs/crispy_tabler_coverage.md`.

## Constraints

- Python `>=3.14` and Django 6.1 stay as they are.
- `django_tabler` goes before `crud_views_tabler` in `INSTALLED_APPS`. `crud_views_tabler` stays before `crud_views`.
- `BASE_DIR` in `example/config/settings.py` resolves to `example/`, so `db.sqlite3`, `staticfiles/`, `media/` and
  `templates/` all resolve inside `example/`. Existing `.gitignore` patterns already match there.
- `../django-crud-views` stays an editable path dependency, with its relative path unchanged.

## Verification

**Baseline before this work, at commit `a287d94`: 84 tests, 80 pass, 4 fail.** The failures already exist and are out
of scope:

- `catalog.tests.ProductFormCoverageTests.test_form_actions_and_group_labels`
- `crud_views_tabler.tests.ThemeRenderingTests.test_delete_form_is_the_stock_crispy_delete_form`
- `crud_views_tabler.tests.ThemeRenderingTests.test_related_objects_alerts_get_the_tabler_layout`
- `crud_views_tabler.tests.TablerIconTests.test_every_upstream_icon_name_is_mapped`

The work is done when:

- The Django test run has the same 84 tests, with exactly these 4 failures for the same reasons.
- crispy-tabler's pytest suite passes from its new location with the same results as in the sibling project.
- `uv run python example/manage.py check` reports no issues, and existing data is still there after the database move.
- The rendered HTML of the login, dashboard, user list, customer list and product list pages is unchanged, apart from
  expected differences such as CSRF tokens. Capture these before moving anything.
- `src/` contains no imports from `example/` outside `crud_views_tabler/tests.py`, and `django_tabler` contains no reference to `crud_views`.
- `git -C ../crispy-tabler status` is clean.

## Left to the builder

- The order of the moves and how the commits are split.
- How to capture and compare the rendered HTML.
- Exact pytest configuration in `pyproject.toml`, including how the crispy suite's `tests.settings` module is renamed.
- `django_tabler`'s `AppConfig` details.
