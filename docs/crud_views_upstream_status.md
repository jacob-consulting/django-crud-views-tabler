# django-crud-views upstream questions: current state

Status snapshot for the five points in
[crud_views_upstream_questions.md](crud_views_upstream_questions.md). That document keeps the analysis, the code
paths and the options per point; this one says only where each point stands today and what is left to do. The
questions document is not edited.

## Update 2026-10-22: caught up with upstream e212dc3

Upstream moved 20 commits between 2026-10-21 and e212dc3 (branch `fix/form-enctype-multipart`, one ahead of `main`
at c79ec22). Against that checkout, before any theme change, three theme tests failed: the filter toggle now hides
its icon spans with `hidden` instead of `d-none` (#232), and five new `message-*` icon names had no Tabler mapping
(#222). What the theme does now:

- **Buttons:** `btn-icon` moved from the base action keys to `location:variant:icon` keys (#209, #216), so a labelled
  button in any location is no longer squared. The `card:tertiary` workaround is gone (ask 2 below is resolved);
  the demo's icon-only card action uses `label_mode="icon"` instead of `no_label=True`. Labelled card buttons show
  icon plus label again (upstream default `both`, #213).
- **Two bugs inherited by copying:** the theme's `view_create.content.html` lacked
  `enctype="multipart/form-data"` (#236) and both create and update rendered `{{ form.media }}` a second time
  (#191). Upstream had fixed both; the copies kept them. Fixed and pinned by tests. This is the drift #211 is
  about, in its quietest form: nothing failed, file uploads on create just arrived empty.
- **Messages:** `{% cv_messages %}` replaces the demo's `includes/messages.html`; the theme overrides
  `tags/messages.html` for Tabler's `.alert-icon` layout and maps the `message-*` icons.
- **Tests:** 75, OK; `manage.py check --fail-level WARNING` clean.
- **Overrides:** 11 (the 10 layout overrides plus `tags/messages.html`); 10 after #239 (below), and none of them
  copies a `<form>` any more. The upstream hooks that would remove most
  of them are filed as new issues; see "Upstream asks, round 2" below.

## What this was checked against (2026-10-21)

- **Upstream:** `/home/alex/projects/alex/django-crud-views`, branch `main` at **5e36477** (#205, tooltip
  lifecycle). The last commit that touches `src/crud_views/templates` is **4b62ed6** (#204), so the template
  audit recorded in the questions document at 4b62ed6 still describes HEAD; `git show --stat 5e36477` touches
  JavaScript, tests and docs only.
- **Theme:** this repository at **7799490** on `main` (clean apart from untracked `.run/`).
- **Install:** editable — `crud_views.__file__` resolves to the upstream checkout, so the theme runs against main,
  not against a released wheel.
- **Tests:** `uv run python manage.py test crud_views_tabler` → 47 tests, OK.
- **Upstream issue tracker:** six issues open: #191 (create view renders `form.media` twice), #89 (stability
  docs) and **#208**, **#209**, **#210**, **#211** — all four asks below, filed from this document on 2026-10-21.
  #202, raised by this theme, and #203, which came out of the #202 acceptance run upstream, are both closed.
- **Not run this session:** no browser verification. The demo has no formset page, so nothing here exercises
  `formset.js`.

## The five points

| # | Question | Resolved by | What the theme does now | Residual |
|---|---|---|---|---|
| 1 | [Icons hard-coded as Font Awesome classes](crud_views_upstream_questions.md#1-icons-font-awesome-class-names-hard-coded-in-several-places) | 0.30.0 (#198, #199): semantic icon registry | Registers a `tabler` library (inline SVG) and an icon per semantic name from `ready()` | none |
| 2 | [Button classes set in Python](crud_views_upstream_questions.md#2-button-classes-set-in-python) | #201 (e4bce00): `CrispyDeleteForm` hooks + layered class table | Registers `TABLER_BUTTON_CLASSES` with `form:delete`; uses stock `CrispyDeleteForm` | none |
| 3 | [jQuery and a global `bootstrap`](crud_views_upstream_questions.md#3-jquery-and-a-global-bootstrap) | #200 (440ac55): jQuery-free core + `cv.adapters`; #205 added the tooltip lifecycle | One asset, `tabler-adapters.js`, one statement; no jQuery, no shim | **open:** `formset.js` is still jQuery |
| 4 | [Marking a context action as primary](crud_views_upstream_questions.md#4-marking-a-context-action-as-the-pages-primary-action) | #201 (e4bce00): `cv_action_variant` + per-button `variant` | `context:primary` / `secondary` / `danger` in the class table; no key-based special case | none |
| 5 | [Overrides copy template logic, nothing detects drift](crud_views_upstream_questions.md#5-theme-overrides-have-to-copy-the-packages-template-logic) | #201 (leaves), #204 (tooltip markers) — **for buttons** | Overrides no button template; 10 layout overrides left | **open:** nothing detects a stale override |

Point by point, with the evidence behind "none":

- **1.** The second icon convention is gone too: `CRUD_VIEWS_OBJECT_DETAIL_ICONS_*` are listed as removed settings
  pointing at `CRUD_VIEWS_ICONS` / `BOOTSTRAP_ICONS` (`src/crud_views/lib/icons.py:226-229`), so core and object
  detail share one table.
- **2.** The unused `cv_submit_button` / `cv_cancel_button` / `cv_delete_button` tags the question asked about are
  removed, replaced by the class table (`docs/reference/buttons.md:248`).
- **3.** Resolved for every page without a formset. `formset.js` still needs jQuery and says so at runtime
  (`src/crud_views/static/crud_views/js/formset.js:633`); option C of the question (port it) was deferred and no
  upstream issue tracks it.
- **4.** `cv_action_variant` defaults to `secondary` (`lib/view/base.py:109`), `primary` on `CreateView`
  (`lib/views/create.py:27`) and on the polymorphic create-select view
  (`src/crud_views_polymorphic/lib/create_select.py:44`), `danger` on `DeleteView` (`lib/views/delete.py:49`);
  `ContextButton.variant` and `CardAction.variant` override per button. The part of the question that asked for a
  *visible label* on the primary action was settled the other way: the stock leaf keeps the label visually hidden
  and the maintainer accepted the icon-only blue button (recorded in
  [crud_views_tabler.md](crud_views_tabler.md#header-and-actions)).
- **5.** Option D landed for buttons and the leaf contract is documented (`docs/reference/buttons.md:178, 193`).
  Nothing was built for the drift problem itself: no template marker, no system check, and no contract
  documentation for the templates a theme still overrides.

## Still to do

### Upstream asks (#208-#211 filed on 2026-10-21; #217 added later the same day and already resolved)

1. **`cv-key=""` on the stock filter toggle.** `FilterContextButton.get_context()`
   (`src/crud_views/lib/view/buttons.py:295-328`) never puts `cv_key` in the context, while
   `templates/crud_views/tags/context_action_filter.html` renders `cv-key="{{ cv_key }}"`. Harmless today (no
   script reads that attribute on the toggle) but inconsistent with every other toolbar button, and a one-line fix.
   The theme no longer overrides that template, so it has to be fixed upstream. **Filed as
   [#208](https://github.com/jacob-consulting/django-crud-views/issues/208)** (2026-10-21), with the golden-file
   evidence, why the context is missing the key, `self.key` vs the list view's key, and acceptance criteria.
   **Fixed upstream in 5cc9240** (the toggle renders `cv-key="filter"`); #209-#211 not re-checked.
2. ~~**The class table cannot tell an icon-only card button from a labelled one.**~~ **Done (#209, #216);
   the theme uses `:icon` keys since 2026-10-22.** `card:tertiary` carries
   `btn-icon` because the demo's only tertiary card action is the icon-only delete; a project with a labelled
   tertiary card button has to override the key
   ([crud_views_tabler.md](crud_views_tabler.md#card-views), "limitation"). `cv_label_visible` is already part of
   the leaf contract (`lib/view/button_data.py:51`); it just never reaches `{% cv_button_class cv_location
   cv_variant %}`. This limitation appeared *with* #201 and is not in the questions document. **Filed as
   [#209](https://github.com/jacob-consulting/django-crud-views/issues/209)** (2026-10-21), weighing a label-mode
   segment in the key with a fallback (per mode: fine-tuning later, covers the non-additive ghost-vs-solid case)
   against one appended `icon-only` key (union: less code, one rule for all) — recommending the per-mode key,
   because the fallback makes it cost one table entry today while the additive rule cannot express a class swap.
3. **A jQuery-free `formset.js`** (option C of point 3). **Filed as
   [#210](https://github.com/jacob-consulting/django-crud-views/issues/210)**: 644 lines, one `$.ajax` plus jQuery
   selections as instance state, and — the part that lowers the risk — a documented surface that is *not*
   jQuery-shaped (the `cv:formset:row-added` event and "load jQuery"; the `X*` classes sit on `globalThis.cv` for
   the unit tests only). The original unknown stays: whether anything in the wild reaches into those classes. Low
   urgency here — the demo has no formset page.
4. **Something for drift** (point 5, options B/E), or at least option A for what is left. **Filed as
   [#211](https://github.com/jacob-consulting/django-crud-views/issues/211)**, with the three cases this theme hit
   in one upgrade (the `{% cv_filter_icon %}` `TemplateSyntaxError`, the silently dead `tags/icon.html` override,
   the `data-bs-dismiss` override that only worked by Bootstrap's accident) and two cheaper options than markers: a
   check for an override of a template the package no longer ships, and a `cv_template_overrides --diff` command for
   upgrade review. Recommends those two plus documenting the contract of the remaining templates.

5. ~~**An unreferenced template that hardcodes Bootstrap includes.**~~ **Done (#217).** `crud_views/detail/field.html`
   was a vendored copy of Bootstrap's `field.html` with four `bootstrap5/layout/...` includes, and nothing in the
   package rendered it. Filed as [#217](https://github.com/jacob-consulting/django-crud-views/issues/217) as a
   question (dead code or live?) with the exact greps; resolved as dead code in upstream commit 10d81ad, which
   removed the whole `crud_views/detail/` directory (`field.html` plus `widgets/{attrs,bool,display}.html`) and the
   `cv_is_true` / `cv_is_false` / `cv_is_list` filters that only those templates used. No template under
   `src/crud_views/templates/` contains `bootstrap5/` any more. The demo was unaffected either way; its guard test
   `test_form_and_detail_pages_use_no_bootstrap5_template` runs unskipped and green, and `crispy_bootstrap5` is out
   of the demo's `INSTALLED_APPS`.

### Upstream asks, round 2 (filed 2026-10-22): hooks that would remove layout overrides

| Issue | Hook | Tabler override it removes |
|---|---|---|
| [#239](https://github.com/jacob-consulting/django-crud-views/issues/239) **done (8fcb7f2)** | one frame template around the form; delete's protection alert as a snippet | `view_create`, `view_update`, `view_delete` `.content.html` → replaced by `snippets/form_frame.html` + `snippets/delete/protection_errors.html` |
| [#240](https://github.com/jacob-consulting/django-crud-views/issues/240) | `modal:root` / `modal:dialog` class keys | `modal/shell.html` |
| [#241](https://github.com/jacob-consulting/django-crud-views/issues/241) **done (3d2ee82)** | accessible pagination, `page-previous` / `page-next` icons | `snippets/pagination.html` deleted; the theme maps the two icons, and its table footer pagination uses them too |
| [#242](https://github.com/jacob-consulting/django-crud-views/issues/242) **closed, not planned** | filter card class instead of `<br>`, heading with class key | — the two filter overrides stay |
| [#243](https://github.com/jacob-consulting/django-crud-views/issues/243) **done (73b5037)** | card blocks (title, content, actions) and class keys | `tags/card.html` stays (the footer is structure, as upstream decided), but now uses upstream's block names (`card_footer` → `card_actions`) and `card:root` / `card:body` / `card:title`; the theme registers `card:root` = `card` |
| [#244](https://github.com/jacob-consulting/django-crud-views/issues/244) **closed, not planned** | card row class, shared empty-state snippet | — `view_card.content.html` stays. Split out of it: [#246](https://github.com/jacob-consulting/django-crud-views/issues/246) **done (337b1f6)**, the stock empty text is translated; the theme's empty state uses the same msgid, so it shows German too (pinned by `test_empty_state_is_translated`) |

Not filed: `table/bootstrap5.html` (the whole django-tables2 template in Tabler markup) and `tags/messages.html`
(small, genuinely Tabler-specific) stay theme overrides.

### Theme follow-ups

- **Re-diff the 9 overrides whenever an upstream release touches `src/crud_views/templates`.** Two commits up to
  10d81ad do: 3fc4be6 (#213/#218) touched `tags/button/action.html` and 10d81ad (#217) deleted `crud_views/detail/`.
  Neither path is among the 10 overrides, so they are still current. The drift surface is small but not empty: `tags/list_filter.html` and
  `tags/list_filter.inner.html` carry the pinned-filter contract, and `snippets/form_frame.html` must keep the
  `cv_form_body` block and leave the modal bare. (Until #239 the theme copied the create, update and delete
  `<form>`s here, and those copies missed #236 and #191; since 2026-10-22 the form is upstream's.) The others
  (`tags/card.html`, `view_card.content.html`, `modal/shell.html`,
  `table/bootstrap5.html`, `snippets/delete/protection_errors.html`, `tags/messages.html`) are layout and markup.
- **The "no jQuery" claim is verified for pages without formsets only** (`tests.py:159`). If the demo ever gets a
  formset page, it needs jQuery loaded, and the theme's documentation already says a project must load it itself.

### Questions from the document that are now moot, or still unanswered

| Question (from "Not known / not tested") | State |
|---|---|
| 1. Were the object-detail icon settings meant to grow into a package-wide mechanism? | Moot — 0.30.0 unified them into one table |
| 2. Are the unused `cv_*_button` tags used in the wild? | Moot — removed in #201 |
| 3. Does external code rely on the core scripts' jQuery usage? | Still unknown; now only `formset.js` is affected |
| 4. Is the stock look (every toolbar button equal) deliberate? | Answered in practice: the maintainer accepted the icon-only primary action |
| 5. Was "point 5 matters most" the right call? | Borne out: #201 plus #204 took the theme from 19 overrides to 10 and removed every logic-copying one |
