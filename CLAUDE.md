# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

The distribution **django-crud-views-tabler** (PyPI; repo `jacob-consulting/django-crud-views-tabler`, docs on Read the
Docs): two reusable packages under `src/` and a demo project under `example/` that exercises them. Supported: Python
3.12–3.15 × Django 5.2, 6.1 (the nox matrix); local development runs Python 3.14 / Django 6.1.

- `src/django_tabler/`: Tabler 1.6.1 page shell (loaded from the jsDelivr CDN), layouts, sign-in page, `{% load tabler %}`
  icon tags, Tabler icon SVG paths (`icons.py`), the end-user layout switch, **and** the django-crispy-forms template
  pack `crispy_tabler` (`templates/crispy_tabler/` + `django_tabler.crispy`). Must not import django-crud-views (a test greps
  the package), although the distribution depends on it.
- `src/crud_views_tabler/`: Tabler theme for django-crud-views. Depends on `django_tabler`.
- `example/`: the Acme Roasters demo: `config/` (settings, the "Show code" collector `showcode.py`, tag libraries
  `showcode` and `acme_nav` registered in `TEMPLATES['OPTIONS']['libraries']` because `config` is not an app, date
  formats in `config/formats/`), apps `dashboard` (start page, demo accounts, `seed_demo`), `sales` (customers with
  Guardian, addresses, orders with workflow and line formset, subscriptions), `catalog` (polymorphic products, ordered
  categories), `roastery` (green lots, cupping sessions with score formsets, roast batches), `shipping` (a `Resource`
  over a fake courier API) and `showcase` (the crispy pack coverage form). App code never imports `django_tabler` or
  `crud_views_tabler`; icon names are strings (`"tabler:<name>"`).

django-crud-views and django-crud-views-extensions come from the sibling checkouts `../django-crud-views` and
`../django-crud-views-extensions` as editable path dependencies (`[tool.uv.sources]`), because the theme tracks
unreleased upstream features. Upstream changes there can break the theme's tests. Both checkouts are read-only for
this repo: gaps are worked around here and logged in `dev/crud_views_upstream_findings_roastery.md`. nox, CI and the
Render demo cannot see the checkouts: until django-crud-views 1.0.0rc1 is on PyPI they install it from GitHub `main`
(`CRUD_VIEWS` in `noxfile.py`, `requirements/demo.txt`, both with `--no-sources`/no uv sources), and the declared floor
stays `>=0.30`; `publish.yml` refuses to publish until the floor is `>=1.0.0rc1` (`scripts/check_release_floor.py`).

## Commands

```shell
task up      # Taskfile.yaml: uv sync --extra examples --extra test --extra dev, migrate, superuser, seed, runserver
task setup   # the same without runserver; idempotent
task reset   # delete example/db.sqlite3 + example/media, then setup (asks first)
task seed:reset   # seed_demo --reset: rebuild the demo data in place

uv run python example/manage.py seed_demo [--reset] | seed_demo_showcase   # demo data by hand

# Always run test suites on all cores: pytest -n auto (pytest-xdist; task test and nox do). Single-core only for
# one test or a -k selection.

# Example apps' tests: pytest-django from example/ (example/pytest.ini, settings config.settings)
cd example && uv run pytest -n auto
cd example && uv run pytest dashboard/tests.py -k some_name   # single test
# sales keeps its tests in a tests/ package (sales/tests/test_orders.py, ...), the other apps in tests.py

# package suites, each with its own settings
uv run pytest -n auto tests/crud_views_tabler --ds tests.crud_views_tabler.settings   # theme (own test app)
uv run pytest -n auto tests/django_tabler --ds tests.django_tabler.settings           # shell, packaging scripts
uv run pytest -n auto                                                         # crispy_tabler pack (default)
uv run pytest tests/crispy_tabler/test_widgets.py -k some_name

task test          # all of the above plus the check, against the sibling checkouts
task test:matrix   # uvx nox: tests-<py>(django='<dj>'), examples-<py>(django='<dj>'), package, docs
uv run python example/manage.py check --fail-level WARNING   # includes crud_views_tabler.W001
```

Lint: ruff with django-crud-views' configuration (`uv run ruff format . && uv run ruff check .`; pre-commit
hook in `.pre-commit-config.yaml`). Docs: mkdocs (`uvx nox -s docs`, strict). Workflows in `.github/workflows/`
(tests, lint, docs, publish, demo); the Render demo is `render.yaml` + `example/config/settings_demo.py`.

`seed_demo` (demo accounts alex/sam/kim, password `demo`; apps listed in `SEED_APPS`, each with a `seed(rng, world)`)
builds the whole roastery world and is deterministic for a `--seed` (dates are relative to today). It refuses with
"Demo data already present; use --reset to rebuild." when those users exist; `seed_demo --reset` deletes the demo rows
(never `admin` or other users) in one transaction and rebuilds. `seed_demo_showcase` is separate and not idempotent
(a re-run adds rows: it skips a clashing row before drawing its remaining random values, so later names change); the
Taskfile's `seed:showcase` guards against that with a `status:` check that skips it when the table has data.

## Architecture

**Template chain.** `django_tabler/base.html` ← `django_tabler/layouts/app.html` (navbar/sidebar, Tabler page header
with blocks `page_header_before` (empty, above the header), `page_header_top` (top of the header, above the title row), `breadcrumb`, `page_heading` (wraps `page_title`), `subtitle`, `actions`, `messages`, `content`) ← `crud_views_tabler/page.html`,
which is `CRUD_VIEWS_EXTENDS` and maps crud_views tags/blocks (`cv_navbar_items` for ViewSet Navigation, `cv_header`, `cv_context_actions`,
`cv_filter`, `cv_content`, `cv_css`/`cv_js`) onto those blocks. Projects customise branding by overriding
`django_tabler/includes/{site_name,nav_menu,brand,head,layout_defaults}.html` (the example does so in `example/templates/`).
`nav_menu.html` is included by both navigations with `nav_layout` `"horizontal"` (top bar) or `"vertical"`
(sidebar); the example renders its sections as dropdowns in the top bar and as headings in the sidebar, from the menu
defined once in `example/config/templatetags/acme_nav.py`. The example's `CRUD_VIEWS_EXTENDS` is
`project/crud_views.html`, which extends `crud_views_tabler/page.html` and adds the "Show code" panel (sources fetched
from `/_code/<app_label>/` when it opens).

**How the crud_views theme works** (details in `docs/theme_internals.md`): django-crud-views has no theme setting.
The theme is an app listed *before* `crud_views` in `INSTALLED_APPS`, so its `templates/crud_views/...` files shadow
the stock Bootstrap 5 templates; anything not overridden falls through. No crud_views code is patched or subclassed.
Overrides are deliberately limited to page *layout* (modal shell, form frame, table, card, alert, filter, card
content) — none renders a button. Everything else is registered in `CrudViewsTablerConfig.ready()`:
- button classes: `buttons.TABLER_BUTTON_CLASSES` via `register_button_classes()` (keys like `location:variant` and
  `location:variant:icon`; the `:icon` variant adds `btn-icon` for icon-only label mode; also the `workflow:*` keys:
  `workflow:badge-<colour>` for the state badge and `workflow:history-table`, and the manage page's `manage:*` badge
  keys, in named colours because the page's legend names them),
- label modes: `register_label_mode_defaults({"form": "both"})`, so form buttons show icon plus label,
- icons: `register_icon_library("tabler", ...)` + `register_icons(TABLER_ICONS)` mapping crud_views' semantic icon
  names to `tabler:<name>`; SVG paths live in `django_tabler.icons.ICONS`, and the system check
  `crud_views_tabler.W001` flags `tabler:` names with no path,
- assets: `tabler-adapters.js` wires `cv.adapters` (modal/tooltip/collapse) to `window.tabler`'s Bootstrap
  components. Wrap `cv.adapters.tooltip.init` (call the original), never replace it or the whole `tooltip` object:
  upstream's `init` carries a Bootstrap transition guard, and the object carries `hide`/`dispose`.

Prefer solving theme problems through upstream hooks (class keys, blocks, settings) rather than new template
overrides; copied templates drift from upstream silently. Upstream asks and their status are tracked in
`dev/crud_views_upstream_*.md`.

**crispy_tabler pack.** The templates are vendored from crispy-bootstrap5 by `scripts/vendor_templates.py` (rewrites
`bootstrap5/` includes to `crispy_tabler/`, adds a provenance comment, otherwise byte-identical). Six templates are
hand-edited (`HAND_EDITED` in the script) and the script refuses to overwrite them without `--force`; files under
`widget/` are pack-owned. `django_tabler/crispy/vendored.py:CRISPY_BOOTSTRAP5_VERSION` must match the `test` extra's
crispy-bootstrap5 pin — `test_pack_parity.py` fails otherwise. `django_tabler.crispy.layout` subclasses
crispy-bootstrap5's `FloatingField`/`Switch`, so that distribution stays installed (but not in `INSTALLED_APPS`).
`docs/crispy_tabler.md` documents which template branches the `showcase` demo form exercises.

**Layout switch.** The navbar gear (`layout_switch_menu.html` + `static/django_tabler/layout-switch.js`) stores the
user's layout choice in `localStorage` using Tabler's own `tabler-*` keys. A project's *default* layout is the JSON
object in `django_tabler/includes/layout_defaults.html` (empty in the package: Tabler's top bar); the
`{% layout_defaults_attrs %}` tag on `<html>` turns it into `data-bs-<key>` server values, which `tabler-theme.js`
uses when nothing is stored, plus `data-tabler-layout-defaults` for layout-switch.js, which stores a choice only when
it differs from the project default and falls back to Tabler's defaults. The example sets the vertical, dark
(`navbar-theme: dark`) sidebar of the mockup. Gap: Tabler's primary-colour themes (`data-bs-theme-primary`,
`?theme-primary=…`) need `tabler-themes.min.css`, which `django_tabler/base.html` does not load, so such a choice
shows Tabler's base blue; the switch offers no colour choice.

## Conventions

- All pages require login (`LoginRequiredMiddleware`); the login view is the exception.
- Settings from env: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` (`1`/`0`), `DJANGO_ALLOWED_HOSTS`,
  `CRUD_VIEWS_MANAGE_VIEWS_ENABLED` (default `yes`: since upstream #361 only active members of the
  `CRUD_VIEWS_MANAGE` group may open the manage pages, whatever DEBUG says; `no` closes them for everyone,
  `debug_only` also requires DEBUG). The manage pages also list users (`CRUD_VIEWS_MANAGE_SHOW_USERS`) and show the
  Access check card (`CRUD_VIEWS_MANAGE_ACCESS_TRACE`), both on in `example/config/settings.py`. The default allowed hosts
  include `cv.jacob-consulting.org`, where the demo is served through a Cloudflare tunnel that terminates HTTPS;
  hence `CSRF_TRUSTED_ORIGINS = ['https://cv.jacob-consulting.org']` in `example/config/settings.py`.
- Demo accounts: `alex` (Owner; the only member of the `CRUD_VIEWS_MANAGE` group, so the only account that opens
  the manage pages), `sam` (Account managers; Guardian grants on their own customers), `kim` (Roasters);
  password `demo`. Brand "Acme Roasters", primary colour sienna `#a0522d` (`example/static/acme/acme.css`).
- Theme fix order: an upstream hook (class keys, settings, blocks), then CSS in `crud_views_tabler.css`, then a new
  override template as a last resort. Every theme CSS rule or override, and every upstream bug or awkwardness, gets
  an entry in `dev/crud_views_upstream_findings_roastery.md` in the same commit.
- Design specs and implementation plans live in `superpowers/{specs,plans}/`. `docs/` is the published user guide
  (Read the Docs); maintainer notes live in `dev/`, which is not published.

## Tabler reference material

The maintainer keeps the extracted paid Tabler archives in a local directory outside this repo (`<tabler archives>`,
each next to its `.zip`; ask for the path, it is not recorded here):

- `tabler-1.6.1/dashboard/`: the Tabler 1.6.1 dashboard pages (one `.html` per page, e.g. `alerts.html`,
  `all-elements.html`), the reference markup for how components should look
- `tabler-icons-3.49.0/` (`svg/`, `png/`, `webfont/`, …): source for new paths in `django_tabler.icons.ICONS`
- `tabler-illustrations-1.18.0/`, `tabler-avatars-1.1.0/`, `tabler-emails-3.0/`

These are licensed assets: use them as reference, and don't commit them wholesale into this repo.
