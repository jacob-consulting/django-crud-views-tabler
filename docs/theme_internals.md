# Theme internals

How `crud_views_tabler` themes django-crud-views: what it overrides, which upstream hooks it uses, and where it stops.
It is exercised by the Acme Roasters demo (`example/`: apps `sales`, `catalog`, `roastery`, `shipping`), which puts
nested ViewSets, formsets, conditional groups, workflow, polymorphic models, object detail packs, Guardian, resources,
card views and the django-crud-views-extensions widgets through it, and by the `showcase` app (`/showcase/`), whose
create form renders every crispy template branch on one page (see [crispy_tabler.md](crispy_tabler.md)). Everything
the demo needed beyond upstream hooks is listed, with upstream references, in the
[findings log](https://github.com/jacob-consulting/django-crud-views-tabler/blob/main/dev/crud_views_upstream_findings_roastery.md).

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
    "django_tables2",
    "django_filters",
    "django_tabler",  # also provides the crispy_tabler template pack
    "crud_views_tabler",  # before crud_views
    "crud_views.apps.CrudViewsConfig",
]
CRISPY_TEMPLATE_PACK = "crispy_tabler"
CRISPY_ALLOWED_TEMPLATE_PACKS = ("crispy_tabler",)
CRUD_VIEWS_EXTENDS = "crud_views_tabler/page.html"  # the theme's page, see below
DJANGO_TABLES2_TEMPLATE = "crud_views/table/bootstrap5.html"  # the theme's table template
```

## The page: CRUD_VIEWS_EXTENDS

`crud_views_tabler/page.html` is part of the theme: it extends the Tabler layout from the `django_tabler` package
(`django_tabler/layouts/app.html`, top navbar) and maps the crud_views pieces onto Tabler's page header:

| crud_views | Tabler page |
|---|---|
| `cv_navbar.icon` + `cv_navbar.label`, `{% cv_navbar_items %}` (block `cv_navbar`) | top of `.page-header`, in the layout's `page_header_top` block: breadcrumb, owner avatar and `h1`, tabs; stock items template with Tabler `nav-bordered` through the `navbar:*` class keys (#384), no override |
| `{% cv_breadcrumb %}` | `.breadcrumb` above the title |
| `{% cv_header_icon %}` + `{% cv_header %}` | `.page-title` |
| `{% cv_paragraph %}` | `.page-subtitle` |
| `{% cv_context_actions object %}` | the page header's action area (`.btn-list`) |
| `cv_filter`, `cv_content` blocks | `.page-body` |
| `{% cv_css %}` / `{% cv_js %}` / `{% cv_config %}` | head / end of body / modal shell |

ViewSet Navigation (upstream PR #383; the "object navbar") is opt-in per view. With a bar, the page header
starts with the owner: the breadcrumb (moved up from the title row), an avatar with the owner ViewSet's header icon,
the owner's name as the page's `h1`, and the section links as Tabler underline tabs (`nav nav-bordered`, set
through upstream's `navbar:nav`/`navbar:item`/`navbar:link` class keys, #384). This follows upstream's owner-as-page-heading recipe
(#384). The view's own title row (title,
subtitle, buttons) follows the tabs as a section heading, so overrides of `page_title`, `cv_context` and `actions`
keep working; the browser title adds the owner's name. A view heading whose text equals the active tab's label is
left out (tag `cv_tabler_heading_repeats_tab` in the theme's `crud_views_tabler` library); the subline and buttons
stay, and a heading that says more ("Order #1073", "Edit order") stays. The `cv_navbar` block holds only the tabs and their
`.cv-tabler-navbar` wrapper: emptying it drops the tabs and keeps the owner row; the one tab rule (the active colour,
readable in dark mode) is scoped to that wrapper. `NavBar(template=...)` wrappers are not used (findings 36, 38). Without a bar the header is unchanged.

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
`.card-footer` with "Showing x–y of n" and a Tabler `.pagination` in a `<nav aria-label="pagination">`, with the
same accessibility markup as crud_views' table (Phase 05 parity: the current page a non-link `span` with
`aria-current`, the ellipsis and the missing neighbour `aria-disabled`, hidden labels from the
`pagination:hidden-label` class key). Card views use crud_views' own
`snippets/pagination.html` (#241: `aria-current`, `aria-disabled`, translated hidden labels), which is Tabler's own
pagination markup, so the theme no longer overrides it. Both paginations take their arrows from the semantic icon
names `page-previous` / `page-next`, which the theme maps to Tabler's chevrons at the standard icon size, as in
Tabler's examples (the old override used `icon-sm`). A project changes them with `CRUD_VIEWS_ICONS`.

## Workflow state badges, transition buttons and history

`crud_views_workflow` renders every state badge (`WorkflowModelMixin.state_badge`, the history table) with the class
key `workflow:badge-<colour>` (upstream #319). The theme registers each `BadgeEnum` value (`primary`, `secondary`,
`success`, `danger`, `warning`, `info`, `light`, `dark`) as Tabler's light status badge, `badge bg-<colour>-lt`, in
`buttons.TABLER_BUTTON_CLASSES`; a project overrides any of them with `CRUD_VIEWS_BUTTON_CLASSES`. The workflow page
puts its action form in the shared form frame (a card) and the history table in `workflow:history-wrapper`
(`table-responsive` upstream); the theme sets `workflow:history-table` to `table table-vcenter`, the list tables'
classes without `card-table`, because the history is not inside a card. With `cv_transition_presentation = "buttons"`
each transition's `custom["variant"]` picks the class key `workflow:transition-<variant>` (upstream #362; unknown or
missing variants keep `form:submit:label`) and its `custom["icon"]` is drawn before the label; the theme registers the
eight variants explicitly as `btn btn-<variant>`, the same values as upstream's defaults, so the Tabler choice is
visible in `TABLER_BUTTON_CLASSES`. The theme overrides no workflow template and
adds no workflow CSS. The `workflow:*` keys are registered only when `crud_views_workflow` is installed.

## Manage page

The structured manage page (upstream #366, with #370's Access check and #372's Resource pages) colours its badges
through `manage:*` class keys. The theme registers Tabler's light badges for them in `buttons.TABLER_BUTTON_CLASSES`,
using named colours rather than `primary`, because the page's legend names them ("Blue: required permission ·
Magenta: required group · Green: Guardian policy"): `bg-blue-lt` for permissions, `bg-pink-lt` for groups (instead of
upstream's fixed-colour `cv-manage-badge-group`), `bg-green-lt` for Guardian policies and allowed/passed trace
steps, `bg-red-lt` for denied, `bg-yellow-lt` for the other trace outcomes, `bg-secondary-lt` for the rest, and
`badge badge-outline text-secondary` for object grants; the help buttons are `btn btn-sm`. Upstream's `manage.css`
reads `--bs-secondary-color` and `--bs-secondary-text-emphasis`; `crud_views_tabler.css` sets both on
`[data-cv-manage]` from Tabler's `--tblr-*` values so the headers and dimmed default rows follow dark mode. The page
wraps its tables in `.table-responsive`, so the theme needs no overflow rule for it.

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
  `row-deck` grid does not need). The card title is a `{% cv_heading level=3 %}`, so it follows
  `CRUD_VIEWS_HEADER_LEVEL` like crud_views' own card,
- variants map to Tabler buttons through the class table: `primary` → `btn btn-sm btn-primary`, `secondary` → the
  default `btn btn-sm`, `tertiary` → `btn btn-sm btn-ghost-secondary`, `danger` → `btn btn-sm btn-ghost-danger`;
  `flex` → `flex-grow-1`. Labelled buttons show icon and label (crud_views' card default, label mode `both`),
- icon-only buttons (`CardAction(label_mode="icon")`, as the demo's delete) use the `card:<variant>:icon` keys, which
  add `btn-icon`; they keep a `.visually-hidden` label and get a tooltip,
- the order bar is crud_views' `snippets/card_order.html` with Tabler's sort-ascending / sort-descending icons and
  the `card-order:*` classes (`btn btn-icon` in a `btn-group`); signed ordering (`submit-on-change`) is unchanged,
- no results render Tabler's `.empty` state; pagination is crud_views' `snippets/pagination.html` (see Pagination).

**Custom card content** without repeating the actions markup: a view's `cv_card_template` extends
`crud_views/tags/card.html` and fills crud_views' blocks (`card_root`, `card_header`, `card_title`, `card_content`, `card_actions`; #243, #325). Under
this theme that resolves to the Tabler card, so the same template works with or without the theme. `card_root`
is the first child of the root `.card` (a `.card-status-top` stripe), `card_header` the first child of `.card-body`
above the heading (a badge row); both are empty by default. A card that adds its own footer fills `card_actions`
with that footer plus `{{ block.super }}` (the demo's product card does). Emptying `card_actions` drops the footer
along with the actions:

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

The demo renders forms through `django_tabler`'s template pack `crispy_tabler` (`CRISPY_TEMPLATE_PACK = "crispy_tabler"`;
see [crispy_tabler.md](crispy_tabler.md) for what it fixes). The theme app itself needs **no
crispy template overrides**: Tabler is Bootstrap 5, so `form-label`, `form-control`, `form-select`, `form-check`,
`is-invalid` and `invalid-feedback` render natively with either pack, including in dark mode. `crispy_bootstrap5`
is **not** in `INSTALLED_APPS` and nothing needs it: upstream removed `crud_views/detail/` — the last templates in
the package carrying hardcoded `bootstrap5/...` includes — in 10d81ad (#217), so the former precaution is gone (see
[crispy_tabler.md](crispy_tabler.md)). The `crispy-bootstrap5` *distribution* stays installed, as a
dependency of the `crispy` extra: `django_tabler.crispy.layout` subclasses its `FloatingField` and `Switch`. Remaining gaps and
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
  paths (six findings, now fixed in the `crispy_tabler` pack); plain Bootstrap 5 markup was enough only for the common inputs.

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

- `django_tabler/icons.py` holds Tabler outline icons as SVG paths (`ICONS`); `crud_views_tabler/icons.py` holds the registry renderer `render`
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
    { const init = cv.adapters.tooltip.init;
      cv.adapters.tooltip.init = (el, options = {}) => { /* data-bs-placement="bottom" for "context" */ init(el, options); }; }

The second statement places toolbar tooltips below the buttons, so they do not cover the page header. It **wraps**
crud_views' `init` instead of replacing it: since 06.8 that `init` guards Bootstrap 5.3 tooltip transitions that
outlive `dispose()`, and a theme calling `Tooltip.getOrCreateInstance` itself (crud_views' own recipe in
`docs/reference/javascript.md#tooltips` still shows that) would silently drop the guard. The placement travels as the
`data-bs-placement` attribute, which Bootstrap reads when it creates the tooltip; a button that already has one keeps
it. Only `init` is touched, so the adapter keeps crud_views' optional `hide(el)` and `dispose(el)` (#205),
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

## Heading levels

The page title, card titles and the filter heading render through crud_views' `{% cv_heading %}`, so
`CRUD_VIEWS_HEADER_LEVEL` (#251) applies under the theme too. While the setting is unset nothing changes: the page
title is an `h2.page-title` (Tabler's default), card and filter titles are `h3.card-title`. With it set, the page title
renders at that level and the card and filter titles one below, each keeping its look through the `heading:size-N`
class (`h2`, `h3`). `django_tabler/layouts/app.html` has a `page_heading` block around its `<h2>` for this, so
`django_tabler` itself still knows nothing about crud_views.

## Bulk actions

Bulk selection (django-crud-views #392) needs one override, one `bulk:*` key and no CSS:

- Six of the seven `bulk:*` button-class keys are not set: upstream's defaults (`form-check-input`, `d-flex` flex rows)
  are Bootstrap classes that Tabler styles. `bulk:card-cell` is `position-relative d-flex flex-fill`: upstream's
  `position-relative` block cell shrinks to its card's content inside Tabler's `.row-deck` column (a flex row), which
  gave cards of unequal width in the demo; `test_bulk_card_cell_fills_its_grid_column` pins it.
- The table view is upstream's: the toolbar renders above the table card and carries the select-all checkbox; the
  table's first column, "Select", holds one checkbox per row inside `.card.table-container > .table-responsive`, so a
  wide list scrolls in the card (the theme's table override already solves C9 of the AdminLTE tracker).
- The card view is the exception. The theme's `view_card.content.html` replaces upstream's grid and so would drop the
  toolbar and the card checkbox; it copies both from upstream's template (the toolbar include and the
  `bulk:card-cell` wrapper around `{% cv_card object %}`), inside its `.row-deck` grid. Upstream has no block for either.
  `test_card_bulk_markup_is_upstreams` compares the copied fragments with the installed upstream template, so a change
  upstream fails the suite.
- Every checkbox posts through `form="<toolbar form id>"`. The review page renders in the theme's page like any custom
  form view; result and warning messages go through the theme's alert template, once.

## Overridden templates

Eight templates, all about page layout; none of them renders a button (the card grid copies upstream's bulk markup,
see [Bulk actions](#bulk-actions)):

```
crud_views/
  modal/shell.html                Tabler modal shell (modal-blur, centered)
  snippets/form_frame.html        card around the form on create/update/delete/custom-form pages, bare in a modal
  table/bootstrap5.html           card table, sort headers, footer pagination
  tags/card.html                  actions in a .card-footer; crud_views' blocks and card:* class keys
  tags/alert.html                 every alert (messages, delete page) in Tabler's layout: .alert-icon, .alert-heading
  tags/list_filter.html, list_filter.inner.html   filter as a Tabler card
  view_card.content.html          card grid and empty state; bulk toolbar and card checkbox (upstream's,
                                  guarded by test_card_bulk_markup_is_upstreams)
static/crud_views_tabler/
  crud_views_tabler.css           required marker, row actions, filter card spacing, modal title, menu icons,
                                  toggle-group and formset legends, the typeahead --bs-* bridge
  tabler-adapters.js              cv.adapters -> window.tabler, toolbar tooltips below
```

The CSS rules added for the roastery demo each have a finding in
[crud_views_upstream_findings_roastery.md](https://github.com/jacob-consulting/django-crud-views-tabler/blob/main/dev/crud_views_upstream_findings_roastery.md): section labels for toggle
groups and formsets (#21: `conditional:legend` and `formset:legend` register `cv-tabler-section-legend`),
the typeahead skins reading Bootstrap's `--bs-*` properties (#31, plain CSS, the theme
does not import the extensions package). The workflow history's sideways-scroll rule (#5) went with upstream's
`.table-responsive` wrapper.

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

On crud_views pages, flash messages render with crud_views' `{% cv_messages %}` (#222) in `crud_views_tabler/page.html`.
Other pages get the same markup from the layout's default, `django_tabler/includes/messages.html`.

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

The roastery demo now renders object detail packs (`split-card`, `accordion`, `tabs-vertical`), formsets with their
control buttons, conditional toggle groups, the workflow badge/history/form, polymorphic create-select, Guardian
views, resources, card views, custom form and action views, and the typeahead and datetimepicker widgets; the sweep
before the demo's hand-over checked every page at 1280/1400 px and 390 px, light and dark, with no console errors.
Still not covered:

- The **language selector**. (The **manage** views are on since upstream #361, for alex only; theme CSS scrolls their
  content below 768 px, finding #25.)
- A Tabler-style cancel button.
- The datetimepicker's own look (finding #32).

## Questions for django-crud-views upstream

Discussed in detail, with the current code paths, pros and cons, in
[crud_views_upstream_questions.md](https://github.com/jacob-consulting/django-crud-views-tabler/blob/main/dev/crud_views_upstream_questions.md):

1. Icons: Font Awesome class names on view classes, in two settings and hard-coded in templates. **Resolved in 0.30.0 (icon registry).**
2. Button classes set in Python (`CrispyDeleteForm` has no hook for its Delete button). **Resolved on main (#201, button class table).**
3. jQuery (used by four of the six core scripts, including modals and POST actions) and a global `bootstrap`. **Resolved on main (#200, jQuery-free core and cv.adapters).**
4. A way to mark a context action as the page's primary action. **Resolved on main (#201, variants).**
5. Theme overrides have to copy the package's template logic, and nothing detects when they go stale. **Resolved for buttons on main (#201 leaves, #204 tooltip markers): the theme overrides no button template.**

Where each point stands against upstream main today, and what is left to do (two open points; the four upstream
asks are filed as #208, #209, #210 and #211):
[crud_views_upstream_status.md](https://github.com/jacob-consulting/django-crud-views-tabler/blob/main/dev/crud_views_upstream_status.md).
