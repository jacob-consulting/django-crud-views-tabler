# crud_views_tabler: a Tabler theme for django-crud-views (draft)

Status: **prototype**, living in this project as the `crud_views_tabler` app and exercised by the `customers`
demo app (`/customer/`). Built against django-crud-views 0.29.4, Tabler 1.6.1 and crispy-bootstrap5 2026.9.

## Approach

django-crud-views has no theme setting (`CRUD_VIEWS_THEME` is ignored and raises `crud_views.W110`). Its own
hint describes the intended route, and the prototype follows it:

- a theme **app** ships templates under the `crud_views/` namespace,
- it is listed **before** `crud_views` in `INSTALLED_APPS`, so Django's app template loader finds its files first,
- anything it does not override falls through to the stock Bootstrap 5 templates.

So the theme is template overrides plus a little Python (icons, one form class) and two static files. No
crud_views code is patched or subclassed except where noted under "Forms".

```python
INSTALLED_APPS = [
    ...,
    "crispy_forms",
    "crispy_bootstrap5",
    "django_tables2",
    "django_filters",
    "crud_views_tabler",                 # before crud_views
    "crud_views.apps.CrudViewsConfig",
]
CRISPY_TEMPLATE_PACK = "bootstrap5"
CRUD_VIEWS_EXTENDS = "crud_views_page.html"                   # project template, see below
DJANGO_TABLES2_TEMPLATE = "crud_views/table/bootstrap5.html"  # the theme's table template
```

## The page: CRUD_VIEWS_EXTENDS

`templates/crud_views_page.html` is a **project** template, not part of the theme: it extends the app's own Tabler
layout (`layouts/app.html`, top navbar) and maps the crud_views pieces onto Tabler's page header:

| crud_views | Tabler page |
|---|---|
| `{% cv_breadcrumb %}` | `.breadcrumb` above the title |
| `{% cv_header_icon %}` + `{% cv_header %}` | `.page-title` |
| `{% cv_paragraph %}` | `.page-subtitle` |
| `{% cv_context_actions object %}` | the page header's action area (`.btn-list`) |
| `cv_filter`, `cv_content` blocks | `.page-body` |
| `{% cv_css %}` / `{% cv_js %}` / `{% cv_config %}` | head / end of body / modal shell |

A reusable theme could ship a default version of this page; the prototype keeps it in the project because the
surrounding layout (navbar, footer) is the project's.

## Header and actions

This is where crud_views and Tabler line up best: Tabler's page header has a title area and an actions area,
and crud_views has a header snippet and **context actions**.

- **Context actions** (`tags/context_actions.html`, `tags/context_action.html`) render as a `.btn-list` in the
  page header. `create` / `create_select` is the page's primary action: `btn-primary` with its label. Every other
  key is an icon button (`btn btn-icon`) with a tooltip; the label stays in a `.visually-hidden` span, as
  crud_views requires for accessibility. The current view's key gets `active` + `aria-current`.
- **Row actions** (`columns/actions.html`, `tags/list_action.html`) are small ghost icon buttons
  (`btn-sm btn-icon btn-ghost-secondary`, `btn-ghost-danger` for `delete`), right-aligned and never wrapping.
- **Overflow menu** (`tags/actions_menu_*.html`): the `⋯` toggle and its dropdown items use Tabler icons
  (`dropdown-item-icon`). The `{% if group is None %}` branch crud_views needs for menus is kept.
- All hooks the package's JavaScript relies on are kept unchanged: `cv-key`, `cv-list-container`,
  `cv-context-container`, `data-cv-action`, `data-cv-target`, `data-cv-modal`, `#cv-filter-toggle`, the hidden POST
  forms from `list_action_form.html`.

## Sorting

Sorting stays server-side django-tables2 ordering; only the header changes (`table/bootstrap5.html`):

- an orderable header is `<a class="table-sort [asc|desc]" href="?sort=…">`. Tabler's `.table-sort` draws the
  neutral, ascending and descending arrows in CSS, so no JavaScript (Tabler's demo uses List.js; not needed here),
- the `<th>` gets `aria-sort="ascending|descending|none"`,
- the state comes from `column.is_ordered` / `column.order_by_alias.is_descending` instead of comparing
  `request.GET.sort` as the stock template does, so it also works for tables with a `prefix`,
- the next link is still built with `{% cv_querystring %}`, so filters and paging survive a sort change and the
  filter form keeps the sort.

## Pagination

The table renders as a whole card: `.card > .table-responsive > table.table.table-vcenter.card-table`, and a
`.card-footer` with "Showing x–y of n" and a Tabler `.pagination` with chevron icons. `snippets/pagination.html`
(card views) uses the same look.

## Forms (crispy)

crispy-bootstrap5 needs **no template overrides**: Tabler is Bootstrap 5, so `form-label`, `form-control`,
`form-select`, `form-check`, `is-invalid` and `invalid-feedback` render natively, including in dark mode.
Remaining gaps and how the prototype handles them:

- **Required marker**: crispy prints `<span class="asteriskField">*</span>`; the theme CSS colours it like Tabler's
  `.form-label.required`.
- **Button colours**: crispy's `Submit` is always `btn btn-primary`, so `CrispyDeleteForm`'s Delete button is blue.
  The theme ships `crud_views_tabler.forms.DangerSubmit` and `TablerDeleteForm` (full-width confirm, red Delete);
  the demo uses `form_class = TablerDeleteForm`. Cancel buttons stay `btn-secondary` (set in crud_views'
  `get_cancel_button_kwargs`).
- **Cards vs. modals**: `view_create/update/delete.content.html` wrap the form in a card on a full page and leave it
  bare inside a modal, by checking `request.headers.x_cv_modal` (the header crud_views' modal.js sends).
- A dedicated crispy template pack for Tabler is **not** needed for this level of fidelity; it would only pay off
  for Tabler-only widgets (input icons, floating labels, selectgroups).

## Filter

The filter renders as a Tabler card with a titled header inside crud_views' collapse (`tags/list_filter*.html`).
The crispy filter form itself needs nothing. `CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS` controls the reset button.

## Icons

crud_views names icons with Font Awesome classes, hard-coded on the view classes (`cv_icon_action =
"fa-regular fa-eye"`) and in two settings. Rather than requiring every project to subclass its views, the theme
maps them at render time:

- `crud_views_tabler/icons.py` holds Tabler outline icons as SVG paths plus a Font Awesome → Tabler table for every
  default crud_views ships,
- `{% cvt_icon value %}` renders inline SVG for a Tabler name (`"building-store"`) or a known Font Awesome class,
  and falls back to the original `<i class="…">` for anything else, so a project that also loads Font Awesome
  keeps working,
- a ViewSet can use Tabler names directly: `ViewSet(..., icon_header="building-store")`.

Side effect: list.filter.js toggles `fa-filter` on an `<i>` inside the filter button; with SVG that does nothing
(harmless, the button simply doesn't swap icons).

## JavaScript

crud_views' scripts expect **jQuery** (list.filter.js, formset.js) and a global **`bootstrap`** (modal.js,
tooltip.js). Tabler's bundle has no jQuery and exposes Bootstrap's components on `window.tabler`. The theme's
`shared/js.html` (what `{% cv_js %}` renders) therefore emits, all `defer`red so they run after `tabler.min.js`:

1. jQuery 3.7.1 from code.jquery.com with an SRI hash,
2. `crud_views_tabler/bootstrap-shim.js`: `window.bootstrap = window.tabler`, and registers Bootstrap's jQuery
   plugins (`$.fn.collapse`, …), which Bootstrap only does itself when jQuery is loaded before it,
3. crud_views' own scripts.

Without step 2 the filter toggle fails with `collapse.collapse is not a function`.

## Overridden templates

```
crud_views/
  columns/actions.html            row actions
  modal/content.html              modal header icon
  shared/js.html                  jQuery + shim + deferred scripts
  snippets/pagination.html        card-view pagination
  table/bootstrap5.html           card table, sort headers, footer pagination
  tags/actions_menu_item_label.html, actions_menu_toggle.html
  tags/breadcrumb.html
  tags/context_action.html, context_action_filter.html, context_actions.html
  tags/icon.html                  header/filter icon -> Tabler SVG
  tags/list_action.html (+ list_action.inner.html)
  tags/list_filter.html, list_filter.inner.html
  view_create.content.html, view_update.content.html, view_delete.content.html
```

## Not covered yet

- **Card views** (`view_card*.html`, `tags/card.html`, `tags/card_action.html`, `snippets/card_order.html`).
- **Property-grid detail** (`crud_views_object_detail`): it has its own template packs and icon library settings
  (`bootstrap` / `fontawesome`); a Tabler datagrid layout would be the natural fit. The demo detail page uses a
  hand-written Tabler `.datagrid` instead.
- **Formsets** (`formsets/*.html`, formset.js), **delete related-objects** snippets, the **manage** view,
  **language selector**, and the workflow / polymorphic / guardian extensions' templates.
- Filter button state (active/open) and a Tabler-style cancel button.
- Responsive check below the `md` breakpoint.

## Questions for django-crud-views upstream

1. Icons: a setting or registry for action icons (instead of Font Awesome classes on view classes) would let a
   theme swap icon sets without a render-time mapping.
2. Button classes: crud_views sets `btn btn-secondary` for Cancel and plain `Submit` for Delete in Python; a hook
   or setting for these would avoid the `TablerDeleteForm` subclass.
3. jQuery: list.filter.js only needs it for click handlers and `collapse("toggle")`; dropping jQuery there would
   remove the theme's biggest shim.
4. A "primary" flag for context actions (today the theme hard-codes `create`/`create_select`).
