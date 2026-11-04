# Acme Admin

Django 6.1 project with a Tabler 1.6.1 UI (loaded from the jsDelivr CDN), two reusable packages and a demo:

- `django_tabler`: the Tabler page shell, layouts, sign-in page, icons and a crispy-forms template pack;
- `crud_views_tabler`: a Tabler theme for [django-crud-views](https://github.com/jacob-consulting/django-crud-views);
- **Acme Roasters**, a back-office for a specialty coffee roastery (customers, orders, subscriptions, products, green
  coffee lots, cupping, roast batches, shipments), built with django-crud-views and themed by `crud_views_tabler`.
  The app code never imports the theme; every crud_views page has a "Show code" panel, and "How this is themed"
  (`/theming/`) shows the whole theme.

## Run it

With [Task](https://taskfile.dev):

```shell
task up      # uv sync, migrate, superuser admin/admin, seed the demo data, runserver
task         # list all tasks (setup, run, seed, seed:reset, reset, test, …)
```

`task setup` is safe to re-run: the superuser and each seed step are skipped when their data already exists.
`task seed:reset` rebuilds the Acme Roasters demo data in place (`seed_demo --reset`; `admin` and showcase items stay).
`task reset` deletes the SQLite database and uploaded media and sets everything up again. Change the login with
`task up ADMIN_USER=… ADMIN_PASSWORD=…` (local development only).

Or by hand:

```shell
uv sync
uv run python example/manage.py migrate
uv run python example/manage.py createsuperuser
uv run python example/manage.py seed_demo             # the Acme Roasters world and the accounts alex, sam, kim
uv run python example/manage.py seed_demo_showcase    # 40 sample items for the form showcase
uv run python example/manage.py runserver
```

django-crud-views and django-crud-views-extensions are installed from the sibling checkouts `../django-crud-views`
and `../django-crud-views-extensions` (branch `main`) as editable path dependencies (`[tool.uv.sources]` in
`pyproject.toml`), because the theme follows features that are not released yet. Replace the source entries with
version pins once they are.

Open http://127.0.0.1:8000/ and sign in. Every page except the login page requires a signed-in user
(`LoginRequiredMiddleware`).

## Demo accounts and data

| Account | Role | Sees |
|---|---|---|
| `alex` | Owner (group `Owner`) | everything; the only one who may run subscriptions or manage users |
| `sam` | Account manager (`Account managers`) | only the customers Guardian grants him, their orders and subscriptions; roastery and catalog read-only; actions he may not use show disabled |
| `kim` | Head roaster (`Roasters`) | roastery in full; customers, orders and catalog read-only, except the confirmed → roasted step |
| `admin` | superuser from the Taskfile | everything, plus `/admin/` |

The password is `demo` for the three demo accounts (`admin` for `admin`); the sign-in page has a button per demo
account that fills the form.

`seed_demo` builds one coherent world from a fixed random seed: about 25 customers (four of them Sam's), their
addresses, 70 orders over 90 days in every workflow state, 30 products of three kinds, 7 green lots with cupping
sessions and scores, roast batches, subscriptions and shipments for the shipped orders. It refuses to run on a
database that already has the demo accounts. `seed_demo --reset` deletes every row of the demo apps' tables and the
demo accounts and groups (not `admin`, not the showcase items) and builds the same world again; `--seed N` varies it.

## Pages

The sidebar (or, in the top-bar layout, one dropdown per section) shows what the account may open:

| Section | Page | URL | django-crud-views features on show |
|---|---|---|---|
| | Dashboard | `/` | plain Django view: stat cards, revenue chart (ApexCharts), orders to roast, recent cuppings |
| Sales | Customers | `/customer/` | Guardian per-object permissions, conditional group (wholesale terms), object detail `split-card`, action menus, nested addresses (Mark default: action view), delete protection |
| | Orders | `/orders/`, `/customer/<id>/order/` | two ViewSets on one model, workflow (draft → confirmed → roasted → shipped → delivered, cancel), line formset, typeahead customer picker, datetimepicker, Duplicate (custom form), Packing slip (context button), disabled edit/delete once shipped |
| | Subscriptions | `/subscriptions/` | nested and top-level lists, "Run subscriptions" (custom form without an object, own permission) |
| Catalog | Products | `/product/` | polymorphic (beans / equipment / subscription), card view as the landing page plus a table, per-kind object detail |
| | Categories | `/category/` | ordered (up/down) |
| Roastery | Green lots | `/lot/` | object detail `card-rows`, nested cupping sessions with a score formset, delete preview |
| | Roast batches | `/batch/` | M2M to orders, computed weight loss |
| | Shipments | `/shipment/` | a `Resource` (no ORM) from a fake courier API |
| Developer | Form showcase | `/showcase/` | every branch of the crispy pack on one form ([coverage](docs/crispy_tabler_coverage.md)) |
| | How this is themed | `/theming/` | the theme's files and line counts, computed at render time |
| Users | Users | `/users/` | searchable user list, create in a modal (`auth.view_user` / `auth.add_user`) |

Plus `/accounts/login/` and `/admin/` (staff). The navbar's gear switches the layout (top bar, sidebar, folded
sidebar, width, navbar colour and style); dark mode is the moon/sun toggle. Both stay in the browser's `localStorage`.

## Layout

- `src/django_tabler/`: the HTML shell and layouts (`templates/django_tabler/`: top navbar and sidebar, both rendered;
  Tabler's CSS shows the one the user picked), sign-in page, messages and form-field partials, the `{% icon %}`
  template tags (`{% load tabler %}`) and the Tabler icons. It does not depend on django-crud-views. It also holds the
  django-crispy-forms template pack for Tabler (`templates/crispy_tabler/`, with fields, widgets and layout objects in
  `django_tabler.crispy`), originally from `jacob-consulting/crispy-tabler`; the pack needs the `crispy` extra.
  A project overrides `django_tabler/includes/{site_name,brand,nav_menu,head}.html`; `nav_menu.html` is included
  twice, with `nav_layout` set to `"horizontal"` (top bar) or `"vertical"` (sidebar).
- `src/crud_views_tabler/`: Tabler theme for django-crud-views (template overrides, Tabler icon library, button
  classes, CSS, JS adapter), including `crud_views_tabler/page.html`, the page every crud_views view extends; design
  notes in [`docs/crud_views_tabler.md`](docs/crud_views_tabler.md).
- `example/`: the demo project: `manage.py`, `config/` (settings, the "Show code" collector `showcode.py`, the
  navigation `templatetags/acme_nav.py`, date formats), the apps `dashboard` (start page, demo accounts, `seed_demo`),
  `sales`, `catalog`, `roastery`, `shipping` and `showcase`, and `templates/` (the Acme overrides of the
  `django_tabler` includes, `project/crud_views.html` with the code panel, the theming page).
- `tests/crispy_tabler/`: the template pack's test suite; `scripts/vendor_templates.py` re-vendors its templates.
- `tests/crud_views_tabler/`: the theme's test suite, with its own settings and a small test app, independent of
  the demo.

## Settings from the environment

`DJANGO_SECRET_KEY`, `DJANGO_DEBUG` (`1`/`0`, default `1`), `DJANGO_ALLOWED_HOSTS` (comma-separated) and
`CRUD_VIEWS_MANAGE_VIEWS_ENABLED` (`no` by default: crud_views' manage pages list who holds which permission, and
upstream's `debug_only` would open them to every signed-in user while `DEBUG` is on). The built-in secret key is for
local development only.

## Tests

```shell
task test    # everything below
uv run python example/manage.py test django_tabler dashboard sales catalog roastery shipping showcase
uv run --group test pytest                                                         # the crispy template pack
uv run --group test pytest tests/crud_views_tabler --ds tests.crud_views_tabler.settings   # the theme
uv run python example/manage.py check --fail-level WARNING                          # incl. crud_views_tabler.W001
```

## Upstream findings

Everything the demo needed beyond upstream hooks (theme CSS, override templates, workarounds) is listed, with
upstream file and line, in [`docs/crud_views_upstream_findings_roastery.md`](docs/crud_views_upstream_findings_roastery.md).
