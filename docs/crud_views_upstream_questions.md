# django-crud-views: questions raised by the Tabler theme prototype

Four points came up while building `crud_views_tabler` (see [crud_views_tabler.md](crud_views_tabler.md)). For
each: what the package does today, why it matters for a theme, what the prototype does about it, and options with
their trade-offs.

## How this was checked, and what was not

- Every statement about the package is checked against the **installed django-crud-views 0.29.4** source
  (`.venv/lib/python3.14/site-packages/crud_views*`). File and line references are for that version.
- **Not checked:** the upstream repository's current main branch, its issue tracker, discussions, or anything after
  0.29.4. Some of these points may already be discussed, decided or changed there.
- Where something was not tried, it says so. "Not tested" means exactly that.
- Two statements in the first version of the design doc turned out to be wrong or incomplete on closer reading;
  they are corrected here and in the design doc (jQuery is used by four scripts, not two; context buttons can
  already have their own template).

---

## 1. Icons: Font Awesome class names hard-coded in several places

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
