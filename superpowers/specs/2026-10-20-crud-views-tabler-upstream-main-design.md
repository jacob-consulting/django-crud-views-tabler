# crud_views_tabler: follow django-crud-views main (icon registry, JS adapters)

Date: 2026-10-20
Status: design, discussed with the maintainer; builder check pending

## Intent

django-crud-views main carries two changes that remove the two biggest workarounds in the Tabler theme prototype
(`crud_views_tabler`, described in `docs/crud_views_tabler.md`):

- **0.30.0** (released on PyPI): a semantic icon registry. The package refers to icons by name (`detail`, `delete`,
  `filter`, ...), values are `prefix:name`, a library per prefix owns a renderer, everything renders through
  `{% cv_icon %}`, and a theme registers its library and default icons from `AppConfig.ready()`. Upstream reference:
  `docs/reference/icons.md`, module `crud_views.lib.icons`.
- **main @ 440ac55** (#200, unreleased): a jQuery-free core and `cv.adapters` (`modal`, `tooltip`, `collapse`) with
  `cv.bootstrapAdapters(ns)` for Bootstrap under another global. Also new: `crud_views/modal/shell.html`,
  `data-cv-modal-dismiss`, semantic `cv_modal_size` tokens (`""`, `sm`, `lg`, `xl`, check `viewset.E250`), and a
  filter toggle contract (`aria-expanded`, `aria-controls="filter-collapse"`, two `data-cv-filter-icon` spans).
  Upstream reference: `docs/reference/javascript.md`, `modals.md`, `theme.md`, `assets.md`.

Today the theme maps Font Awesome class strings to inline Tabler SVG at render time (`icons.py`, `{% cvt_icon %}`)
and loads jQuery 3.7.1 plus `bootstrap-shim.js`, which aliases `window.bootstrap = window.tabler` and registers
Bootstrap's jQuery plugins after the fact. Both exist only because the package hard-coded Font Awesome and jQuery.

This design moves the theme onto the upstream mechanisms, deletes what they make redundant, and updates the two
documents that describe the theme and the questions it raised upstream. The upstream checkout is the sibling
directory `/home/alex/projects/alex/django-crud-views` (branch `main`); the maintainer of both repos is the same
person.

## What is broken against main today

Checked by diffing upstream `v0.29.4..main` against the theme's 23 overrides (`git diff v0.29.4..main -- src/crud_views/templates src/crud_views/static` in the upstream checkout):

| Theme file | Problem on main |
|---|---|
| `tags/list_filter.inner.html` | calls `{% cv_filter_icon %}`, removed in 0.30.0: `TemplateSyntaxError` on every list page with a filter |
| `tags/icon.html` | upstream deleted the template; `{% cv_header_icon %}` now calls `render_icon()` directly, so this override is dead and the header icon renders as Font Awesome `<i>` (invisible: the demo loads no Font Awesome) |
| `customers/views.py` `icon_header="building-store"` | a bare value is a raw CSS class on 0.30.0: `<i class="building-store">`, invisible |
| `tags/context_action_filter.html` | lacks `aria-expanded`, `aria-controls`, the two icon spans; `list.filter.js` falls back to reading the panel's visibility and the icon never swaps |
| `modal/content.html` | `data-bs-dismiss="modal"`; works only because Tabler's data API handles it, not through `cv.adapters.modal.hide` |
| `shared/js.html`, `bootstrap-shim.js` | load jQuery and alias `bootstrap`; core needs neither. The default adapters still look for `globalThis.bootstrap`, so without the alias the Tabler page would throw on modal open and filter toggle |
| every `{% cvt_icon cv_icon_action %}` | `cv_icon_action`, `cv_icon_header`, `cv_menu_icon` now carry icon values (`far:eye`), not classes; the Font Awesome table no longer matches anything and the fallback renders `<i class="far:eye">` |

## Goals

- The demo project installs django-crud-views from the sibling checkout as an editable path dependency.
- The theme registers a `tabler` icon library (inline SVG renderer) and a Tabler icon for **every** semantic name
  in upstream `DEFAULT_ICONS` (27 names), from `AppConfig.ready()`. No Font Awesome mapping, no theme-own tag.
- The theme loads no jQuery and no shim. A one-statement `tabler-adapters.js`, registered as a theme asset, points
  `cv.adapters` at `window.tabler`.
- The theme follows the new modal and filter toggle contracts and ships a Tabler modal shell.
- Theme buttons use `data-cv-tooltip`, so core initialises their tooltips, including inside modal content.
- Tests cover the registration, the asset order, the contracts, and fail when upstream adds a semantic icon name
  the theme does not map.
- `docs/crud_views_tabler.md` and `docs/crud_views_upstream_questions.md` describe the new state.

## Non-goals

- Adopting the upstream draft spec `superpowers/specs/2026-10-19-button-variants-and-leaves-design.md` (variants,
  button class table, leaf templates). It is not implemented on main. `TablerDeleteForm`, the key-based
  primary/danger styling and the six logic-copying overrides stay as they are.
- Tabler templates for `crud_views_object_detail`, formsets, the manage view, the language selector or the
  extensions. Their icons become Tabler through the registry; their markup is untouched.
- Loading jQuery for anyone. A project with formsets loads jQuery in its own base template, as upstream documents.
- A Tabler Icons webfont or sprite. Icons stay inline SVG.
- Pinning a release. Switching back to a PyPI version happens when the next release ships; the docs say so.

## Anti-goals

- Any Font Awesome class string left in theme code, templates or tests.
- Any `jquery` reference left in the theme app.
- A theme template that renders an icon value with `<i class="{{ … }}">` instead of `{% cv_icon %}`.
- A silently unmapped semantic name: a new upstream name must fail a theme test.

## Constraints

- Python 3.14, Django 6.1, uv. Tests run with `uv run python manage.py test`; the system checks must pass at
  `--fail-level WARNING` (an existing test asserts this).
- Tabler 1.6.1 from the CDN, `tabler.min.js` loaded `defer` at the end of `templates/base.html`; the theme must not
  require changes to the script order in the project's base template.
- Strict-CSP friendly: no inline scripts; `nonce` support in the stock `shared/js.html` is used as is.
- The three modal ids `cv-modal`, `cv-modal-dialog`, `cv-modal-content`, the ids `cv-filter-toggle` and
  `filter-collapse`, and every `cv-key` / `data-cv-*` hook the package's JavaScript reads stay unchanged.
- The `dashboard` app's `{% icon %}` tag (`dashboard/templatetags/tabler.py`) imports the theme's SVG function. It
  keeps working with a plain `name -> SVG` function; it does not go through the registry.

## Design

### 1. Dependency: editable path to the sibling checkout

`pyproject.toml`:

```toml
dependencies = [
    "django>=6.1,<6.2",
    "django-crud-views>=0.30.0",
]

[tool.uv.sources]
django-crud-views = { path = "../django-crud-views", editable = true }
```

`uv lock && uv sync` regenerates `uv.lock` and replaces the PyPI 0.29.4 in `.venv` with the editable install
(upstream builds with hatchling; `src/` layout). Verify with `uv run python -c "import crud_views, pathlib; print(crud_views.__file__)"` pointing into the checkout, and that `manage.py check` passes. README gets one line: the demo tracks
upstream main through the sibling checkout; a released version replaces the source entry later.

### 2. Icons

**Module `crud_views_tabler/icons.py`** keeps `ICONS` (Tabler name -> list of `<path d>` strings) and loses
`FONT_AWESOME`, `FONT_AWESOME_EXACT` and `resolve()`. It exposes:

- a plain function `svg(name, css="") -> SafeString`: the inline SVG for a Tabler name in `ICONS`, `""` for an
  unknown name (the `dashboard` tag calls this; today's `render_icon(value, css_class)` becomes it, name is the
  builder's choice);
- the registry renderer `render(name, *, css, config) -> SafeString`, the upstream renderer contract, delegating to
  `svg(name, css)` and ignoring `config`;
- `TABLER_ICONS: dict[str, str]`, every upstream `DEFAULT_ICONS` key -> `"tabler:<name>"`.

The SVG markup stays exactly as today: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false" class="icon {css}">` followed by one `<path d="…"/>` per entry. `class` is
`"icon"` plus the extra classes, trimmed.

**Mapping** (`TABLER_ICONS`), Tabler outline set. Names marked new need a path added to `ICONS`:

| Semantic name | Tabler icon | | Semantic name | Tabler icon |
|---|---|---|---|---|
| `list` | `list` | | `sort-asc` | `sort-ascending` |
| `card` | `layout-grid` | | `sort-desc` | `sort-descending` |
| `detail` | `eye` | | `table-sort-asc` | `chevrons-up` (new) |
| `create` | `square-plus` | | `table-sort-desc` | `chevrons-down` (new) |
| `update` | `pencil` | | `formset-up` | `caret-up` (new) |
| `delete` | `trash` | | `formset-down` | `caret-down` (new) |
| `order-up` | `arrow-up` | | `formset-add` | `plus` |
| `order-down` | `arrow-down` | | `formset-delete` | `square-x` (new) |
| `manage` | `settings` | | `field-marker` | `chevrons-right` (new) |
| `workflow` | `hierarchy` (new) | | `boolean-true` | `circle-check` (new) |
| `actions-menu` | `dots` | | `boolean-false` | `circle-x` (new) |
| `filter` | `filter` | | `property-detail` | `info-circle` |
| `filter-close` | `filter-x` (new) | | `text-icon` | `file-text` (new) |
| `language` | `language` (new) | | | |

Path source: the local package `/home/alex/projects/alex/tabler/tabler-icons-3.41.0/svg/` (outline variants) or
`https://cdn.jsdelivr.net/npm/@tabler/icons@3.34.0/icons/outline/<name>.svg` (all twelve names verified to exist
there). Copy only the `<path d="…">` values; drop the invisible `M0 0h24v24H0z` background path if present, as the
existing entries do.

**Registration** in `crud_views_tabler/apps.py` `ready()`:

```python
from crud_views.lib.assets import register_assets
from crud_views.lib.icons import register_icon_library, register_icons

register_icon_library("tabler", renderer="crud_views_tabler.icons.render")
register_icons(TABLER_ICONS)
register_assets("crud_views_tabler", js=["crud_views_tabler/tabler-adapters.js"], css=["crud_views_tabler/crud_views_tabler.css"])
```

Precedence is upstream's: package defaults, then theme registrations, then `CRUD_VIEWS_ICONS` from the project. A
project can still say `CRUD_VIEWS_ICONS = {"detail": "tabler:zoom"}` or `"far:eye"`.

**System check** `crud_views_tabler.W001` (my call): for every value in `crud_views.lib.icons.get_icons()` that
starts with `tabler:` and whose name is not in `ICONS`, warn with the key, the value, and the hint to add the path to
`ICONS` or use another library. Registered from `ready()` with `django.core.checks.register`. It covers the table
only, not `cv_icon_action` / `icon_header` attributes on views (upstream's `W353` covers those for unregistered
prefixes only). Unknown names render nothing at request time, as upstream does.

**Templates**: every `{% cvt_icon … %}` becomes `{% load crud_views %}` + `{% cv_icon … %}`. Semantic names where
one exists, `tabler:<name>` for theme-only icons. The tag's extra classes go in `css=`:

| Template | Change |
|---|---|
| `tags/context_action.html`, `tags/list_action.inner.html`, `tags/card_action.html`, `tags/actions_menu_toggle.html` | `{% cv_icon cv_icon_action %}` / `{% cv_icon cv_menu_icon %}` (`css="icon-sm"` where the theme passes it today) |
| `tags/actions_menu_item_label.html` | `{% cv_icon cv_icon_action css="dropdown-item-icon" %}` (Tabler's class instead of upstream's `cv-icon-fw`) |
| `tags/list_filter.inner.html` | `{% cv_icon "filter" %}` instead of `{% cv_filter_icon %}` |
| `snippets/card_order.html` | `{% cv_icon "sort-asc" %}`, `{% cv_icon "sort-desc" %}` |
| `snippets/pagination.html`, `table/bootstrap5.html` | `{% cv_icon "tabler:chevron-left" css="icon-sm" %}` / `chevron-right` |
| `view_card.content.html` | `{% cv_icon "tabler:mood-empty" %}` |
| `view_delete.content.html` | `{% cv_icon "tabler:alert-circle" css="alert-icon" %}` |
| `tags/icon.html` | delete (dead) |
| `templatetags/crud_views_tabler.py`, `templatetags/__init__.py` | delete (the `cvt_icon` tag has no caller left) |

`{% cv_header_icon %}` in `templates/crud_views_page.html` and `modal/content.html` stays; it renders through the
registry. `customers/views.py`: `icon_header="tabler:building-store"`.

**Dashboard**: `dashboard/templatetags/tabler.py` imports the plain SVG function under its new name; its icons
(`home`, `users`, `moon`, `sun`, `dashboard`, `search`, `trending-up`, `trending-down`, `check`, `corner-left-up`,
`user`, `building-store`, …) stay in `ICONS`.

### 3. JavaScript

**Delete** `templates/crud_views/shared/js.html` and `static/crud_views_tabler/bootstrap-shim.js`. The stock
`shared/js.html` renders the core scripts synchronously (`type="application/javascript"`, nonce when configured) in
the order `adapters.js`, `viewset.js`, `formset.js`, `list.filter.js`, `modal.js`, `toggle.js`, `tooltip.js`, then
registered bundles in `INSTALLED_APPS` order.

**Add** `static/crud_views_tabler/tabler-adapters.js`:

```javascript
// Tabler's bundle exposes Bootstrap's components on window.tabler, not window.bootstrap.
// The namespace is resolved on every adapter call, so tabler.min.js may load deferred.
Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler));
```

Registered through `register_assets` (section 2), so it renders after core and `cv.adapters` exists when it runs.

**Why no `defer` is needed any more**: `{% cv_js %}` sits in the page's `extra_js` block after the deferred
`tabler.min.js` tag. Core scripts need nothing at load (they attach document-level listeners). Adapters resolve
`globalThis.tabler` per call. `tooltip.js` initialises on `DOMContentLoaded`, which fires after deferred scripts
have executed, so `tabler.Tooltip` exists by then. `formset.js` logs one `console.error` naming jQuery on pages
with formsets only; the demo has none.

**Modal**:

- `modal/content.html` (kept for the flex title that aligns the SVG): close button carries `data-cv-modal-dismiss`
  instead of `data-bs-dismiss="modal"`.
- New override `modal/shell.html` with Tabler's look; ids unchanged:

  ```html
  <div class="modal modal-blur fade" id="cv-modal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered" id="cv-modal-dialog">
      <div class="modal-content" id="cv-modal-content"></div>
    </div>
  </div>
  ```

  The Bootstrap adapter's `setSize` only swaps `modal-sm/lg/xl`, so `modal-dialog-centered` survives.
- The demo sets `cv_modal = True` and no size; nothing to migrate. The design doc mentions the tokens.

**Filter toggle** `tags/context_action_filter.html`, Tabler icon button with the upstream contract:

```html
{% load crud_views %}
<button type="button" class="btn btn-icon" id="cv-filter-toggle"
        aria-expanded="{% if cv_filter_expanded %}true{% else %}false{% endif %}" aria-controls="filter-collapse"
        title="{{ cv_action_label }}" data-cv-tooltip data-bs-placement="bottom" cv-key="{{ cv_key }}">
  <span data-cv-filter-icon="open"{% if cv_filter_expanded %} class="d-none"{% endif %}>{% cv_icon "filter" %}</span>
  <span data-cv-filter-icon="close"{% if not cv_filter_expanded %} class="d-none"{% endif %}>{% cv_icon "filter-close" %}</span>
  <span class="visually-hidden">{{ cv_action_label }}</span>
</button>
```

**Tooltips**: in `tags/context_action.html`, `tags/list_action.inner.html`, `tags/card_action.html` and the filter
toggle, `data-bs-toggle="tooltip"` becomes `data-cv-tooltip`; `title` and `data-bs-placement` stay. Reason: Tabler
1.6.1 auto-initialises `[data-bs-toggle="tooltip"]` once at page load (verified in `tabler.min.js`), while core's
`tooltip.js` initialises `[data-cv-tooltip]` through the adapter at load, on `cv:modal:loaded` and on
`cv:formset:row-added`. Buttons inside modal content therefore get tooltips too. The project's own templates
(navbar, login) keep `data-bs-toggle="tooltip"`; both mechanisms use `getOrCreateInstance`, so no double init.

### 4. Override inventory after the change

```
crud_views/
  columns/actions.html                        unchanged
  modal/content.html                          data-cv-modal-dismiss
  modal/shell.html                            NEW: modal-blur, centered dialog
  snippets/card_order.html                    cv_icon sort-asc / sort-desc
  snippets/pagination.html                    cv_icon tabler:chevron-*
  table/bootstrap5.html                       cv_icon tabler:chevron-* (footer pagination)
  tags/actions_menu_item_label.html           cv_icon css="dropdown-item-icon"
  tags/actions_menu_toggle.html               cv_icon cv_menu_icon
  tags/breadcrumb.html                        unchanged
  tags/card.html                              unchanged
  tags/card_action.html                       cv_icon, data-cv-tooltip
  tags/context_action.html                    cv_icon, data-cv-tooltip
  tags/context_action_filter.html             rewritten (contract above)
  tags/context_actions.html                   unchanged
  tags/list_action.html                       unchanged
  tags/list_action.inner.html                 cv_icon, data-cv-tooltip
  tags/list_filter.html                       unchanged
  tags/list_filter.inner.html                 cv_icon "filter"
  view_card.content.html                      cv_icon tabler:mood-empty
  view_create.content.html                    unchanged
  view_delete.content.html                    cv_icon tabler:alert-circle
  view_update.content.html                    unchanged
  (deleted) shared/js.html, tags/icon.html
static/crud_views_tabler/
  crud_views_tabler.css                       unchanged
  tabler-adapters.js                          NEW
  (deleted) bootstrap-shim.js
```

### 5. Tests (`crud_views_tabler/tests.py`)

Replace `IconTests` and `test_scripts_load_jquery_and_shim_deferred`; keep the rest, adjusting assertions.

- SVG function: known name renders `class="icon icon-sm"` and `<path`; unknown name renders `""`; `None` renders `""`.
- Registry: `crud_views.lib.icons.render_icon("detail")` returns the theme SVG (registration from `ready()` works);
  `render_icon("tabler:building-store")` works; with `override_settings(CRUD_VIEWS_ICONS={"detail": "far:eye"})`
  the project wins and renders `<i class="fa-regular fa-eye"`.
- Completeness: `set(TABLER_ICONS) == set(crud_views.lib.icons.DEFAULT_ICONS)` and every `TABLER_ICONS` value's
  name is in `ICONS`. This is the guard against a new upstream name.
- Check: `call_command("check", "--fail-level", "WARNING")` passes (exists); with
  `override_settings(CRUD_VIEWS_ICONS={"detail": "tabler:does-not-exist"})` the check run reports
  `crud_views_tabler.W001`.
- Scripts: the list page HTML contains no `jquery`; `crud_views/js/adapters.js` appears before
  `crud_views_tabler/tabler-adapters.js`; `crud_views/js/modal.js` is present. Drop the
  `type="application/javascript"` assertion.
- Filter toggle: the list page has `id="cv-filter-toggle"` with `aria-controls="filter-collapse"`,
  `aria-expanded="false"`, both `data-cv-filter-icon` spans, the close span hidden. After posting
  `{"filter_expanded": true}` as JSON to the list URL (what `list.filter.js` does; upstream `tests/test1/test_filter.py`
  shows the request shape) a GET renders `aria-expanded="true"` and the open span hidden.
- Modal: the delete partial (`X-CV-Modal: true`) contains `data-cv-modal-dismiss` and no `data-bs-dismiss`; the
  list page contains `id="cv-modal"` with `modal-blur` and `id="cv-modal-dialog"` with `modal-dialog-centered`.
- Tooltips: the list page contains `data-cv-tooltip` and no `data-bs-toggle="tooltip"` inside the
  `cv-list-container` / `cv-context-container` markup (the navbar outside still has it, so scope the assertion).
- Icons in output: keep `assertNotIn("fa-regular")` / `assertNotIn("fa-solid")`, add `assertNotIn("<i class=")` for
  the list and card pages (the demo has no raw-class icons anywhere).
- Card order bar: `sort-asc` renders as SVG (`<svg` directly inside the `value="asc"` button).

### 6. Documentation

**`docs/crud_views_upstream_questions.md`** keeps every point's analysis and gains, directly under each point's
heading, a block `### Status (upstream main @ 440ac55)` with "What upstream did", "How it maps to the options above"
and "What the theme does now":

- *Point 1 (icons)*: 0.30.0 implemented option C in substance: semantic names, one render point (`{% cv_icon %}`),
  libraries with pluggable renderers (`prefix:name`), theme registration from `ready()`, object detail folded in,
  system checks `E350`–`E356`, `W352`, `W353`, `viewset.W246`; the compatibility rule is the one option C
  predicted (a colon-less unknown value is a raw CSS class). Theme now: `tabler` library, 27 names, Font Awesome
  table and `tags/icon.html` gone; formset, object-detail and language icons are Tabler too without any override.
- *Point 3 (jQuery, global `bootstrap`)*: main (#200) implemented option B (viewset, modal, list.filter and tooltip
  scripts on the DOM API and `fetch`) and generalised "a configured global" into `cv.adapters` with
  `cv.bootstrapAdapters(ns)`, `ns` being a function resolved per call, which also removes the load-order trap.
  `formset.js` stays on jQuery (option C deferred) and fails soft with one `console.error`. Theme now: no jQuery,
  no shim, one-line adapter asset; plus the modal shell, `data-cv-modal-dismiss`, `cv_modal_size` tokens, and the
  filter toggle contract.
- *Points 2, 4, 5*: a draft design on upstream main, `superpowers/specs/2026-10-19-button-variants-and-leaves-design.md`,
  covers all three (variants with view defaults, a layered button class table with theme registration, leaf
  templates); nothing is implemented as of 440ac55; its "Tabler check" section lists what this theme would drop.
- *Point 5 additionally*: a paragraph "Observed while following main": the removed `{% cv_filter_icon %}` would
  have raised on every filtered list page, `tags/icon.html` went silently dead, and `data-bs-dismiss` kept working
  only through Tabler's data API. One loud failure, two silent ones, found only by diffing upstream.
- The section "How this was checked, and what was not": add that the status blocks were checked against the
  upstream checkout at `main` 440ac55 (the diff above), while the original file/line references remain 0.29.4.

**`docs/crud_views_tabler.md`**: "Built against" line names django-crud-views main @ 440ac55 (editable path
dependency); the Icons section describes the `tabler` library, the registration, `{% cv_icon %}`, project overrides
via `CRUD_VIEWS_ICONS` and the W001 check; the JavaScript section describes `tabler-adapters.js`, that no jQuery is
loaded, formsets need the project to load it, and the modal shell; the filter paragraph mentions the icon swap; the
overridden-templates list matches section 4; "Not covered yet" drops "Filter button state"; the "Questions for
upstream" list gets the status in one phrase each.

**`README.md`**: the `crud_views_tabler/` line says "template overrides, Tabler icon library, JS adapter"; one
sentence on the editable path dependency.

## Verification

1. `uv lock && uv sync`; `uv run python manage.py check --fail-level WARNING`; `uv run python manage.py test`.
2. Browser pass (Chrome, `runserver`, logged in as a superuser, demo customers seeded):
   - `/customer/`: Tabler SVG icons everywhere, tooltips on hover, no console errors, no request to code.jquery.com;
   - filter toggle: opens and closes the panel, icon swaps between `filter` and `filter-x`, state survives a reload;
   - sort a column, page through the table;
   - `/customer/card/`: order bar icons, pagination;
   - delete from the list: modal opens through the Tabler adapter (blurred backdrop, centered), the close button
     dismisses it, submitting deletes and redirects with the message;
   - `?theme=dark`: icons follow `currentColor`.
3. Confirm the deleted files are gone from the tree and nothing references `cvt_icon`, `bootstrap-shim`,
   `FONT_AWESOME` or `jquery` under `crud_views_tabler/`, `templates/`, `customers/`, `dashboard/`.

## Left to the builder

- Function names in `icons.py`; whether the check lives in `icons.py`, `apps.py` or a `checks.py`.
- The twelve new SVG paths and their source (local package or CDN).
- The check's tag (`Tags.templates` or none) and the exact message wording.
- Test organisation (one class per concern or extending the existing three).
- Commit granularity. Suggested: dependency; icons; JavaScript and contracts; docs.

## Calls I made (not discussed, say if wrong)

- Inline SVG stays the icon mechanism; no Tabler webfont, no sprite.
- The Tabler icon chosen per semantic name in the mapping table (in particular `hierarchy` for `workflow`,
  `filter-x` for `filter-close`, `arrow-up`/`arrow-down` for the ordered views as today).
- The `crud_views_tabler.W001` check.
- `data-cv-tooltip` on theme buttons.
- `modal/shell.html` with `modal-blur` and `modal-dialog-centered`.
- The questions document gains status blocks instead of being rewritten, and point 5 gets the "observed" paragraph.
- `TablerDeleteForm`, the `dashboard` icon tag and the demo `customers` views are otherwise untouched.
