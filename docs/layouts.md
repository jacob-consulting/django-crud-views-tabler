# Layouts

`django_tabler/layouts/app.html` renders Tabler's top bar or its sidebar, fluid or boxed, light or dark. Two things
decide which one a user sees.

## The project default

`django_tabler/includes/layout_defaults.html` holds a JSON object with Tabler's layout settings (keys `layout`,
`navbar-position`, `navbar-style`, `navbar-theme`, `sidebar`). It is empty in the
package, which gives Tabler's own default (top bar). The demo uses a dark sidebar:

```json
{"navbar-position": "vertical", "navbar-theme": "dark"}
```

The `{% layout_defaults_attrs %}` tag on `<html>` (in `django_tabler/base.html`) turns this into `data-bs-<key>`
attributes, which Tabler's `tabler-theme.js` applies when the user has not chosen anything.

## The user's choice

A gear in the navbar opens the layout switch: Top, Side, Folded, Fluid, Boxed, Dark, Floating. The choice is stored in
the browser's `localStorage` under Tabler's own `tabler-*` keys, so it survives reloads and applies on every page. A
choice equal to the project default is not stored, so changing the default later reaches users who never picked
anything else.

!!! note "Primary colour themes"
    Tabler's primary-colour themes (`data-bs-theme-primary`, `?theme-primary=…`) need `tabler-themes.min.css`, which
    `django_tabler/base.html` does not load. Such a choice shows Tabler's base blue, and the switch offers no colour
    choice. Set the colour in CSS instead (see [Branding](branding.md)).
