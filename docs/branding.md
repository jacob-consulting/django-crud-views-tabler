# Branding

Branding is done by overriding small include templates of `django_tabler`. Put files with the same path in a
directory listed in `TEMPLATES[0]["DIRS"]`, which Django searches before app templates.

| Template | Default | Purpose |
|---|---|---|
| `django_tabler/includes/site_name.html` | `Django Tabler` | Name in the `<title>`, the navbar and the sign-in page |
| `django_tabler/includes/brand.html` | site name | Logo and name in the navbar and the sidebar |
| `django_tabler/includes/head.html` | empty | Extra `<head>` content on every page: favicon, stylesheets |
| `django_tabler/includes/nav_menu.html` | empty | The menu entries (see below) |
| `django_tabler/includes/user_menu_items.html` | admin links for staff, Sign out | The user dropdown (keep the Sign out form when overriding) |
| `django_tabler/includes/layout_defaults.html` | empty (comment only) | The project's default layout (see [Layouts](layouts.md)) |

The demo's files are in
[`example/templates/django_tabler/includes/`](https://github.com/jacob-consulting/django-crud-views-tabler/tree/main/example/templates/django_tabler/includes).

## Brand and colour

```django
{# templates/django_tabler/includes/brand.html #}
{% load tabler %}<a href="{% url 'home' %}" class="d-inline-flex align-items-center gap-2 text-reset text-decoration-none">
  <span class="avatar avatar-sm bg-primary text-white">{% icon "coffee" %}</span>
  <span>{% include "django_tabler/includes/site_name.html" %}</span>
</a>
```

The primary colour is Tabler's CSS variable; set it in a stylesheet loaded from `head.html`:

```css
:root { --tblr-primary: #a0522d; --tblr-primary-rgb: 160, 82, 45; }
```

## The menu

`nav_menu.html` is included twice: by the top bar with `nav_layout="horizontal"` and by the sidebar with
`nav_layout="vertical"`. Render `<li class="nav-item">` entries; use `nav_layout` to show sections as dropdowns in
the top bar and as headings in the sidebar:

```django
{% load tabler %}
<li class="nav-item">
  <a class="nav-link" href="{% url 'customer-list' %}">
    <span class="nav-link-icon">{% icon "users" %}</span><span class="nav-link-title">Customers</span>
  </a>
</li>
{% if nav_layout != "horizontal" %}
<li class="nav-item nav-section mt-2"><div class="nav-link text-uppercase small text-secondary">Catalog</div></li>
{% endif %}
```

The demo builds its menu, with permission checks and the active entry, in one template tag
([`example/config/templatetags/acme_nav.py`](https://github.com/jacob-consulting/django-crud-views-tabler/blob/main/example/config/templatetags/acme_nav.py)).
