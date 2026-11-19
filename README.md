# django-crud-views-tabler

[![Tests](https://github.com/jacob-consulting/django-crud-views-tabler/actions/workflows/tests.yml/badge.svg)](https://github.com/jacob-consulting/django-crud-views-tabler/actions/workflows/tests.yml)
[![Lint](https://github.com/jacob-consulting/django-crud-views-tabler/actions/workflows/lint.yml/badge.svg)](https://github.com/jacob-consulting/django-crud-views-tabler/actions/workflows/lint.yml)
[![Coverage](https://codecov.io/gh/jacob-consulting/django-crud-views-tabler/branch/main/graph/badge.svg)](https://codecov.io/gh/jacob-consulting/django-crud-views-tabler)
[![Docs](https://readthedocs.org/projects/django-crud-views-tabler/badge/?version=latest)](https://django-crud-views-tabler.readthedocs.io/en/latest/)
[![License](https://img.shields.io/github/license/jacob-consulting/django-crud-views-tabler)](https://github.com/jacob-consulting/django-crud-views-tabler/blob/main/LICENSE)
[![Demo](https://github.com/jacob-consulting/django-crud-views-tabler/actions/workflows/demo.yml/badge.svg)](https://django-crud-views-tabler-demo.onrender.com)

Current version: 0.1.0

A [Tabler](https://tabler.io) 1.6.1 theme for [django-crud-views](https://github.com/jacob-consulting/django-crud-views).
One distribution, two Django apps:

- `crud_views_tabler`: the theme. Listed before `crud_views` in `INSTALLED_APPS`, it shadows the stock Bootstrap 5
  layout templates and registers Tabler button classes, icons and JavaScript adapters through upstream's hooks; your
  views need no changes.
- `django_tabler`: a Tabler page shell that does not depend on django-crud-views: layouts (top bar or sidebar),
  sign-in page, `{% load tabler %}` icon tags, an end-user layout switch, and `crispy_tabler`, a django-crispy-forms
  template pack.

Python 3.12–3.15, Django 5.2 and 6.1. Tabler loads from the jsDelivr CDN.

- Documentation: https://django-crud-views-tabler.readthedocs.io/
- Source and issues: https://github.com/jacob-consulting/django-crud-views-tabler
- Live demo: https://django-crud-views-tabler-demo.onrender.com (sign in as `alex`, `sam` or `kim`, password `demo`)

## Install

```shell
pip install django-crud-views-tabler
```

```python
INSTALLED_APPS = [
    # django.contrib apps, then:
    "crispy_forms",
    "django_tables2",
    "django_filters",
    "django_tabler",
    "crud_views_tabler",  # before crud_views: its templates shadow the stock ones
    "crud_views.apps.CrudViewsConfig",
    # your apps
]

CRUD_VIEWS_EXTENDS = "crud_views_tabler/page.html"
CRISPY_ALLOWED_TEMPLATE_PACKS = ("crispy_tabler",)
CRISPY_TEMPLATE_PACK = "crispy_tabler"
DJANGO_TABLES2_TEMPLATE = "crud_views/table/bootstrap5.html"
```

Branding (site name, logo, menu, default layout) is done by overriding a few include templates; see the
[documentation](https://django-crud-views-tabler.readthedocs.io/en/latest/branding/).

## The demo: Acme Roasters

`example/` is a back office for a specialty coffee roastery (customers, orders, subscriptions, products, green coffee
lots, cupping, roast batches, shipments), built with django-crud-views and themed by this package. The app code never
imports the theme; every crud_views page has a "Show code" panel, and `/theming/` shows the whole theme.

Try it online at https://django-crud-views-tabler-demo.onrender.com: sign in as `alex`, `sam` or `kim` (password
`demo`). It runs on Render's free plan, so the first request after a pause may take a minute, and its data is reset
every night.

### Run it

With [Task](https://taskfile.dev) and [uv](https://docs.astral.sh/uv/), next to checkouts of
[django-crud-views](https://github.com/jacob-consulting/django-crud-views) and
[django-crud-views-extensions](https://github.com/jacob-consulting/django-crud-views-extensions) (local development
installs both from `../`, because the theme tracks unreleased upstream features):

```shell
task up      # uv sync, migrate, superuser admin/admin, seed the demo data, runserver
task         # list all tasks (setup, run, seed, seed:reset, reset, test, test:matrix, …)
```

Open http://127.0.0.1:8000/ and sign in. `task setup` is safe to re-run; `task seed:reset` rebuilds the demo data in
place; `task reset` deletes the SQLite database and uploaded media and sets everything up again. More in
[Development](https://django-crud-views-tabler.readthedocs.io/en/latest/development/).

### Demo accounts and data

| Account | Role | Sees |
|---|---|---|
| `alex` | Owner (group `Owner`) | everything; the only one who may run subscriptions or manage users |
| `sam` | Account manager (`Account managers`) | only the customers Guardian grants him (setting a customer's account manager grants or withdraws that access), their orders and subscriptions; roastery and catalog read-only; actions he may not use show disabled |
| `kim` | Head roaster (`Roasters`) | roastery in full; customers, orders and catalog read-only, except the confirmed → roasted step |
| `admin` | superuser from the Taskfile | everything, plus `/admin/` |

The password is `demo` for the three demo accounts (`admin` for `admin`); the sign-in page has a button per demo
account that fills the form.

`seed_demo` builds one coherent world from a fixed random seed: about 25 customers (four of them Sam's), their
addresses, 70 orders over 90 days in every workflow state, 30 products of three kinds, 7 green lots with cupping
sessions and scores, roast batches, subscriptions and shipments for the shipped orders. It refuses to run on a
database that already has the demo accounts. `seed_demo --reset` deletes every row of the demo apps' tables and the
demo accounts and groups (not `admin`, not the showcase items) and builds the same world again; `--seed N` varies it.

### Pages

The sidebar (or, in the top-bar layout, one dropdown per section) shows what the account may open:

| Section | Page | URL | django-crud-views features on show |
|---|---|---|---|
| | Dashboard | `/` | plain Django view: stat cards, revenue chart (ApexCharts), orders to roast, recent cuppings |
| Sales | Customers | `/customer/` | Guardian per-object permissions, conditional group (wholesale terms), object detail `split-card`, action menus, nested addresses (Mark default: action view), delete protection |
| | Orders | `/orders/`, `/customer/<id>/order/` | two ViewSets on one model, workflow (draft → confirmed → roasted → shipped → delivered, cancel), line formset, typeahead customer picker, datetimepicker, Duplicate (custom form), Packing slip (context button), disabled edit/delete once shipped |
| | Subscriptions | `/subscriptions/` | nested and top-level lists, "Run subscriptions" (custom form without an object, own permission) |
| Catalog | Products | `/product/` | polymorphic (beans / equipment / subscription), card view as the landing page plus a table, per-kind object detail |
| | Categories | `/category/` | ordered (up/down) |
| Roastery | Green lots | `/lot/` | object detail `accordion`, nested cupping sessions with a score formset, delete preview |
| | Roast batches | `/batch/` | M2M to orders, computed weight loss |
| | Shipments | `/shipment/` | a `Resource` (no ORM) from a fake courier API |
| Developer | Form showcase | `/showcase/` | every branch of the crispy pack on one form ([coverage](https://django-crud-views-tabler.readthedocs.io/en/latest/crispy_tabler/)) |
| | How this is themed | `/theming/` | the theme's files and line counts, computed at render time |
| Users | Users | `/users/` | searchable user list, create in a modal (`auth.view_user` / `auth.add_user`) |

Plus `/accounts/login/` and `/admin/` (staff). The demo opens with the dark sidebar of the approved mockup (its
default layout, `example/templates/django_tabler/includes/layout_defaults.html`). The gear (in the sidebar footer,
or in the top bar) switches the layout (top bar, sidebar, folded sidebar, width, navbar colour and style); dark mode
is the moon/sun toggle. A choice stays in the browser's `localStorage` and wins over the default.

### Settings from the environment

`DJANGO_SECRET_KEY`, `DJANGO_DEBUG` (`1`/`0`, default `1`), `DJANGO_ALLOWED_HOSTS` (comma-separated) and
`CRUD_VIEWS_MANAGE_VIEWS_ENABLED` (`yes` by default: crud_views' manage pages list who holds which permission, so
only active members of the `CRUD_VIEWS_MANAGE` group may open them, whatever `DEBUG` says; the seed makes `alex` the
only member. `no` closes them for everyone, `debug_only` also requires `DEBUG`). The built-in secret key is for
local development only.

## Development

```shell
task test          # all suites against the sibling checkouts, plus the system check
task test:matrix   # nox: Python 3.12–3.15 x Django 5.2/6.1 against the built package, as CI
```

Everything the demo needed beyond upstream hooks (theme CSS, override templates, workarounds) is listed, with upstream
file and line, in [`dev/crud_views_upstream_findings_roastery.md`](https://github.com/jacob-consulting/django-crud-views-tabler/blob/main/dev/crud_views_upstream_findings_roastery.md).

## License

MIT
