# Acme Admin

Django 6.1 app with a Tabler 1.6.1 UI (loaded from the jsDelivr CDN) and Django's built-in authentication.

## Run it

```shell
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py seed_demo_users   # optional: 40 sample accounts so the charts have data
uv run python manage.py runserver
```

Open http://127.0.0.1:8000/ and sign in. Every page except the login page requires a signed-in user
(`LoginRequiredMiddleware`).

## Pages

| URL | What | Who |
|---|---|---|
| `/accounts/login/` | Sign-in | everyone |
| `/` | Dashboard: account stats, sign-ups per month, roles, recent sign-ins | signed-in users |
| `/users/` | Searchable, paginated user list | `auth.view_user` permission |
| `/users/new/` | Create a user (the form opens as a modal on the list) | `auth.add_user` permission |
| `/admin/` | Django admin | staff |

Seeded demo users have no usable password and cannot sign in.

## Layout

- `templates/base.html`: HTML shell, Tabler CSS/JS with SRI hashes
- `templates/layouts/app.html`: top-navbar page layout; `templates/includes/` holds the navbar, messages and form-field partials
- `templates/registration/login.html`: sign-in page used by Django's `LoginView`
- `dashboard/`: views, the user form, the `{% icon %}` template tag (`templatetags/tabler.py`), the seed command and tests

## Settings from the environment

`DJANGO_SECRET_KEY`, `DJANGO_DEBUG` (`1`/`0`, default `1`) and `DJANGO_ALLOWED_HOSTS` (comma-separated).
The built-in secret key is for local development only.

## Tests

```shell
uv run python manage.py test
```
