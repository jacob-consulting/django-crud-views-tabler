# Acme Admin

Django 6.1 app with a Tabler 1.6.1 UI (loaded from the jsDelivr CDN), Django's built-in authentication and a
prototype Tabler theme for django-crud-views.

## Run it

```shell
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py seed_demo_users       # optional: 40 sample accounts so the charts have data
uv run python manage.py seed_demo_customers   # optional: 60 sample customers for the crud_views demo
uv run python manage.py runserver
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
| `/admin/` | Django admin | staff |

Seeded demo users have no usable password and cannot sign in.

## Layout

- `templates/base.html`: HTML shell, Tabler CSS/JS with SRI hashes
- `templates/layouts/app.html`: top-navbar page layout; `templates/includes/` holds the navbar, messages and form-field partials
- `templates/registration/login.html`: sign-in page used by Django's `LoginView`
- `dashboard/`: views, the user form, the `{% icon %}` template tag (`templatetags/tabler.py`), the seed command and tests
- `crud_views_tabler/`: prototype Tabler theme for django-crud-views (template overrides, Tabler icon library, JS adapter);
  design notes in [`docs/crud_views_tabler.md`](docs/crud_views_tabler.md)
- `customers/`: demo ViewSet that exercises the theme
- `templates/crud_views_page.html`: the page every crud_views view extends (`CRUD_VIEWS_EXTENDS`)

## Settings from the environment

`DJANGO_SECRET_KEY`, `DJANGO_DEBUG` (`1`/`0`, default `1`) and `DJANGO_ALLOWED_HOSTS` (comma-separated).
The built-in secret key is for local development only.

## Tests

```shell
uv run python manage.py test
```
