# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Django 6.1 / Python 3.14 project ("Acme Admin") that grows two reusable packages under `src/` and a demo project
under `example/` that exercises them:

- `src/django_tabler/`: Tabler 1.6.1 page shell (loaded from the jsDelivr CDN), layouts, sign-in page, `{% load tabler %}`
  icon tags, Tabler icon SVG paths (`icons.py`), the end-user layout switch, **and** the django-crispy-forms template
  pack `crispy_tabler` (`templates/crispy_tabler/` + `django_tabler.crispy`). Must not depend on django-crud-views;
  only the crispy pack needs the `crispy` extra.
- `src/crud_views_tabler/`: Tabler theme for django-crud-views. Depends on `django_tabler`.
- `example/`: the demo site (`config/` settings, apps `dashboard`, `showcase`).

django-crud-views comes from the sibling checkout `../django-crud-views` as an editable path dependency
(`[tool.uv.sources]`), because the theme tracks unreleased upstream features. Upstream changes there can break the
theme's tests.

## Commands

```shell
task up      # Taskfile.yaml: uv sync, migrate, superuser admin/admin, seed, runserver
task setup   # the same without runserver; idempotent
task reset   # delete example/db.sqlite3 + example/media, then setup (asks first)

uv run python example/manage.py seed_demo | seed_demo_showcase   # demo data by hand

# Example apps' Django tests (the example's settings)
uv run python example/manage.py test django_tabler dashboard showcase
uv run python example/manage.py test dashboard.tests.SomeTestCase.test_name   # single test

# crud_views_tabler theme tests (pytest, own settings and test app: tests/crud_views_tabler/)
uv run --group test pytest tests/crud_views_tabler --ds tests.crud_views_tabler.settings

# crispy_tabler template pack (pytest, own settings: tests/crispy_tabler/settings.py)
uv run --group test pytest
uv run --group test pytest tests/crispy_tabler/test_widgets.py -k some_name

task test    # all of the above plus the check
uv run python example/manage.py check --fail-level WARNING   # includes crud_views_tabler.W001
```

There is no configured linter/formatter.

`seed_demo` (demo accounts alex/sam/kim, password `demo`; apps listed in `SEED_APPS`) refuses to run when those users
exist. `seed_demo_showcase` is not idempotent (a re-run adds rows: it skips a clashing row
before drawing its remaining random values, so later names change). The
Taskfile's `seed:*` tasks guard against that with `status:` checks that skip a step when its table has data.

## Architecture

**Template chain.** `django_tabler/base.html` ← `django_tabler/layouts/app.html` (navbar/sidebar, Tabler page header
with blocks `breadcrumb`, `page_heading` (wraps `page_title`), `subtitle`, `actions`, `messages`, `content`) ← `crud_views_tabler/page.html`,
which is `CRUD_VIEWS_EXTENDS` and maps crud_views tags/blocks (`cv_header`, `cv_context_actions`, `cv_filter`,
`cv_content`, `cv_css`/`cv_js`) onto those blocks. Projects customise branding by overriding
`django_tabler/includes/{site_name,nav_menu,brand,head}.html` (the example does so in `example/templates/`).

**How the crud_views theme works** (details in `docs/crud_views_tabler.md`): django-crud-views has no theme setting.
The theme is an app listed *before* `crud_views` in `INSTALLED_APPS`, so its `templates/crud_views/...` files shadow
the stock Bootstrap 5 templates; anything not overridden falls through. No crud_views code is patched or subclassed.
Overrides are deliberately limited to page *layout* (modal shell, form frame, table, card, alert, filter, card
content) — none renders a button. Everything else is registered in `CrudViewsTablerConfig.ready()`:
- button classes: `buttons.TABLER_BUTTON_CLASSES` via `register_button_classes()` (keys like `location:variant` and
  `location:variant:icon`; the `:icon` variant adds `btn-icon` for icon-only label mode),
- label modes: `register_label_mode_defaults({"form": "both"})`, so form buttons show icon plus label,
- icons: `register_icon_library("tabler", ...)` + `register_icons(TABLER_ICONS)` mapping crud_views' semantic icon
  names to `tabler:<name>`; SVG paths live in `django_tabler.icons.ICONS`, and the system check
  `crud_views_tabler.W001` flags `tabler:` names with no path,
- assets: `tabler-adapters.js` wires `cv.adapters` (modal/tooltip/collapse) to `window.tabler`'s Bootstrap
  components. Wrap `cv.adapters.tooltip.init` (call the original), never replace it or the whole `tooltip` object:
  upstream's `init` carries a Bootstrap transition guard, and the object carries `hide`/`dispose`.

Prefer solving theme problems through upstream hooks (class keys, blocks, settings) rather than new template
overrides; copied templates drift from upstream silently. Upstream asks and their status are tracked in
`docs/crud_views_upstream_*.md`.

**crispy_tabler pack.** The templates are vendored from crispy-bootstrap5 by `scripts/vendor_templates.py` (rewrites
`bootstrap5/` includes to `crispy_tabler/`, adds a provenance comment, otherwise byte-identical). Six templates are
hand-edited (`HAND_EDITED` in the script) and the script refuses to overwrite them without `--force`; files under
`widget/` are pack-owned. `django_tabler/crispy/vendored.py:CRISPY_BOOTSTRAP5_VERSION` must match the `test` group's
crispy-bootstrap5 pin — `test_pack_parity.py` fails otherwise. `django_tabler.crispy.layout` subclasses
crispy-bootstrap5's `FloatingField`/`Switch`, so that distribution stays installed (but not in `INSTALLED_APPS`).
`docs/crispy_tabler_coverage.md` documents which template branches the `showcase` demo form exercises.

**Layout switch.** The navbar gear (`layout_switch_menu.html` + `static/django_tabler/layout-switch.js`) stores the
user's layout choice in `localStorage` using Tabler's own `tabler-*` keys; nothing is server-side.

## Conventions

- All pages require login (`LoginRequiredMiddleware`); the login view is the exception.
- Settings from env: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` (`1`/`0`), `DJANGO_ALLOWED_HOSTS`. The default allowed hosts
  include `cv.jacob-consulting.org`, where the demo is served through a Cloudflare tunnel that terminates HTTPS;
  hence `CSRF_TRUSTED_ORIGINS = ['https://cv.jacob-consulting.org']` in `example/config/settings.py`.
- Design specs and implementation plans live in `docs/superpowers/{specs,plans}/`.

## Tabler reference material

`~/projects/tabler/` holds the extracted paid Tabler archives (each next to its `.zip`, outside this repo):

- `tabler-1.6.1/dashboard/`: the Tabler 1.6.1 dashboard pages (one `.html` per page, e.g. `alerts.html`,
  `all-elements.html`), the reference markup for how components should look
- `tabler-icons-3.49.0/` (`svg/`, `png/`, `webfont/`, …): source for new paths in `django_tabler.icons.ICONS`
- `tabler-illustrations-1.18.0/`, `tabler-avatars-1.1.0/`, `tabler-emails-3.0/`

These are licensed assets: use them as reference, and don't commit them wholesale into this repo.
