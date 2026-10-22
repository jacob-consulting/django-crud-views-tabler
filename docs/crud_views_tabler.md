# crud_views_tabler: a Tabler theme for django-crud-views (draft)

Status: **prototype**, living in this project as the `crud_views_tabler` app and exercised by two
demo apps: `customers` (`/customer/` table list, `/customer/card/` card view) and `catalog` (`/product/`), whose
create form renders every crispy template branch on one page — see [crispy_tabler_coverage.md](crispy_tabler_coverage.md). Built against django-crud-views @ 1727a75 (branch `feat/alert-template`, PR #252, not merged yet; 0.30.0 plus the unreleased JavaScript adapters #200, button variants, class table and leaves #201, tooltip markers #204 and tooltip lifecycle #205, the three-state card button label mode #213, the removal of the dead crispy detail templates #217, `{% cv_messages %}` instead of django-bootstrap5 #222, label-mode class keys #209 and context/list label mode #216, utility class keys #227, `hidden` instead of `d-none` #232, form media once #191, multipart create forms #236, the form frame #239, the translated card empty state #246, accessible card pagination #241, card blocks and class keys #243 and the alert frame #250, installed as an editable path dependency from the sibling checkout `../django-crud-views`), Tabler 1.6.1 and crispy-bootstrap5 2026.9.

## Approach

django-crud-views has no theme setting (`CRUD_VIEWS_THEME` is ignored and raises `crud_views.W110`). Its own
hint describes the intended route, and the prototype follows it:

- a theme **app** ships templates under the `crud_views/` namespace,
- it is listed **before** `crud_views` in `INSTALLED_APPS`, so Django's app template loader finds its files first,
- anything it does not override falls through to the stock Bootstrap 5 templates.

So the theme is template overrides plus a little Python (the icon library, the button class table, a system check) and two static files (a stylesheet and the adapter script). No
crud_views code is patched or subclassed.

```python
INSTALLED_APPS = [
    ...,
    "crispy_forms",
    "crispy_tabler",
    "django_tables2",
    "django_filters",
    "crud_views_tabler",                 # before crud_views
    "crud_views.apps.CrudViewsConfig",
]
CRISPY_TEMPLATE_PACK = "crispy_tabler"
CRISPY_ALLOWED_TEMPLATE_PACKS = ("crispy_tabler",)
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

The theme overrides **no** button template. Every action button, the row and toolbar containers, the `⋯` menu
toggle, the filter toggle and the card-order bar render through crud_views' stock logic templates and leaves
(`tags/button/action.html`, `menu_item.html`, `container.html`). The Tabler look comes from crud_views' button class
table: `crud_views_tabler/buttons.py` holds `TABLER_BUTTON_CLASSES`, and `CrudViewsTablerConfig.ready()` registers it
with `register_button_classes()`, so projects need no button settings. A project overrides single keys with
`CRUD_VIEWS_BUTTON_CLASSES` (project settings win over the theme).

Which classes a button gets depends on its **variant**, which comes from the view it targets: `create` /
`create_select` are `primary`, `delete` is `danger`, everything else `secondary`. A view changes it with
`cv_action_variant`, a single button with `ContextButton.variant` / `CardAction.variant`.

- **Label mode decides `btn-icon`.** Tabler's `btn-icon` squares a button, which only suits an icon-only one. The
  table therefore holds each action key twice: `location:variant` without `btn-icon` for a labelled button (label
  mode `label` or `both`), and `location:variant:icon` with it (#209). crud_views reads the mode key when it is
  present and falls back to the base key otherwise.
- **Context actions** render as a `fieldset.btn-list` in the page header. They are icon-only by default (crud_views'
  default for toolbar and row buttons): `btn btn-icon`; the primary action (create) is `btn btn-primary btn-icon`,
  a danger action (delete on a detail page) `btn btn-icon btn-outline-danger`. The label stays in a
  `.visually-hidden` span and is the tooltip. A view that shows labels (`cv_context_actions_label_mode`, #216) gets
  the same buttons without `btn-icon`. The current view's key gets `active` + `aria-current`.
- **Row actions** are small ghost buttons (`btn btn-sm btn-icon btn-ghost-secondary` icon-only, `btn-ghost-danger`
  for danger; without `btn-icon` when `cv_list_actions_label_mode` shows a label), in a `fieldset.btn-list` that is
  right-aligned and never wraps.
- **Overflow menu**: the `⋯` toggle uses the same icon-button classes per location inside a Tabler `dropdown`
  wrapper; crud_views adds `dropdown-toggle`, so it shows a caret. The dropdown items are crud_views' own; the
  stylesheet sizes and mutes their `.cv-icon-fw` icon slot like Tabler's `dropdown-item-icon`, so labels line up
  whether an action has an icon or not.
- **Tooltips**: crud_views marks every icon-only button with `data-cv-tooltip="<location>"` and initialises it
  through `cv.adapters.tooltip`, which the theme points at Tabler (see JavaScript). Toolbar tooltips open below the
  button. A click hides the clicked button's tooltip, and tooltips inside the modal are disposed before its content is
  replaced (#205).
- All hooks the package's JavaScript relies on come from the stock templates unchanged: `cv-key`,
  `cv-list-container`, `cv-context-container`, `cv-card-container`, `data-cv-action`, `data-cv-target`,
  `data-cv-modal`, `#cv-filter-toggle`, the hidden POST forms.

**Accepted differences from the earlier theme overrides** (stock markup wins over the old look):

| Where | Before | Now |
|---|---|---|
| Toolbar "Create" | `btn-primary` with icon and text label | icon-only `btn-primary`; the label is the tooltip |
| Labelled card buttons ("Open", "Edit") | icon plus label | icon plus label again (crud_views' card default `both`, #213) |
| `⋯` menu toggles | no caret | caret (`dropdown-toggle`) |
| Row and toolbar containers | `div.btn-list` | `fieldset.btn-list` (lays out the same) |
| Card-order bar | `form-label text-secondary` label, full-size select, `aria-pressed` | crud_views' bar: plain label, `form-select-sm`, `active` only |
| Delete form | confirmation checkbox full width | crud_views' `Row(Column4("confirm"))` |

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
`.card-footer` with "Showing x–y of n" and a Tabler `.pagination`. Card views use crud_views' own
`snippets/pagination.html` (#241: `aria-current`, `aria-disabled`, translated hidden labels), which is Tabler's own
pagination markup, so the theme no longer overrides it. Both paginations take their arrows from the semantic icon
names `page-previous` / `page-next`, which the theme maps to Tabler's chevrons at the standard icon size, as in
Tabler's examples (the old override used `icon-sm`). A project changes them with `CRUD_VIEWS_ICONS`.

## Card views

`CardListView` pages (`view_card.content.html`, `tags/card.html`; the card buttons and the order bar are crud_views'
own):

- cards sit in a `.row.row-deck.row-cards` grid, so cards in a row share their height;
  `cv_card_container_class` still sets the column width (the demo uses `col-sm-6 col-lg-4`),
- each card is `.card > .card-body` (title + content) and a `.card-footer`, which includes crud_views' container
  leaf (`tags/button/container.html`, a `div.btn-list`) for the actions and the overflow menu. The footer is why the
  theme still overrides `tags/card.html`: crud_views' card keeps its actions inside the body, and where they sit is
  structure, not classes (#243). The override uses crud_views' block names and its `card:root` / `card:body` /
  `card:title` class keys; the theme registers `card:root` = `card` (crud_views' default adds `mb-3`, which the
  `row-deck` grid does not need),
- variants map to Tabler buttons through the class table: `primary` → `btn btn-sm btn-primary`, `secondary` → the
  default `btn btn-sm`, `tertiary` → `btn btn-sm btn-ghost-secondary`, `danger` → `btn btn-sm btn-ghost-danger`;
  `flex` → `flex-grow-1`. Labelled buttons show icon and label (crud_views' card default, label mode `both`),
- icon-only buttons (`CardAction(label_mode="icon")`, as the demo's delete) use the `card:<variant>:icon` keys, which
  add `btn-icon`; they keep a `.visually-hidden` label and get a tooltip,
- the order bar is crud_views' `snippets/card_order.html` with Tabler's sort-ascending / sort-descending icons and
  the `card-order:*` classes (`btn btn-icon` in a `btn-group`); signed ordering (`submit-on-change`) is unchanged,
- no results render Tabler's `.empty` state; pagination is crud_views' `snippets/pagination.html` (see Pagination).

**Custom card content** without repeating the actions markup: a view's `cv_card_template` extends
`crud_views/tags/card.html` and fills crud_views' blocks (`card_title`, `card_content`, `card_actions`; #243). Under
this theme that resolves to the Tabler card, so the same template works with or without the theme. Emptying
`card_actions` drops the footer along with the actions:

```html
{% extends "crud_views/tags/card.html" %}
{% block card_title %}{{ object.name }} <span class="badge bg-{{ object.status_badge }}-lt">…</span>{% endblock %}
{% block card_content %}<div class="text-secondary">{{ object.company }}</div>{% endblock %}
```

(This only works because the template has a different name than the one it extends; overriding
`crud_views/tags/card.html` itself must not extend it.)

**Getting back to the cards.** With both a list and a card view, create / update / delete return to `"list"` by
default. Set `cv_cancel_keys` / `cv_success_keys` (e.g. `["list", "card"]`, plus `"detail"` where an object
remains) so they return to the view the user came from; the links then carry `?cv_from=card`. The theme's form
templates post to `request.get_full_path`, which keeps that origin across validation errors.

## Forms (crispy)

The demo renders forms through the sibling template pack `crispy_tabler` (`CRISPY_TEMPLATE_PACK = "crispy_tabler"`;
see [crispy_tabler_coverage.md](crispy_tabler_coverage.md) for what it fixes). The theme app itself needs **no
crispy template overrides**: Tabler is Bootstrap 5, so `form-label`, `form-control`, `form-select`, `form-check`,
`is-invalid` and `invalid-feedback` render natively with either pack, including in dark mode. `crispy_bootstrap5`
is **not** in `INSTALLED_APPS` and nothing needs it: upstream removed `crud_views/detail/` — the last templates in
the package carrying hardcoded `bootstrap5/...` includes — in 10d81ad (#217), so the former precaution is gone (see
[crispy_tabler_coverage.md](crispy_tabler_coverage.md)). The `crispy-bootstrap5` *distribution* stays installed, as a
dependency of `crispy-tabler`, whose `layout` module subclasses its `FloatingField` and `Switch`. Remaining gaps and
how the prototype handles them:

- **Required marker**: crispy prints `<span class="asteriskField">*</span>`; the theme CSS colours it like Tabler's
  `.form-label.required`.
- **Button colours**: crud_views' crispy buttons (`crud_views.lib.crispy.Submit`, `Button`, `Reset`) take their
  classes from the button class table. The theme sets only `form:delete` to `btn btn-danger`, so the stock
  `CrispyDeleteForm` (which the demo's delete view uses) has a red Delete button; submit, cancel, filter submit and
  reset keep crud_views' `btn-primary` / `btn-secondary`. The theme's former `TablerDeleteForm` and `DangerSubmit`
  were removed.
- **Cards vs. modals**: `view_create/update/delete.content.html` wrap the form in a card on a full page and leave it
  bare inside a modal, by checking `request.headers.x_cv_modal` (the header crud_views' modal.js sends).
- A dedicated pack turned out to be needed after all for the range, colour, read-only, fieldset and form-actions
  paths (six findings, now fixed in `crispy_tabler`); plain Bootstrap 5 markup was enough only for the common inputs.

## Filter

The filter renders as a Tabler card with a titled header inside crud_views' collapse (`tags/list_filter*.html`).
The crispy filter form itself needs nothing; the reset button's classes are the `form:filter-reset` key of the
button class table. The toggle button in the page header is crud_views' own `tags/context_action_filter.html`
(classes from `context:secondary`); it follows list.filter.js' contract, so the icon swaps between filter and
filter-x and matches the session state after a reload.

## Icons

django-crud-views 0.30.0 refers to icons by semantic name (`detail`, `delete`, `filter`, …), resolves names through a
layered table (package defaults, theme registrations, `CRUD_VIEWS_ICONS`) to `prefix:name` values, and renders every
icon through `{% cv_icon %}` with a renderer per library prefix. The theme plugs into that:

- `crud_views_tabler/icons.py` holds Tabler outline icons as SVG paths (`ICONS`), the registry renderer `render`
  (inline SVG with `class="icon …"` and `aria-hidden`), and `TABLER_ICONS`: a Tabler icon for every semantic name
  the package defines (34 names, from `detail` to the formset, object-detail, `message-*` and `page-*` icons),
- `CrudViewsTablerConfig.ready()` registers the library (`register_icon_library("tabler", renderer=…)`) and the table
  (`register_icons(TABLER_ICONS)`), so a project needs no icon settings; formset, boolean, object-detail and
  language-selector icons are Tabler too, without a template override,
- the theme's templates use `{% cv_icon "sort-asc" %}` for semantic names and `{% cv_icon "tabler:chevron-left" %}`
  for Tabler-only icons; a ViewSet or view uses `icon_header="tabler:building-store"`,
- a project overrides any name with `CRUD_VIEWS_ICONS = {"detail": "tabler:zoom"}` (or a value from another
  library); a `tabler:` value without a path in `ICONS` renders nothing and is reported by the system check
  `crud_views_tabler.W001`.

The `dashboard` app's `{% icon %}` tag renders the same SVGs through the plain `icons.svg()` function.

The theme's former template library (`{% load crud_views_tabler %}` with `{% cvt_icon %}`) and
`crud_views_tabler.icons.render_icon` were removed: use `{% cv_icon %}` and `icons.svg()`. Font Awesome classes set
directly on a project's views (e.g. `cv_icon_action = "fa-regular fa-eye"`) are no longer mapped to Tabler SVG: use a
semantic name or a `tabler:` value instead.

## JavaScript

Core scripts on django-crud-views main run without jQuery and call Bootstrap only through `cv.adapters` (`modal`,
`tooltip`, `collapse`). Tabler's bundle exposes Bootstrap's components on `window.tabler`, so the theme registers one
asset, `crud_views_tabler/tabler-adapters.js`:

    Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler));
    cv.adapters.tooltip.init = (el, {location} = {}) => { /* Tabler Tooltip, "bottom" for location "context" */ };

The second statement is crud_views' per-location recipe (`docs/reference/javascript.md#tooltips`): toolbar tooltips
open below the buttons, so they do not cover the page header; it does nothing while `window.tabler` has no
`Tooltip`. Only `init` is replaced, so the adapter keeps crud_views' optional `hide(el)` and `dispose(el)` (#205),
which resolve `tabler.Tooltip` through the same namespace: `tooltip.js` hides a trigger's tooltip on click and disposes
the tooltips under `#cv-modal` on `cv:modal:unload`, so Tabler's per-tooltip `hide.bs.modal` handlers do not pile up
over repeated modal opens. Do not reassign `cv.adapters.tooltip` as a whole in the theme; that would drop both.

The namespace is resolved on every call, so `tabler.min.js` stays `defer`red at the end of the body while the
crud_views scripts load synchronously from `{% cv_js %}`. The theme loads no jQuery; a project with formsets loads it
in its own base template (`formset.js` is the only core script that needs it).

The theme follows the modal and filter contracts of main: `modal/shell.html` is overridden with Tabler's `modal-blur`
and a centered dialog (the ids `cv-modal`, `cv-modal-dialog`, `cv-modal-content` are the contract), crud_views' own
`modal/content.html` closes through `data-cv-modal-dismiss`, `cv_modal_size` takes `""`, `"sm"`, `"lg"` or `"xl"`, and
the filter toggle carries `aria-expanded`, `aria-controls="filter-collapse"` and both filter icons. crud_views' own
buttons carry `data-cv-tooltip`, so core's `tooltip.js` initialises their tooltips through the adapter, including
inside modal content, which Tabler's own page-load initialisation never sees.

## Overridden templates

Eight templates, all about page layout; none of them renders a button:

```
crud_views/
  modal/shell.html                Tabler modal shell (modal-blur, centered)
  snippets/form_frame.html        card around the form on create/update/delete/custom-form pages, bare in a modal
  table/bootstrap5.html           card table, sort headers, footer pagination
  tags/card.html                  actions in a .card-footer; crud_views' blocks and card:* class keys
  tags/alert.html                 every alert (messages, delete page) in Tabler's layout: .alert-icon, .alert-heading
  tags/list_filter.html, list_filter.inner.html   filter as a Tabler card
  view_card.content.html          card grid and empty state
static/crud_views_tabler/
  crud_views_tabler.css           required marker, row actions, filter card spacing, modal title, menu icons
  tabler-adapters.js              cv.adapters -> window.tabler, toolbar tooltips below
```

The theme used to override the context, list and card action templates, both containers, the `⋯` toggle, the filter
toggle and the card-order bar (nine templates). crud_views' class table, leaves and tooltip markers made all of them
unnecessary.

The form pages used to be three full copies (`view_create`, `view_update`, `view_delete` `.content.html`) whose only
change was the card around the form. Being copies, they missed two upstream fixes until the theme caught up: the
create form's `enctype="multipart/form-data"` (#236, file fields arrived empty) and `{{ form.media }}` after the form
(#191, widget media rendered twice). Since #239 the four form content templates extend
`crud_views/snippets/form_frame.html`, so the theme overrides only that frame; the `<form>`, its `enctype`, `action` and media handling are upstream's
again (custom-form pages get the card too). Tests pin the frame, the bare modal and that the content templates are
not overridden.

The demo's flash messages render with crud_views' `{% cv_messages %}` (#222) in `layouts/app.html`; the demo's own
`includes/messages.html` is gone.

**Alerts** (#250): crud_views renders every alert — the flash messages, the delete page's protection and
related-objects alerts — through one frame, `crud_views/tags/alert.html`, with the body chosen in Python (a text
snippet, a list snippet, or the related-objects tree). The theme overrides only that frame: the level icon in
`.alert-icon`, and with a heading an `.alert-heading` above an `.alert-description`; without one the text sits in a
plain `<div>`, as in Tabler's examples. The body snippets (`snippets/alert/text.html`, `snippets/alert/list.html`,
upstream's `<ul>`) and the `alert:*` colour keys are crud_views' own: Tabler spells `alert-danger`, `alert-warning`,
… like Bootstrap. `TABLER_ICONS` maps the `message-success` / `-info` / `-warning` / `-error` / `-debug` names. The
theme's former `tags/messages.html` and `snippets/delete/protection_errors.html` overrides are gone, and the
related-objects alerts, which used to render in plain Bootstrap style, now get the Tabler layout too.

## Not covered yet

- **Property-grid detail** (`crud_views_object_detail`): it has its own template packs and icon library settings
  (`bootstrap` / `fontawesome`); a Tabler datagrid layout would be the natural fit. The demo detail page uses a
  hand-written Tabler `.datagrid` instead.
- **Formsets** (`formsets/*.html`, formset.js; the theme registers `formset:control` = `btn btn-icon` and
  `formset:control-danger` = `btn btn-icon btn-danger`, untested because the demo has no formsets), **delete
  related-objects** snippets, the **manage** view, **language selector**, and the workflow / polymorphic / guardian
  extensions' templates.
- A Tabler-style cancel button.
- Responsive check below the `md` breakpoint.

## Questions for django-crud-views upstream

Discussed in detail, with the current code paths, pros and cons, in
[crud_views_upstream_questions.md](crud_views_upstream_questions.md):

1. Icons: Font Awesome class names on view classes, in two settings and hard-coded in templates. **Resolved in 0.30.0 (icon registry).**
2. Button classes set in Python (`CrispyDeleteForm` has no hook for its Delete button). **Resolved on main (#201, button class table).**
3. jQuery (used by four of the six core scripts, including modals and POST actions) and a global `bootstrap`. **Resolved on main (#200, jQuery-free core and cv.adapters).**
4. A way to mark a context action as the page's primary action. **Resolved on main (#201, variants).**
5. Theme overrides have to copy the package's template logic, and nothing detects when they go stale. **Resolved for buttons on main (#201 leaves, #204 tooltip markers): the theme overrides no button template.**

Where each point stands against upstream main today, and what is left to do (two open points; the four upstream
asks are filed as #208, #209, #210 and #211):
[crud_views_upstream_status.md](crud_views_upstream_status.md).
