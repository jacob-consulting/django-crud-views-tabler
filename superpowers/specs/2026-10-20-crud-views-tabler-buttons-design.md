# crud_views_tabler: follow django-crud-views main (button classes, leaves, tooltips)

Date: 2026-10-20
Status: design, discussed with the maintainer; builder check pending

## Intent

django-crud-views main has moved past the commit the theme was last aligned with (440ac55, #200, see
`2026-10-20-crud-views-tabler-upstream-main-design.md`). Two more merges landed on 2026-10-20:

- **#201 (e4bce00)**, "button variants, a class table and logic/markup leaves". Every button gets a semantic variant
  (`primary`, `secondary`, `tertiary`, `danger`; `CreateView` / `create_select` default to `primary`, `DeleteView` to
  `danger`). Every button class comes from one layered `location:slot` table (`crud_views.lib.button_classes`:
  package defaults, then `register_button_classes()` from a theme's `ready()`, then `CRUD_VIEWS_BUTTON_CLASSES`). The
  action templates are split into one-line logic templates (do not copy) and presentation leaves
  (`tags/button/action.html`, `menu_item.html`, `menu_item_label.html`, `container.html`) fed by a flat contract
  (`cv_button_data()`). `CrispyDeleteForm` gains `get_delete_button()` with slot `form:delete`. Upstream reference:
  `docs/reference/buttons.md`, `theme.md`, CHANGELOG "Unreleased".
- **#204 (4b62ed6)**, closing #202 (filed from this work, rationale in `docs/crud_views_tooltips.md`). Icon-only
  action buttons, the filter toggle, the card-order toggles and the formset controls carry
  `data-cv-tooltip="<location>"` next to their `title`, and `tooltip.js` calls `cv.adapters.tooltip.init(el,
  {location})`. Upstream reference: `docs/reference/javascript.md#tooltips`.

The sibling checkout `../django-crud-views` is on `main` @ 4b62ed6. The demo installs it as an
editable path dependency, so no install step is needed.

These two merges make most of the theme's action overrides unnecessary. The intent: **delete every override whose
only job was button classes, primary-action styling or the tooltip marker, and express the Tabler look as class-table
entries.** The maintainer decided explicitly: **where the stock upstream markup plus the class table looks slightly
different from today's theme, stock markup wins.** The theme should not keep a leaf override to preserve a detail of
the current look.

## Current state (theme @ ab8c456)

19 template overrides under `crud_views_tabler/templates/crud_views/` plus `crud_views_tabler/forms.py`
(`TablerDeleteForm`, used by `customers/views.py` `CustomerDeleteView.form_class`). On main @ 4b62ed6 the
overridden logic templates still render, because overrides from 0.30 keep working, but they bypass the variants, the
class table, `aria-current` on list/card buttons, card `cv-key`, `cv-card-container` and the new tooltip markers.

## Goals

- Remove these overrides (9 templates):
  - `tags/context_action.html`
  - `tags/list_action.html`
  - `tags/list_action.inner.html`
  - `tags/card_action.html`
  - `tags/context_actions.html`
  - `columns/actions.html`
  - `tags/actions_menu_toggle.html`
  - `tags/context_action_filter.html`
  - `snippets/card_order.html`
- Remove `crud_views_tabler/forms.py` (`TablerDeleteForm`, `DangerSubmit`). The demo's delete view uses upstream's
  `CrispyDeleteForm`.
- Register the Tabler button classes from `CrudViewsTablerConfig.ready()` with `register_button_classes()`, so
  projects need no button settings.
- Show toolbar tooltips below the toolbar again, through the tooltip adapter in `tabler-adapters.js` (upstream's
  documented per-location recipe), with no template.
- Keep `tags/card.html`, rewired so that its footer renders upstream's container leaf.
- Keep the theme's tests green against the new markup. Tests assert class-table registration, absence of the
  removed overrides and the tooltip markers.
- Update the docs:
  - `docs/crud_views_tabler.md`
  - `docs/crud_views_upstream_questions.md`: points 2, 4 and 5
  - `docs/crud_views_tooltips.md`: the "meanwhile" section becomes "resolved"

After this the theme has 10 template overrides, all of them about page layout rather than buttons:

- `tags/card.html`
- `view_card.content.html`
- `view_create.content.html`
- `view_update.content.html`
- `view_delete.content.html`
- `modal/shell.html`
- `snippets/pagination.html`
- `table/bootstrap5.html`
- `tags/list_filter.html`
- `tags/list_filter.inner.html`

## Non-goals

- Overriding any leaf (`tags/button/*.html`). The maintainer chose stock markup over the current look.
- Restyling the crispy form submit/cancel or filter submit/reset buttons. Bootstrap's `btn-primary` / `btn-secondary`
  render correctly in Tabler; only `form:delete` changes.
- Tabler templates for `crud_views_object_detail`, formsets, the manage view, the language selector or the
  extensions. Their classes keep the package defaults except where listed below; the demo uses none of them.
- Tooltips on disabled buttons (upstream documents the `pointer-events: none` limitation in
  `inaccessible_actions.md`).
- Switching to a PyPI release; the editable sibling checkout stays.

## Anti-goals

- A theme template that copies upstream branching: the `cv_disabled` / POST / modal decisions, or loops over
  `group.inline`.
- Any button class literal left in theme templates for buttons the class table covers.
- `data-cv-tooltip` or `data-bs-toggle="tooltip"` written by the theme. Upstream owns the marker.
- A theme registration of a key that is not in upstream's default table. `crud_views.W362` must not fire. The
  existing test runs the checks at `--fail-level WARNING`.

## Constraints

- Python 3.14, Django 6.1, uv. Tests: `uv run python manage.py test`. System checks pass at `--fail-level WARNING`.
- Tabler 1.6.1 from the CDN; `tabler.min.js` loads `defer` at the end of `templates/base.html`. The tooltip adapter
  must resolve `globalThis.tabler` at call time, not at load time.
- No inline scripts (CSP). The adapter change stays in the registered asset `tabler-adapters.js`.
- The ids and hooks the package's JavaScript reads stay as upstream renders them.

## Visible changes accepted by the maintainer

| Where | Today | After |
|---|---|---|
| Toolbar "Create" | `btn-primary` with icon and text label | icon-only `btn-primary` button; the label is visually hidden and shown as the tooltip |
| Labelled card buttons ("Open", "Edit") | icon plus label | label only (the stock leaf shows no icon when the label is visible) |
| Icon-only card buttons | square `btn-icon` | `btn-icon` is in the class table for the variant, so a labelled button of the same variant would get it too; see the card classes below |
| `⋯` menu toggles | no caret | stock adds `dropdown-toggle`, so a caret shows |
| Row and toolbar containers | `div.btn-list` | `fieldset.btn-list` (stock element; the classes come from the table) |
| Card-order bar | `form-label text-secondary` label, full-size select, `aria-pressed` | stock: plain label, `form-select-sm`, no `aria-pressed`; toggles keep `btn-icon` from the table |
| Delete form | confirmation checkbox full width | stock `Row(Column4("confirm"))` |
| Tooltips | Tabler tooltips (theme's `data-cv-tooltip`) | Tabler tooltips (upstream's markers); toolbar ones below the button as before |

## Design

### 1. Class table registration

In `CrudViewsTablerConfig.ready()`, next to the icon and asset registration:

```python
from crud_views.lib.button_classes import register_button_classes
from crud_views_tabler.buttons import TABLER_BUTTON_CLASSES

register_button_classes(TABLER_BUTTON_CLASSES)
```

New module `crud_views_tabler/buttons.py` holds the dict. That keeps `apps.py` short, mirrors `icons.TABLER_ICONS`,
and lets tests import it. Values:

| Key | Classes | Why |
|---|---|---|
| `context:primary` | `btn btn-primary btn-icon` | the page's primary action (create) stays blue |
| `context:secondary`, `context:tertiary` | `btn btn-icon` | today's toolbar icon buttons |
| `context:danger` | `btn btn-icon btn-outline-danger` | *my call*: delete on a detail toolbar, bordered like its neighbours |
| `list:primary` | `btn btn-sm btn-icon btn-ghost-primary` | *my call*; no demo row action is primary |
| `list:secondary`, `list:tertiary` | `btn btn-sm btn-icon btn-ghost-secondary` | today's row buttons |
| `list:danger` | `btn btn-sm btn-icon btn-ghost-danger` | today's row delete (was keyed on `cv_key == "delete"`, now on the variant) |
| `card:primary` | `btn btn-sm btn-primary` | today |
| `card:secondary` | `btn btn-sm` | today (Tabler's default button) |
| `card:tertiary` | `btn btn-sm btn-icon btn-ghost-secondary` | today's demo uses tertiary only for the icon-only delete; `btn-icon` here keeps it square (*my call*, see below) |
| `card:danger` | `btn btn-sm btn-ghost-danger` | *my call*: matches row delete |
| `context:container` | `btn-list` | today |
| `list:container` | `btn-list flex-nowrap justify-content-end gap-1` | today |
| `card:container` | `btn-list` | today |
| `context:menu-toggle` | `btn btn-icon` | today's classes; stock adds `dropdown-toggle cv-menu-toggle` |
| `list:menu-toggle` | `btn btn-sm btn-icon btn-ghost-secondary` | today |
| `card:menu-toggle` | `btn btn-sm btn-icon` | today |
| `context:menu-wrapper`, `list:menu-wrapper` | `dropdown` | *my call*: Tabler's dropdown wrapper; the stock `btn-group` would merge borders with nothing inside a `btn-list` |
| `form:delete` | `btn btn-danger` | replaces `TablerDeleteForm` |
| `card-order:toggle` | `btn btn-icon` | today |
| `card-order:container` | `btn-group` | today (stock is `btn-group btn-group-sm`) |
| `formset:control` | `btn btn-icon` | *my call*, untested in the demo (no formsets) |
| `formset:control-danger` | `btn btn-icon btn-danger` | *my call*, untested in the demo |

Keys not listed keep the package defaults:

- `card:menu-wrapper` (`dropdown`)
- `menu:item` (`dropdown-item`)
- `form:submit`, `form:cancel`, `form:filter-submit`, `form:filter-reset`
- `formset:container`
- `language:toggle`
- `object-detail:property-detail`

Projects still override any key through `CRUD_VIEWS_BUTTON_CLASSES` (project wins).

**`btn-icon` and variants.** The class table cannot tell an icon-only card button from a labelled one. In the demo
the only tertiary card action is the icon-only delete (`no_label=True, variant="tertiary"`), so `card:tertiary`
carries `btn-icon`. A project with a labelled tertiary card button would get a square-padded button and can override
the key. This is a known limitation of "stock markup wins"; record it in `docs/crud_views_tabler.md`.

### 2. Tooltip placement

`tabler-adapters.js` today is one statement. Add upstream's recipe from `docs/reference/javascript.md#tooltips`:

```javascript
Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler));
cv.adapters.tooltip.init = (el, {location} = {}) =>
    globalThis.tabler.Tooltip.getOrCreateInstance(el, {placement: location === "context" ? "bottom" : "top"});
```

Keep the existing comment block and add one line on why toolbar tooltips go below: they would otherwise cover the page
header. Guard against `globalThis.tabler?.Tooltip` being missing, the way upstream's default adapter does nothing
without `Tooltip`. The exact guard is the builder's choice.

### 3. `tags/card.html`

It stays because `customers/customer_card.html` extends it, and it carries the theme's card layout (`h3.card-title`,
`card-footer`) and the blocks `card_title`, `card_content`, `card_footer`. Only the inside of `card_footer` changes. The
two branches and the `btn-list` loop are replaced by upstream's pattern from its stock `tags/card.html`:

```django
{% block card_footer %}
<div class="card-footer">
  {% for ctx in group.menu %}{% cv_render_list_action_form ctx %}{% endfor %}
  {% include "crud_views/tags/button/container.html" with cv_buttons=group.inline cv_group=group cv_location="card" cv_container_tag="div" %}
</div>
{% endblock card_footer %}
```

`cv_get_card_action_group()` always returns an `ActionGroup` on main, so the `group is None` branch goes. The header
comment of the template is updated accordingly.

### 4. Delete form

Delete `crud_views_tabler/forms.py`. In `customers/views.py`, `CustomerDeleteView.form_class = CrispyDeleteForm`,
imported from `crud_views.lib.crispy`. Upstream's `DeleteView` sets no `form_class` of its own, so the line stays and
only the class changes.

### 5. Stylesheet

`crud_views_tabler.css` keeps its rules. Check two of them against the stock markup:

- `.card-table td:has(> [cv-list-container])` still matches: the stock container is a `fieldset` with
  `cv-list-container="true"` as the cell's direct child. Verify in the browser.
- `fieldset.btn-list`: upstream left it unverified that Tabler renders it like `div.btn-list`. Bootstrap's reboot
  resets the fieldset's `border`, `padding`, `margin` and `min-width`. Check in the browser that the toolbar and the
  row buttons lay out in a row with Tabler's gap, and in a table cell without wrapping. If not, add the smallest rule
  needed to the stylesheet, not a template.

The caret from `dropdown-toggle` on the `⋯` toggles is accepted. Do not hide it with CSS.

### 6. Tests (`crud_views_tabler/tests.py`)

Existing assertions that encode the old markup change:

- `btn-ghost-danger` on the row delete (now from `list:danger`)
- `btn btn-danger` on the delete form (now from `form:delete` through `CrispyDeleteForm`)
- `data-cv-tooltip` presence on toolbar, row and card buttons (now `data-cv-tooltip="context"` / `"list"` /
  `"card"`, written by upstream)
- the card variant classes (`btn btn-sm btn-primary flex-grow-1` was the theme's order; the stock leaf renders
  `{table classes} flex-grow-1`)
- the card-order toggle (`class="btn btn-icon active"`)

New or extended:

- Registration: `get_button_classes()` contains every `TABLER_BUTTON_CLASSES` entry, and every key is in upstream's
  default table, so a key upstream renames or removes fails a theme test rather than only a `W362` warning.
- `@override_settings(CRUD_VIEWS_BUTTON_CLASSES={...})` beats the theme: project wins. Upstream's `setting_changed` receiver
  resets the resolved cache, so `override_settings` needs no manual reset.
- The overrides listed under Goals are not shipped by the theme. Extend the existing
  `test_near_copies_of_upstream_templates_are_not_overridden` list.
- The toolbar "Create" renders as `btn btn-primary btn-icon`, with a `title` and a visually hidden label.
- The asset test also asserts that `tabler-adapters.js` sets `cv.adapters.tooltip.init`.

### 7. Docs

- `docs/crud_views_tabler.md`: the "Header and actions", "Card views", "Forms (crispy)", "JavaScript" and
  "Overridden templates" sections describe the class table, the variant mapping, the accepted visual differences
  (table above), the `btn-icon` limitation and the override list of 10.
- `docs/crud_views_upstream_questions.md`: give the Status blocks of points 2, 4 and 5 an update for main @ 4b62ed6
  (#201, #204). Point 2 is resolved (option A plus B, as the draft predicted). Point 4 is resolved (variants). Point 5
  is resolved for buttons: record the final count (19 → 10) and that the theme needs no leaf at all, which is fewer
  than the draft's "two leaf overrides" estimate. Keep the 440ac55 blocks as history and add the new blocks below
  them, in the style already used.
- `docs/crud_views_tooltips.md`: the "What the theme does meanwhile" section becomes "Resolved by #204". Note what
  upstream added beyond the issue (`init(el, {location})`, the object-detail trigger moving to `title`).

## Verification

- `uv run python manage.py test` passes. `uv run python manage.py check --fail-level WARNING` passes.
- Browser check (runserver, demo login), on the customers list, the card view, a detail page, the update form and
  the delete modal:
  - The toolbar is a row of icon buttons with a blue Create. Tooltips appear below on hover and on keyboard focus.
  - The filter toggle opens and closes, and its icon swaps.
  - Row buttons are ghost icons with a red delete, unwrapped at the end of the row, with tooltips above.
  - Card footers show the blue "Open" (flex), "Edit" and the square icon-only delete. The ordering bar works.
  - The delete modal shows a red Delete button, and its cancel and close work.
  - No console errors.
- Note in the result what was not checked:
  - tooltips inside a modal (`cv:modal:loaded` path): the demo's only modal, the delete confirmation, contains no
    tooltip trigger. *My call*: no demo code is added for it; upstream's vitest suite covers the path.
  - formset controls and disabled actions.
  - the unsigned card-order toggle, if the demo does not render it.

## Left to the builder

- The name and exact shape of `crud_views_tabler/buttons.py` (a module-level dict is expected).
- The guard style in the tooltip adapter.
- Whether a CSS rule is needed for `fieldset.btn-list` (only if the browser check shows a difference).
- Test names and grouping.
