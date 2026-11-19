# Icons

`django_tabler.icons.ICONS` maps [Tabler icon](https://tabler.io/icons) names (outline style) to their SVG paths.
Icons render inline, so no icon font or sprite is loaded.

## In templates

```django
{% load tabler %}
{% icon "users" %}
{% icon "alert-triangle" "icon-sm text-warning" %}
```

An unknown name renders nothing.

## In django-crud-views

The theme registers an icon library `tabler` with django-crud-views and maps crud_views' semantic icon names (list,
detail, create, update, delete, …) to Tabler icons. Your own views can name any icon in `ICONS` with the `tabler:`
prefix:

```python
class CustomerDetailView(DetailViewPermissionRequired):
    cv_icon_action = "tabler:star"
```

The system check `crud_views_tabler.W001` warns about a `tabler:` name that has no path in `ICONS`.

## Adding icons

`ICONS` covers the icons the theme and the demo use. To add more in a project, extend the dictionary at startup (for
example in an `AppConfig.ready()`) with the `d` attributes of the icon's `<path>` elements, as in the icon's SVG file
from [tabler-icons](https://github.com/tabler/tabler-icons):

```python
from django_tabler.icons import ICONS

ICONS["rocket"] = [
    "M4 13a8 8 0 0 1 7 7a6 6 0 0 0 3 -5a9 9 0 0 0 6 -8a3 3 0 0 0 -3 -3a9 9 0 0 0 -8 6a6 6 0 0 0 -5 3",
    ...,
]
```
