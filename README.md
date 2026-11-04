# Acme Admin

Django 6.1 app with a Tabler 1.6.1 UI (loaded from the jsDelivr CDN), Django's built-in authentication and a
prototype Tabler theme for django-crud-views.

## Run it

With [Task](https://taskfile.dev):

```shell
task up      # uv sync, migrate, superuser admin/admin, seed the demo data, runserver
task         # list all tasks (setup, run, seed, reset, …)
```

`task setup` is safe to re-run: the superuser and each seed step are skipped when their data already exists.
`task reset` deletes the SQLite database and uploaded media and sets everything up again. Change the login with
`task up ADMIN_USER=… ADMIN_PASSWORD=…` (local development only).

Or by hand:

```shell
uv sync
uv run python example/manage.py migrate
uv run python example/manage.py createsuperuser
uv run python example/manage.py seed_demo_users       # optional: 40 sample accounts so the charts have data
uv run python example/manage.py seed_demo_customers   # optional: 60 sample customers for the crud_views demo
uv run python example/manage.py seed_demo_showcase    # optional: 40 sample items for the crispy forms demo
uv run python example/manage.py runserver
```

django-crud-views is installed from the sibling checkout `../django-crud-views` (branch `main`) as an editable path
dependency (`[tool.uv.sources]` in `pyproject.toml`), because the theme follows features that are not released yet.
Replace the source entry with a version pin once they are.

Open http://127.0.0.1:8000/ and sign in. Every page except the login page requires a signed-in user
(`LoginRequiredMiddleware`).

## Pages

| URL | What | Who |
|---|---|---|
| `/accounts/login/` | Sign-in | everyone |
| `/` | Dashboard: account stats, sign-ups per month, roles, recent sign-ins | signed-in users |
| `/users/` | Searchable, paginated user list | `auth.view_user` permission |
| `/users/new/` | Create a user (the form opens as a modal on the list) | `auth.add_user` permission |
| `/customer/` | Customers: django-crud-views list (sort, filter), detail, create, update, delete (modal) | `customers.*_customer` permissions |
| `/showcase/` | Form showcase: a django-crud-views ViewSet whose form renders every branch of the crispy pack | `showcase.*_showcaseitem` permissions |
| `/admin/` | Django admin | staff |

Seeded demo users have no usable password and cannot sign in.

## Layout

- `src/django_tabler/`: the HTML shell and top-navbar layout (`templates/django_tabler/`), sign-in page, messages and
  form-field partials, the `{% icon %}` template tags (`{% load tabler %}`) and the Tabler icons. It does not depend on
  django-crud-views. It also holds the django-crispy-forms template pack for Tabler (`templates/crispy_tabler/`, with
  fields, widgets and layout objects in `django_tabler.crispy`), originally from `jacob-consulting/crispy-tabler`. The
  pack needs the `crispy` extra; everything else in the package works without crispy.
  A gear in the navigation lets each user pick the layout (top, side or folded navigation, width, navbar colour and
  style); the choice stays in that browser's `localStorage`, through Tabler's own `tabler-*` keys.
- `src/crud_views_tabler/`: Tabler theme for django-crud-views (template overrides, Tabler icon library, JS adapter),
  including `crud_views_tabler/page.html`, the page every crud_views view extends (`CRUD_VIEWS_EXTENDS`); design notes in
  [`docs/crud_views_tabler.md`](docs/crud_views_tabler.md)
- `example/`: the demo project: `manage.py`, `config/`, the `dashboard`, `customers` and `showcase` apps, and
  `templates/django_tabler/includes/`, whose `site_name.html`, `nav_menu.html` and `brand.html` override the package
  defaults with the Acme content
- `tests/crispy_tabler/`: the template pack's test suite; `scripts/vendor_templates.py` re-vendors its templates

## Settings from the environment

`DJANGO_SECRET_KEY`, `DJANGO_DEBUG` (`1`/`0`, default `1`) and `DJANGO_ALLOWED_HOSTS` (comma-separated).
The built-in secret key is for local development only.

## Tests

```shell
uv run python example/manage.py test django_tabler crud_views_tabler dashboard customers showcase
uv run --group test pytest                                                  # the crispy template pack
```

`crud_views_tabler`'s tests use the demo's `customers` app, so they run with the example's settings.
