# Why the tooltip marker belongs in django-crud-views

2026-10-20. Upstream issue: [jacob-consulting/django-crud-views#202](https://github.com/jacob-consulting/django-crud-views/issues/202),
closed by #204 (4b62ed6). The analysis below is as written before the fix; the last section records what landed.

Checked against django-crud-views main @ e4bce00 (0.30.0 plus #200 and #201) and `crud_views_tabler` @ ab8c456.

## The short version

The Tabler theme wants styled tooltips on icon-only buttons. All the parts already exist except one attribute.

- The theme already wires the tooltip adapter: `tabler-adapters.js` sets `cv.adapters.tooltip` to call Tabler's
  `Tooltip`.
- The package already runs the adapter: `tooltip.js` calls it on page load, after a modal loads and after a formset
  row is added.
- The missing piece is the marker. `tooltip.js` only looks at elements marked `data-cv-tooltip`, and since #201 the
  stock button templates never render that marker.

Adding the marker to the stock templates fixes it for every theme with no theme code at all. Every way of fixing it
in the theme copies something upstream owns.

## What happens today

| Step | Where | Status |
|---|---|---|
| Icon-only button renders `title="…"` | `tags/button/action.html` (`cv_title` is set exactly when the label is not visible) | works |
| Button is marked as a tooltip trigger | same template | **missing**: no `data-cv-tooltip` |
| `tooltip.js` finds triggers and calls `cv.adapters.tooltip.init(el)` | `static/crud_views/js/tooltip.js`, selector `[data-cv-tooltip]` | works, finds nothing |
| Adapter creates a Tabler tooltip | `crud_views_tabler/static/crud_views_tabler/tabler-adapters.js` | works, never called |

Result: toolbar, list-row and icon-only card buttons show only the browser's native `title` box, which appears late
and looks different from the rest of the UI. The filter toggle, the card-order toggles and the formset row controls
have the same gap.

Before #201 the theme did not notice, because it overrode `context_action.html`, `list_action.html` and
`card_action.html` and added `data-cv-tooltip` there. #201 makes those overrides unnecessary. Classes now come from
`register_button_classes()`, and the logic templates say "do not copy them; override a leaf instead". The marker is the
one thing that still pulls the theme back to overriding a template.

## Options

**A. The theme overrides the leaf `tags/button/action.html`** and adds `data-cv-tooltip`.
- Pro: no upstream change.
- Con: the theme owns a copy of the leaf contract: the element choice, `disabled` / `data-cv-disabled`,
  `data-cv-action`, the modal attributes, `aria-current`, `cv-key`, the label branches. Upstream documents every one
  of these as "keep it when you override". Each future change to the leaf has to be copied by hand. That is exactly
  the drift #201 was built to remove, and it costs a whole template for one attribute. The filter toggle,
  card-order and formset templates would need overrides too.

**B. The theme's JavaScript also initialises `[cv-key][title]` buttons.**
- Pro: no upstream change, no template override.
- Con: it duplicates `tooltip.js`: the same three triggers (page load, `cv:modal:loaded`, `cv:formset:row-added`)
  under a different selector. If upstream adds a trigger, the theme silently misses it. It also relies on `cv-key`
  plus `title` meaning "tooltip", which nothing promises. It does not cover the card-order buttons or the formset controls (no `cv-key`)
  without more selectors.

**C. The stock templates carry `data-cv-tooltip` wherever they render a `title` for an icon-only control** (the
issue).
- Pro: one attribute in a handful of templates. Every theme gets rich tooltips by wiring the adapter, which a theme
  does anyway for modals and collapse. Nothing in the theme copies upstream logic. It matches what the package
  already does for object detail (#125, `card-rows/property.html`). The marker is inert without an adapter, so a
  project without tooltip JavaScript keeps the native `title`.
- Con: stock Bootstrap 5 projects that load `bootstrap.bundle` start showing Bootstrap tooltips instead of native
  ones. That is a visible change and needs a CHANGELOG entry. A project that prefers native tooltips sets
  `cv.adapters.tooltip = {init() {}}`.

## Why C

- **It finishes #201's own goal.** #201 says a theme "only needs a template when the markup itself differs". A
  tooltip is not different markup. It is the same button with a behaviour the package already supports. Requiring a
  leaf override for it contradicts that rule.
- **The contract already has the right signal.** `cv_title` is set exactly when the label is hidden, which is exactly
  when a tooltip is useful. The template change is one condition the leaf already evaluates.
- **The adapter mechanism from #200 then works for tooltips as it does for modal and collapse.** Tooltip is the only
  one of the three adapters that stock markup cannot reach today.
- **It helps every theme, not only Tabler.** Any theme with a tooltip library (Tippy, Floating UI, a CSS framework's
  own) plugs into `cv.adapters.tooltip` and is done.
- **It fixes a small accessibility and i18n wart on the way.** The formset controls have `title="up"`, `"down"`,
  `"add"`, `"delete"`: untranslated and lowercase, while their `aria-label` is translated. Marking them as tooltip
  triggers puts that text in front of users, so it gets fixed.

## What it does not solve

- **Disabled buttons.** Bootstrap sets `pointer-events: none` on `.btn:disabled`, so no tooltip, rich or native,
  shows on a disabled action (`CRUD_VIEWS_INACCESSIBLE_ACTIONS = "disable"`). Bootstrap's workaround is a wrapper
  element, which would change the leaf markup. This is out of scope for #202 and no worse than today.
- **Placement.** The old theme override set `data-bs-placement="bottom"` on toolbar buttons. Upstream does not need
  to know about placement. A theme that wants it sets it in its adapter's `init(el)`.

## Resolved by #204

Option C landed in #204 (4b62ed6), with a bit more than the issue asked:

- **Markers with a location.** The marker carries the trigger's location, not just its presence:
  `data-cv-tooltip="context"` / `"list"` / `"card"` on icon-only action buttons and the filter toggle,
  `"card-order"` and `"formset"` on those controls, `"object-detail"` on the property-detail button. Labelled card
  buttons, menu items and the `⋯` toggle carry no marker.
- **The location reaches the adapter.** `tooltip.js` calls `cv.adapters.tooltip.init(el, {location})`. Adapters
  written as `init(el)` keep working.
- **The object-detail trigger reads `title`.** It moved from `data-bs-title` to `title`, so every trigger reads its
  text from `title`.
- **The formset controls' `title` is translated.** It is the translated text of their `aria-label` (`Move up`,
  `Move down`, `Add row`, `Delete row`).
- **Opt-out and recipes are documented.** Opt out with `cv.adapters.tooltip = {init() {}}`. `javascript.md` has a
  per-location recipe and a non-Bootstrap example; `inaccessible_actions.md` documents the disabled-button limitation.

The theme now overrides no button template. `tabler-adapters.js` uses the per-location recipe, so toolbar tooltips
open below the buttons as they did with the old overrides. Everything else is upstream's.

#205 (5e36477, closing #203) adds the lifecycle: optional `cv.adapters.tooltip.hide(el)` and `dispose(el)`, a click
on a trigger hides its tooltip, and the new `cv:modal:unload` event disposes the markers under `#cv-modal` before the
content is replaced. Because the theme replaces only `init`, it gets both Bootstrap defaults on `tabler.Tooltip`
without a change. Checked in the demo (`/customer/`): the filter toggle's tooltip goes away on a mouse click and on
Enter while the toggle keeps focus, and five open/close cycles of the delete modal (with a marked button injected
through `cv.initTooltips`, since the stock delete form has no marker) keep one `hide.bs.modal` handler on
`#cv-modal`; with `dispose` removed the count grows 1, 2, 3.
