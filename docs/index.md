# Django CRUD Views Tabler

Current version: 0.1.0

A [Tabler](https://tabler.io) 1.6.1 theme for [django-crud-views](https://django-crud-views.readthedocs.io/). One
distribution, `django-crud-views-tabler`, ships two Django apps:

- **`crud_views_tabler`**: the theme. Listed before `crud_views` in `INSTALLED_APPS`, it shadows the layout templates
  of django-crud-views' stock Bootstrap 5 theme and registers Tabler button classes, icons and JavaScript adapters
  through upstream's hooks. Your ViewSets and views need no changes.
- **`django_tabler`**: a Tabler page shell that does not depend on django-crud-views: base template and app layout
  (top bar or sidebar), sign-in page, `{% load tabler %}` icon tags, an end-user layout switch, and `crispy_tabler`,
  a django-crispy-forms template pack with Tabler markup.

Tabler's CSS and JavaScript load from the jsDelivr CDN; nothing from Tabler is bundled.

Supported: Python 3.12–3.15, Django 5.2, 6.0 and 6.1, django-crud-views 1.0.

- [Installation](installation.md): settings, in the order they matter.
- [Branding](branding.md) and [Layouts](layouts.md): site name, logo, menu, default layout.
- [Icons](icons.md) and the [crispy template pack](crispy_tabler.md).
- [Theme internals](theme_internals.md): what is overridden and why, and every hook the theme uses.
- [Demo](demo.md): Acme Roasters, a back office for a coffee roastery, built with django-crud-views and this theme.
  Live at [django-crud-views-tabler-demo.onrender.com](https://django-crud-views-tabler-demo.onrender.com).
