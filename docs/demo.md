# Demo

**Acme Roasters** is a back office for a specialty coffee roastery, built with django-crud-views and themed by this
package. It covers customers with per-object permissions (Guardian), addresses, orders with a workflow and a line
formset, subscriptions, polymorphic products, ordered categories, green coffee lots, cupping sessions with score
formsets, roast batches and shipments from a fake courier API. Every crud_views page has a "Show code" panel with the
code behind it, and `/theming/` shows the whole theme.

The app code never imports the theme: it is a plain django-crud-views project with `crud_views_tabler` in
`INSTALLED_APPS`.

## Online

**https://django-crud-views-tabler-demo.onrender.com**

The public demo runs on Render's free plan; the first request after a pause may take a minute. Its data is reset every
night, so feel free to change things.

| Account | Password | Role |
|---|---|---|
| `alex` | `demo` | Owner: everything, including django-crud-views' manage pages |
| `sam` | `demo` | Account manager: only the customers granted to them |
| `kim` | `demo` | Roaster: lots, cupping and roasting; customers read-only |

## Locally

```shell
git clone https://github.com/jacob-consulting/django-crud-views-tabler.git
cd django-crud-views-tabler
task up      # uv sync, migrate, superuser admin/admin, seed the demo data, runserver
```

See [Development](development.md) for running it without Task, and for the sibling checkouts of django-crud-views
that local development uses.
