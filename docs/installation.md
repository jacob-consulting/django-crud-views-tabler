# Installation

```shell
pip install django-crud-views-tabler
```

This installs django-crud-views, django-crispy-forms and crispy-bootstrap5 with it. For django-crud-views' optional
features (workflow, polymorphic, ordered, guardian) install its extras as usual, e.g.
`pip install "django-crud-views[workflow]"`.

## `INSTALLED_APPS`

The theme overrides crud_views templates, so **`crud_views_tabler` must come before `crud_views`**. Django's app
template loader then finds the theme's files first; anything the theme does not override falls through to the stock
templates.

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "crispy_forms",
    "django_tables2",
    "django_filters",
    "django_tabler",
    "crud_views_tabler",  # before crud_views
    "crud_views.apps.CrudViewsConfig",
    # crud_views_workflow, crud_views_polymorphic, ... as you use them
    "your_app",
]
```

`crispy_bootstrap5` does not need to be in `INSTALLED_APPS`: the pack's templates live in `django_tabler`, and only
two layout objects subclass crispy-bootstrap5's Python classes.

## Settings

```python
# Pages of django-crud-views extend the theme's page template (or your own template that extends it).
CRUD_VIEWS_EXTENDS = "crud_views_tabler/page.html"

# Forms render through the Tabler template pack.
CRISPY_ALLOWED_TEMPLATE_PACKS = ("crispy_tabler",)
CRISPY_TEMPLATE_PACK = "crispy_tabler"

# django-tables2 tables use the theme's table template.
DJANGO_TABLES2_TEMPLATE = "crud_views/table/bootstrap5.html"
```

Check the configuration with Django's system checks; the theme adds `crud_views_tabler.W001` (an icon name with no
SVG path):

```shell
python manage.py check --fail-level WARNING
```

## Your own page layer

To add something to every crud_views page (a panel, a script), point `CRUD_VIEWS_EXTENDS` at your own template that
extends the theme's page. The demo does this for its "Show code" panel:

```django
{% extends "crud_views_tabler/page.html" %}
{% block actions %}{{ block.super }}<a class="btn" href="#help">Help</a>{% endblock %}
```

The blocks available are those of `django_tabler/layouts/app.html`: `page_header_before`, `page_header_top`,
`breadcrumb`, `page_heading` (wraps `page_title`), `subtitle`, `actions`, `messages`, `content`, plus `extra_head` and
`extra_js` from `django_tabler/base.html`.

## Pages outside django-crud-views

Any template can use the shell directly:

```django
{% extends "django_tabler/layouts/app.html" %}
{% block title %}Reports{% endblock %}
{% block page_title %}Reports{% endblock %}
{% block content %}<div class="card"><div class="card-body">…</div></div>{% endblock %}
```

`django_tabler` also ships `registration/login.html`, a Tabler sign-in page for Django's `LoginView`, with a
`login_after` block below the form.
