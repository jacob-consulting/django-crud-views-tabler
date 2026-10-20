# django-crud-views: questions raised by the Tabler theme prototype

Five points came up while building `crud_views_tabler` (see [crud_views_tabler.md](crud_views_tabler.md)). For
each: what the package does today, why it matters for a theme, what the prototype does about it, and options with
their trade-offs.

## How this was checked, and what was not

- Every statement about the package is checked against the **installed django-crud-views 0.29.4** source
  (`.venv/lib/python3.14/site-packages/crud_views*`). File and line references are for that version.
- **Not checked at the time of writing:** the upstream repository's current main branch, its issue tracker, discussions, or anything after
  0.29.4. Some of these points may already be discussed, decided or changed there.
- **Update 2026-10-20:** the "Status" block under each point was checked against the upstream checkout
  (`/home/alex/projects/alex/django-crud-views`, branch `main` at 440ac55: 0.30.0 plus the unreleased #200) by diffing
  `v0.29.4..main` for `src/crud_views/templates` and `src/crud_views/static` and reading `docs/reference/icons.md`
  and `docs/reference/javascript.md`. The original analysis and its file/line references remain for 0.29.4.
- **Update 2026-10-20 (later):** points 2, 4 and 5 got a second Status block for main @ 4b62ed6 (#201 button
  variants, class table and leaves; #204 tooltip markers), checked by reading `docs/reference/buttons.md`, the
  CHANGELOG and the stock templates, and by moving the theme onto them.
- Where something was not tried, it says so. "Not tested" means exactly that.
- Two statements in the first version of the design doc turned out to be wrong or incomplete on closer reading;
  they are corrected here and in the design doc (jQuery is used by four scripts, not two; context buttons can
  already have their own template).

---

## 1. Icons: Font Awesome class names hard-coded in several places

### Status (upstream main @ 440ac55, 2026-10-20)

**What upstream did (0.30.0):** a semantic icon registry (`crud_views.lib.icons`, `docs/reference/icons.md`). The
package refers to icons by name (`detail`, `delete`, `filter`, …: 27 names); the table is layered (package defaults,
theme registrations from `AppConfig.ready()`, `CRUD_VIEWS_ICONS`); values are `prefix:name` with a renderer per
library (`far`, `fas`, `bi` built in; the `font` renderer or any callable); one tag, `{% cv_icon %}`, renders
everything; `cv_icon_action`, `cv_icon_header` and `cv_menu_icon` carry icon values, not classes; object detail uses
the same table. `tags/icon.html`, `{% cv_filter_icon %}`, `CRUD_VIEWS_FILTER_ICON`, `CRUD_VIEWS_ACTIONS_MENU_ICON` and
the object-detail icon settings are gone, guarded by the checks `crud_views.E350`–`E356`, `W352`, `W353` and
`viewset.W246`.

**How it maps to the options:** option C, with a library/renderer layer on top. The compatibility rule is the one C
predicted: a colon-less value that is not a known name is a raw CSS class.

**What the theme does now:** registers a `tabler` library (inline-SVG renderer) and a Tabler icon for every semantic
name from `ready()`. The Font Awesome table, `{% cvt_icon %}` and `tags/icon.html` are gone; formset, boolean,
object-detail and language-selector icons are Tabler without any template override. Resolved.

### What the package does today

Icons are Font Awesome CSS class strings rendered as `<i class="…">`. They come from four kinds of places:

| Where | Examples (0.29.4) | Can a project change it today? |
|---|---|---|
| Class attributes on view classes | `cv_icon_action = "fa-regular fa-eye"` (`lib/views/detail.py:19`), likewise list, create, update, delete, card, manage, ordered up/down; polymorphic `create_select`; workflow views | Yes, per view: set `cv_icon_action` / `cv_icon_header` on the project's view class |
| ViewSet | `icon_header` (used for the header, and for parent/child/sibling buttons, `lib/view/buttons.py:135,210,266`) | Yes, per ViewSet |
| Settings | `CRUD_VIEWS_FILTER_ICON`, `CRUD_VIEWS_ACTIONS_MENU_ICON` (`lib/settings.py:54,62`) | Yes |
| Hard-coded in templates / JS | `snippets/card_order.html:15,20`, `table/bootstrap5.html:16-17`, `formsets/control.html:9-25`, `detail/widgets/display.html:3`, `detail/widgets/bool.html:4-8`, `snippets/language_selector.html:6`; `fa-fw` in `tags/actions_menu_item_label.html:1`; `list.filter.js:28` toggles `fa-filter fa-filter-circle-xmark` | Only by overriding the template; the JS line not at all (harmless if the icon is not an `<i>`) |

`crud_views_object_detail` already has its own, different icon abstraction: `CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY`
(`"bootstrap"` by default, or `"fontawesome"`), plus class/type/prefix and named-icon settings
(`crud_views_object_detail/lib/conf.py`). So the package currently uses two icon conventions: Font Awesome in core,
Bootstrap Icons by default in object detail.

### Why it matters for a theme

A theme cannot change the defaults without the project's cooperation: the defaults live on view classes the
project subclasses, not in templates the theme can override. And icon *fonts* are assumed: the value is always a
CSS class for `<i>`. Libraries that ship inline SVG (Tabler Icons, Heroicons, Lucide) or SVG sprites do not fit
that model.

### What the prototype does

It maps at render time: the theme's templates call `{% cvt_icon value %}`, which turns known Font Awesome class
strings into inline Tabler SVG (`crud_views_tabler/icons.py`) and falls back to the original `<i class>` for
anything unknown. It needs a mapping table and one exact-match special case (`fa-solid fa-rectangle-list` for card
views vs `fa-regular fa-rectangle-list` for list views), and it only covers templates the theme overrides; the
formset, object-detail widget and language-selector icons are still Font Awesome.

### Options

**A. Keep it as it is; themes map at render time** (what the prototype does).
- Pro: no change upstream, nothing breaks.
- Con: every theme maintains a Font Awesome → own-icons table and has to override every template with a hard-coded
  icon. A project-defined icon outside the table falls back to `<i class>`, i.e. needs Font Awesome loaded anyway.

**B. A settings dict of default icons by semantic name**, e.g. `CRUD_VIEWS_ICONS = {"detail": "…", "update": "…"}`,
read by the view classes and templates instead of literals.
- Pro: one place to switch icon sets; backwards compatible if the defaults stay Font Awesome; the existing
  per-view attributes keep working as overrides.
- Con: still class strings for `<i>`, so it helps icon fonts (Bootstrap Icons, Tabler's webfont) but not inline
  SVG. A theme app cannot set a project's settings; it can only document what to put there.

**C. Semantic icon names plus one overridable render point**, e.g. `{% cv_icon "detail" %}` rendering
`crud_views/tags/icon.html` (which already exists for header/filter icons), used by all templates.
- Pro: a theme overrides one template (or a small registry) and can emit SVG, sprites or fonts; the hard-coded
  template icons go away; object detail could use the same mechanism instead of its own.
- Con: the largest change: about 15 templates, the view defaults and object detail. Existing projects that set
  `cv_icon_action = "fa-…"` need a compatibility rule (for example "a value that is not a known name is a raw CSS
  class"). The set of semantic names becomes public API.

### Not known / not tested

Whether the object-detail icon settings were meant to grow into a package-wide mechanism; option B or C has not
been prototyped.

---

## 2. Button classes set in Python

### Status (upstream main @ 440ac55, 2026-10-20)

Not changed on main. A draft design in the upstream repository,
`superpowers/specs/2026-10-19-button-variants-and-leaves-design.md`, gives `CrispyDeleteForm` the missing
`get_delete_button()` / `get_delete_button_kwargs()` hooks and moves every button class into a layered table
(`CRUD_VIEWS_BUTTON_CLASSES`, `register_button_classes()` for themes): option A plus option B, without the
contradictory-classes problem because the package would ship its own `Submit` subclass reading the table. Not
implemented; the theme keeps `TablerDeleteForm`.

### Status (upstream main @ 4b62ed6, 2026-10-20)

Resolved by #201 (e4bce00): option A plus option B, as the draft above described.
- `CrispyDeleteForm.get_delete_button()` / `get_delete_button_kwargs()`, slot `form:delete`.
- Every button class in the layered table `crud_views.lib.button_classes`: package defaults, then
  `register_button_classes()` from a theme's `ready()`, then `CRUD_VIEWS_BUTTON_CLASSES`.
- `crud_views.lib.crispy.Submit` / `Button` / `Reset` read the table, so no contradictory `btn-primary btn-danger`.
- `CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS` is gone (`crud_views.E360`).

**What the theme does now:** it registers `TABLER_BUTTON_CLASSES` (`crud_views_tabler/buttons.py`) from `ready()`,
with `form:delete` = `btn btn-danger`. `TablerDeleteForm` and `DangerSubmit` are removed, and the demo's delete view
uses the stock `CrispyDeleteForm`. Resolved.


### What the package does today

- Form buttons are crispy-forms layout objects. crispy's `Submit` has `field_classes = "btn btn-primary"`, and a
  `css_class` argument is **appended**, not substituted (`crispy_forms/layout.py:244-245, 323`).
- `CrispyFormMixin` already has hooks per form class: `get_submit_button_kwargs()` / `get_submit_button()` and
  `get_cancel_button_kwargs()` / `get_cancel_button()` (`lib/crispy/form.py:55-82`). The cancel button's class is
  the literal `"btn btn-secondary"` inside `get_cancel_button_kwargs()` (`form.py:77`).
- `CrispyDeleteForm` does **not** use those hooks: its `helper` property builds `Submit("delete", "Delete")` inline
  (`form.py:116-133`). The only way to change the Delete button is to override the whole `helper`.
- The filter reset button already has a setting: `CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS` (`lib/settings.py:64`).
- The template tags `cv_cancel_button`, `cv_submit_button`, `cv_delete_button` (templates `tags/button_*.html`)
  are registered but not used by any template the package ships; `button_delete.html` is a bare
  `<input type="submit" value="Delete">` without classes.

### Why it matters for a theme

Templates are the theme's lever; button classes in Python are out of its reach. In practice this is cosmetic:
Bootstrap's `btn-primary` / `btn-secondary` render fine in Tabler. The visible gap in the prototype was that the
destructive Delete button is blue.

### What the prototype does

`crud_views_tabler.forms.TablerDeleteForm` overrides `helper` and uses a `DangerSubmit(Submit)` subclass with
`field_classes = "btn btn-danger"`; the demo sets `form_class = TablerDeleteForm`. Every project has to opt in.

A simpler variant, `Submit("delete", "Delete", css_class="btn-danger")`, produces `btn btn-primary btn-danger`. In
Tabler 1.6.1 that renders red only because `.btn-danger` comes after `.btn-primary` in the stylesheet with equal
specificity (`tabler.css` lines 17375 vs 17415). It works, but it depends on rule order and leaves contradictory
classes, so the prototype does not use it.

### Options

**A. Add a `get_delete_button()` / `get_delete_button_kwargs()` hook to `CrispyDeleteForm`**, mirroring the
existing submit/cancel hooks.
- Pro: small, non-breaking, consistent with the rest of the mixin; a project changes the button by overriding one
  method.
- Con: still per project (or per project base class); a theme app cannot apply it by itself.

**B. Settings for button classes**, like the existing filter reset setting (e.g. cancel, submit, delete).
- Pro: project-wide in one place; consistent with `CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS`.
- Con: because crispy appends `css_class` to `btn btn-primary`, a "delete class" setting would either produce
  contradictory classes or require crud_views to use its own `Submit` subclass with configurable `field_classes`.
  More settings to document.

**C. Leave it.**
- Pro: no work; the defaults look acceptable in Bootstrap-based themes.
- Con: every project that wants a red Delete subclasses `CrispyDeleteForm`.

Separately: the unused `cv_*_button` tags could either be removed or documented; as they are, they suggest a
template-based mechanism that the shipped templates do not use.

### Not known / not tested

Whether the unused tags are used by projects in the wild, or kept for compatibility.

---

## 3. jQuery and a global `bootstrap`

### Status (upstream main @ 440ac55, 2026-10-20)

**What upstream did (#200, unreleased):** `viewset.js`, `modal.js`, `list.filter.js` and `tooltip.js` use the DOM API
and `fetch`; `formset.js` stays on jQuery, logs one `console.error` without it and retries once on `window` `load`.
Every call into Bootstrap goes through `cv.adapters` (`modal.show` / `hide` / `setSize`, `tooltip.init`,
`collapse.toggle`), defined in a new first core script, `adapters.js`, pre-filled for `globalThis.bootstrap`;
`cv.bootstrapAdapters(ns)` builds all three for any Bootstrap-compatible namespace, `ns` being an object or a function
resolved on every call. New contracts: `crud_views/modal/shell.html` (ids `cv-modal`, `cv-modal-dialog`,
`cv-modal-content`), `data-cv-modal-dismiss`, `cv_modal_size` tokens `""` / `sm` / `lg` / `xl` (`viewset.E250`), and
the filter toggle's `aria-expanded`, `aria-controls="filter-collapse"` and `data-cv-filter-icon` spans
(`docs/reference/javascript.md`).

**How it maps to the options:** B (the three small scripts, plus tooltip.js), with C deferred (formset.js). The
"configured global" idea became an adapter object with a lazily resolved namespace, which also removes the load-order
trap: Bootstrap may load anywhere, deferred included.

**What the theme does now:** no jQuery, no shim. One registered asset, `tabler-adapters.js`, holds one statement:
`Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler))`. `shared/js.html` is no longer
overridden. Resolved for every page without formsets; a project with formsets loads jQuery itself.

### What the package does today

Four of the six core scripts use jQuery; none of this is declared anywhere a project would see it (the Python
package metadata cannot declare JS dependencies, and I found no mention in the package README/metadata; the
django-crud-views skill only implies it through a pipeline example that lists `js/jquery.js` first).

| Script | Size | jQuery use | Effect without jQuery |
|---|---|---|---|
| `viewset.js` | 33 lines | `$(document).ready`, delegated handlers for `data-cv-action="submit-form"` (POST list/context actions), `submit-on-change` (card order combo), `data-cv-cancel-url` (cancel buttons) | POST actions, cancel buttons and the signed card-order combo stop working |
| `modal.js` | 115 lines | `$(document).ready`, delegated click on `[data-cv-modal='true']`, submit inside the modal | modals do not open |
| `list.filter.js` | 53 lines | click handlers, `$.post` to persist the expanded state, `collapse.collapse("toggle")` | filter toggle does nothing |
| `formset.js` | 620 lines | `$.ajax`, selections passed around; its docstrings describe parameters as "jQuery selection" | formsets do not work |
| `toggle.js`, `tooltip.js` | 67 / 40 lines | none | — |

`collapse.collapse("toggle")` uses **Bootstrap's jQuery plugin interface**, which Bootstrap 5 only registers if
jQuery is already present when Bootstrap initialises. So it is not just "jQuery is required" but also "jQuery must
load before Bootstrap". With Bootstrap's own bundle that order is the natural one; with Tabler (Bootstrap compiled
into `tabler.min.js`, loaded first and deferred) it is not.

`modal.js` (line 27) requires a global `bootstrap.Modal` and throws without it; `tooltip.js` uses
`globalThis.bootstrap?.Tooltip` and silently skips without it. Bootstrap's bundle defines `window.bootstrap`;
Tabler's bundle exposes the same components on `window.tabler` instead.

### Why it matters for a theme

A Tabler page has neither jQuery nor `window.bootstrap`. The prototype first failed with
`collapse.collapse is not a function`; modals, POST actions and cancel buttons would have failed without jQuery.

### What the prototype does

The theme's `shared/js.html` loads jQuery 3.7.1 (CDN, SRI) and `bootstrap-shim.js`, which sets
`window.bootstrap = window.tabler` and registers Bootstrap's jQuery plugins after the fact; all scripts are
deferred so they run after `tabler.min.js`.

### Options

**A. Keep jQuery, document it, and remove the load-order trap.** Replace the jQuery plugin call in
`list.filter.js` with the Bootstrap API (`bootstrap.Collapse.getOrCreateInstance(el).toggle()`), as `modal.js`
already does for modals.
- Pro: one-line change; removes the undocumented "jQuery before Bootstrap" constraint; documenting jQuery as a
  requirement costs nothing.
- Con: jQuery stays a dependency (about 30 KB gzipped) on every crud_views page.

**B. Drop jQuery from the three small scripts** (`viewset.js`, `modal.js`, `list.filter.js`: about 200 lines, ~20
jQuery calls; delegated events become `addEventListener` + `closest()`, `$.post` becomes `fetch`).
- Pro: list, detail, card, create/update/delete and modal pages no longer need jQuery; fewer things for a theme
  to shim.
- Con: rewrite and re-test effort; projects that extended these scripts with jQuery assumptions could break (not
  known whether any do).

**C. B plus `formset.js`.**
- Pro: no jQuery at all.
- Con: the largest and riskiest part: 620 lines, and its documented API passes jQuery selections, so subclasses or
  integrations may depend on it. Could stay on jQuery (jQuery then needed only on formset pages).

On the global `bootstrap`: the package could look up `globalThis.bootstrap` only (today), or accept a configured
global. Special-casing Tabler (`globalThis.bootstrap ?? globalThis.tabler`) would work but ties the core to one
theme; a documented one-line alias in the theme (what the prototype does) is arguably the cleaner split.

### Not known / not tested

Whether external code relies on these scripts' jQuery usage; how much of formset.js is jQuery-shaped beyond the
six direct call sites counted (eight matches, two of them in comments). Options A–C have not been implemented.

---

## 4. Marking a context action as the page's primary action

### Status (upstream main @ 440ac55, 2026-10-20)

Not changed on main. The draft design named under point 2 adds `cv_action_variant` to every view (`CreateView` and
the polymorphic create-select view default to `primary`, `DeleteView` to `danger`, the rest to `secondary`), a
`ContextButton.variant` override, and `CardAction.variant = None` meaning "the target view's variant": options B and
C together. Not implemented; the theme still hard-codes `create` / `create_select` as the primary action.

### Status (upstream main @ 4b62ed6, 2026-10-20)

Resolved by #201 (e4bce00), as the draft above described: `cv_action_variant` on every view, with `ContextButton.variant`
and `CardAction.variant` as per-button overrides. Each variant has its own class-table keys (`context:primary`, …).

**What the theme does now:** it no longer keys on `create` / `create_select`. `context:primary` is
`btn btn-primary btn-icon`, and the stock leaf keeps the label visually hidden (shown as the tooltip). The toolbar's
primary action is therefore an icon-only blue button, not a labelled one, which the maintainer accepted.


### What the package does today

- **Card actions** have styling metadata: `CardAction(variant="primary" | "secondary" | "tertiary", flex=…,
  no_label=…)` (`lib/view/card.py:6-13`), passed to the template as `cv_variant` etc.
- **Context actions** (the page-level toolbar) have none. The stock `tags/context_action.html` renders every key
  the same way: icon-only `btn btn-outline-primary btn-lg` with a visually hidden label.
- There **is** a per-button escape hatch: `ContextButton` has `template` / `template_code`
  (`lib/view/buttons.py:27-28, 69-75`), buttons can be declared per view via `cv_context_buttons`
  (`lib/view/base.py:68`) and take precedence over views of the same key (`base.py:459-467`), and the default
  button template is configurable through `CRUD_VIEWS_CONTEXT_BUTTON_TEMPLATE` (`lib/settings.py`, the
  `context_button_template` property). That setting is not listed in the django-crud-views skill's settings
  reference I worked from.
- Buttons with a custom template are excluded from the `⋯` overflow menu (`lib/view/action_menu.py:80-85`,
  `cv_context_button_foldable`).

### Why it matters for a theme

Admin themes, Tabler included, usually give the page one emphasised action ("Create") with a visible label and
show the rest as secondary or icon buttons. The theme only sees keys and has no signal for which one is primary.

### What the prototype does

It hard-codes the keys `create` and `create_select` as primary (`btn-primary` with label) in the theme's
`tags/context_action.html`; every other key is an icon button. A project cannot make another key primary, or
`create` non-primary, without overriding that template.

### Options

**A. Status quo, using the existing hatch.** A project declares
`cv_context_buttons = [ContextButton(key="create", key_target="create", template="…/primary_button.html")]`.
- Pro: works today without upstream changes (per the code paths above; **not tested** in the prototype).
- Con: per view, verbose, the theme cannot apply it; such a button can no longer fold into the `⋯` menu.

**B. A `variant` field on `ContextButton`**, mirroring `CardAction.variant`, exposed as `cv_variant`.
- Pro: consistent with card actions; theme-neutral meaning; the stock template can ignore it, so no visual change
  by default; the button stays foldable.
- Con: still needs a `ContextButton` declaration per styled key, because plain string keys (`"create"`) carry no
  metadata today.

**C. A per-view mapping**, e.g. `cv_context_action_variants = {"create": "primary"}`, or a class default on the
target view (`CreateView` primary by default).
- Pro: works with plain keys; a class default gives every theme a sensible primary action without project config.
- Con: another attribute (and possibly a setting) to document; a class default bakes a UX opinion into the core;
  needs a rule for how it interacts with B if both exist.

### Not known / not tested

Option A was derived from reading the code, not run. Whether the stock look (all buttons equal) is a deliberate
design choice has not been asked.

---

## 5. Theme overrides have to copy the package's template logic

### Status (upstream main @ 440ac55, 2026-10-20)

Not changed on main. The draft design named under point 2 is option D: `cv_button_data()` normalises a button once in
Python, three leaves (`tags/button/action.html`, `menu_item.html`, `container.html`) only draw, and the current
template names become thin logic templates so whole-template overrides keep working. Its "Tabler check" section
counts what this theme would drop: the six logic-copying overrides become two leaf overrides plus a `ready()`
registration. Not implemented.

**Observed while following main (2026-10-20):** three of the theme's overrides had gone stale between 0.29.4 and
main. `tags/list_filter.inner.html` still called `{% cv_filter_icon %}`, removed in 0.30.0: a `TemplateSyntaxError`
on every list page with a filter (9 of the theme's 19 tests). `tags/icon.html` went silently dead: upstream deleted
the template and `{% cv_header_icon %}` renders through `render_icon()` now. `modal/content.html` kept
`data-bs-dismiss="modal"`, which still worked only because Tabler's data API handles it, not through the new
`cv.adapters.modal.hide`. One loud failure, two silent ones, found only by diffing upstream's templates against the
overrides: the failure mode this point describes.

**Override audit after the switch to `{% cv_icon %}` (2026-10-20):** every override was diffed against main. None
was a verbatim copy, but three differed only in ways the theme no longer needs and are gone: `modal/content.html`
(one flex class on the title, now a CSS rule), `tags/actions_menu_item_label.html` (Tabler's `dropdown-item-icon`
instead of `cv-icon-fw`, without upstream's placeholder for icon-less actions; the stylesheet now sizes and mutes
`.cv-icon-fw` in dropdown items) and `tags/breadcrumb.html` (no `<nav>` wrapper; upstream's is valid Tabler markup and
a better landmark). `tags/list_filter.html` stays, for two `<br>` the theme replaces with CSS spacing. That leaves 19
overrides.

**What the draft design would remove from those 19:** the action leaf (`tags/button/action.html`) replaces
`tags/context_action.html`, `tags/list_action.html`, `tags/list_action.inner.html` and `tags/card_action.html`; the
container leaf (`tags/button/container.html`) replaces `tags/context_actions.html` and `columns/actions.html`; class
table entries replace `tags/actions_menu_toggle.html` and `TablerDeleteForm` (`form:delete`). Seven overrides go and
two logic-free leaves come in: 14 files, none of them copying upstream's branching. Still overridden, because they change
markup rather than button classes: `tags/card.html` (blocks, footer), `view_card.content.html` (`row-deck`, empty
state), `view_create` / `view_update` / `view_delete.content.html` (card wrapper outside modals),
`modal/shell.html`, `snippets/card_order.html` (only its toggle classes would come from the table),
`snippets/pagination.html`, `table/bootstrap5.html`, `tags/list_filter.html` and `tags/list_filter.inner.html`.

**Suggestion for the draft:** let the stock action leaf and the filter toggle emit `data-cv-tooltip` whenever the
label is hidden. `tooltip.js` already initialises it through the adapter, and stock markup would gain tooltips too.
The theme would then drop `tags/context_action_filter.html` entirely (its classes come from the table), and its
action leaf would exist only for the visible primary label and `icon-sm`. If Tabler renders a `fieldset.btn-list`
like a `div.btn-list` (the draft's open question), the container leaf goes as well: 12 files.

### Status (upstream main @ 4b62ed6, 2026-10-20)

Resolved by #201 (e4bce00): option D as the draft above described (`cv_button_data()` normalises once, leaves only
draw, the old names are one-line logic templates). The stock leaf and the filter toggle carry the tooltip marker since #204 (4b62ed6, from this theme's issue
#202): `data-cv-tooltip="<location>"` next to `title`, and `tooltip.js` passes the location to
`cv.adapters.tooltip.init(el, {location})`.

**What the theme does now:** it overrides **no** button template. The nine action-related overrides went:
`tags/context_action.html`, `tags/list_action.html` (+ `.inner.html`), `tags/card_action.html`,
`tags/context_actions.html`, `columns/actions.html`, `tags/actions_menu_toggle.html`,
`tags/context_action_filter.html`, `snippets/card_order.html`. That takes the theme from 19 overrides to 10, without
the "two leaf overrides" the draft estimated, for two reasons. The maintainer chose stock markup over the old look
(an icon-only primary action and label-only card buttons were accepted), and #204 made the tooltip marker upstream's.

The ten that stay are about page layout, not buttons, and none copies upstream branching:
- `tags/card.html`: blocks for `cv_card_template`, `card-footer`; it includes upstream's container leaf
- `view_card.content.html`: `row-deck` grid, empty state
- `view_create.content.html`, `view_update.content.html`, `view_delete.content.html`: card wrapper outside modals
- `modal/shell.html`
- `snippets/pagination.html`
- `table/bootstrap5.html`
- `tags/list_filter.html` and `tags/list_filter.inner.html`

**Observed:** upstream's `tags/context_action_filter.html` renders `cv-key=""`, because `cv_key` is not in its
context. The old theme override had the same gap. It is harmless today (no script reads the filter toggle's
`cv-key`), but it is inconsistent with the other toolbar buttons.


### What the package does today

Theming means overriding templates under `crud_views/` (the hint of check `crud_views.W110` says so). Several of
those templates mix two things: deciding *what* to render (disabled, inaccessible, POST vs GET vs modal, inline vs
overflow menu, signed vs direction ordering) and *how* it looks (element, CSS classes, icon, label placement). An
override cannot change the second without copying the first.

How much logic the theme's 23 override files carry (counted from the variables they branch on: `cv_disabled`,
`cv_access`, `cv_action_enabled`, `cv_list_action_method`, `cv_modal`, `cv_is_active`, `cv_oid`, the
`group is None` / `group.inline` / `group.menu` / `group.all` menu branches, `cv_order_signed`, `cv_filter_pinned`):

| Category | Templates |
|---|---|
| Substantial copied logic (3–7 of those variables each) | `tags/context_action.html`, `tags/list_action.html` (via `list_action.inner.html`), `tags/card_action.html`, `tags/context_actions.html`, `columns/actions.html`, `tags/card.html` |
| Some copied logic or a contract to keep | `snippets/card_order.html` (signed mode, preserved params), `tags/list_filter.html` (pinned), `view_create/update/delete.content.html` (must post to `request.get_full_path` so `cv_from` survives; delete keeps the protection-error branch) |
| Presentation only | the remaining 12 (table, pagination, breadcrumb, modal header, menu toggle and item label, icon, filter header, card grid, script include) |

In the six "substantial" templates most of the theme's change is CSS classes and icons; the branching is copied
unchanged.

**Nothing detects a stale override.** The package checks that configured templates exist
(`lib/check.py:225`, `lib/settings.py:98`), not what an override contains. An earlier statement of mine that
`viewset.W290` guards part of this was wrong: W290 warns when a view's own `cv_*_actions_inline` names a key that is
not among its actions (`lib/view/action_menu.py:19-38`). The skill lists it next to "an override lacks the
`{% if group is None %}` branch" only because both show the same symptom, a missing `⋯` menu.

### Why it matters for a theme

When a later release changes the logic in one of these templates (a new button state, a new attribute the
JavaScript looks for, a new menu branch), a theme that copied the old version keeps rendering the old behaviour.
Nothing fails at startup; the feature is just missing or subtly wrong on themed sites. That is the same failure mode
the menu branch already shows. The more templates a theme overrides, the more of these it carries, and every
release needs a manual diff of all of them.

This is not Tabler-specific: any theme that is more than a colour change runs into it.

### What the prototype does

Copies the logic and changes the markup, keeping every hook it found (`cv-key`, `data-cv-*`,
`cv-list-container` / `cv-context-container`, the hidden POST forms, the menu branches). It has tests that render
the demo pages, but nothing compares its templates against the package's.

### Options

**A. Document the contract and leave the structure.** For each overridable template, document which variables,
branches and attributes an override must keep.
- Pro: no code change; helps every theme author immediately.
- Con: drift is still only caught by hand; the documentation itself has to be kept in sync with the templates.

**B. A cheap drift signal.** Stock templates carry a marker (e.g. `{# cv-template: context_action v3 #}`); a system
check warns when the resolved template for that name is an override with an older or missing marker.
- Pro: small to build; turns silent drift into a startup warning after an upgrade.
- Con: depends on maintainers bumping markers for every logic change and theme authors updating them honestly; it
  says *that* something changed, not *what*. Requires reading override sources at startup (cost not measured).

**C. Class hooks instead of overrides for style-only changes.** Stock templates read CSS classes from context,
filled from a setting (e.g. a dict of class names per location/variant: context button, list button, card button,
menu toggle).
- Pro: themes in the Bootstrap family that differ mainly in classes would override none of the logic templates.
- Con: covers classes only. The Tabler theme also changes structure (visible label on the primary action,
  `.btn-list` instead of `fieldset.btn-group`, icon placement), so it would still need some overrides. Another
  settings surface to design and document.

**D. Split logic from markup.** The logic template resolves one normalised button description (element `a` or
`button`, `href`, all `data-cv-*` attributes, disabled state and reason, label, icon, variant) and includes a small
leaf template that only draws it. Themes override the leaves.
- Pro: logic changes upstream reach themed sites automatically; a theme overrides a handful of small leaves
  instead of six logic templates; the leaf variables become an explicit, testable contract.
- Con: the largest refactor of the five items; the leaf contract becomes public API that is hard to change later;
  list, context, card and menu-item buttons differ enough that it may need several leaves; existing overrides of the
  current templates keep working only if the old templates stay in place for a deprecation period.

**E. Blocks plus a second template name.** Move the stock templates to a second name (e.g. `crud_views/base/…`)
with blocks around the presentational parts; `crud_views/…` simply extends them. A theme overrides
`crud_views/…`, extends `crud_views/base/…` and fills only the blocks. (An override cannot extend a template of
its own name, which is why the second name is needed.)
- Pro: plain Django template inheritance; can be introduced one template at a time; existing overrides keep
  working.
- Con: two names per template; the value depends on where the block boundaries are. A block that wraps a branch
  puts the logic back into the theme.

### Not known / not tested

None of B–E has been prototyped. My assessment that this matters more than the icon question is a judgment from
writing the overrides, not a measurement: the theme overrides most of these templates for class and structure
changes anyway, so central icon handling alone would remove few overrides, while a logic/markup split would remove
the riskiest ones.
