# Upstream findings from the Acme Roasters demo

Building the Acme Roasters back-office (apps `sales`, `catalog`, `roastery`, `shipping`, `showcase` under
`example/`) put the Tabler theme in front of nearly every django-crud-views feature: nested ViewSets, formsets,
conditional groups, workflow, polymorphic models, object detail packs, Guardian, resources, card views, custom
forms and the two django-crud-views-extensions widgets. This file collects every place where that needed a theme
CSS rule, a theme template override, or a workaround in the demo instead of an upstream hook, and every upstream bug
or awkwardness found on the way. Findings 4–5 are tracked in
[django-crud-views #319](https://github.com/jacob-consulting/django-crud-views/issues/319), finding 6 in
[#320](https://github.com/jacob-consulting/django-crud-views/issues/320), finding 7 in
[#322](https://github.com/jacob-consulting/django-crud-views/issues/322), findings 8–9 in
[#325](https://github.com/jacob-consulting/django-crud-views/issues/325), findings 10–11 in
[#326](https://github.com/jacob-consulting/django-crud-views/issues/326), and findings 12–14 and 16 in
[#327](https://github.com/jacob-consulting/django-crud-views/issues/327), findings 15 and 17 in
[#328](https://github.com/jacob-consulting/django-crud-views/issues/328), finding 18 in [#329](https://github.com/jacob-consulting/django-crud-views/issues/329)
(closed; adopted from [PR #345](https://github.com/jacob-consulting/django-crud-views/pull/345)), finding 22 in [#347](https://github.com/jacob-consulting/django-crud-views/issues/347)
(closed; implemented in [PR #348](https://github.com/jacob-consulting/django-crud-views/pull/348)), the first half of finding 23 in
[PR #336](https://github.com/jacob-consulting/django-crud-views/pull/336) (merged, no issue), finding 26 in
[#337](https://github.com/jacob-consulting/django-crud-views/issues/337) (closed), finding 27 in
[#314](https://github.com/jacob-consulting/django-crud-views/issues/314) (open, backlog; supersedes #311), finding 28 in
[#338](https://github.com/jacob-consulting/django-crud-views/issues/338) (closed; implemented in PR #342) and finding 29 in
[#339](https://github.com/jacob-consulting/django-crud-views/issues/339) (open). The remaining findings are candidates to
triage into issues for django-crud-views (and, where marked, django-crud-views-extensions). Finding 34 is tracked in
[#349](https://github.com/jacob-consulting/django-crud-views/issues/349) (open).

Upstream references (`path:line`) are against the sibling checkouts as of 2026-11-04: `../django-crud-views` `main`
@ `cf2bfc0f` ("Delete confirm checkbox spans the full row (#308) (#310)"; the demo was built from `b73337ce`, #309,
and nothing cited changed in between), `../django-crud-views-extensions` `main` @ `0d84859`. Paths without a repo
prefix are in django-crud-views; `ext:` marks the extensions repo; paths starting `src/crud_views_tabler/` or
`example/` are in this repo.

Severity: **blocker** (the feature cannot be shown without it), **annoyance** (works, but needs code a project
should not have to write, or breaks visibly without a theme fix), **cosmetic** (looks or reads wrong; harmless).
No finding is a blocker: everything the spec calls a must-have is in the demo.

The rule for this file: every theme CSS fix or override template, and every upstream bug or awkwardness, is logged
here in the same commit that introduces it. The older, theme-level asks (#208-#211 and round 2) and their status are
in [crud_views_upstream_status.md](crud_views_upstream_status.md).

## Summary

| # | Finding | Severity | What the theme / example does today |
|---|---|---|---|
| 1 | ["Show code" panel is example-only](#1-the-show-code-panel-is-example-only-upstream) | annoyance | own collector and lazy-loading panel in `example/config/` |
| 2 | [Tooltip recipe says to replace `init`](#2-the-tooltip-recipe-still-says-to-replace-init) | annoyance | theme wraps `init` and calls the original |
| 3 | [`Column1..12` hard-code `col-md-N`](#3-column1column12-hard-code-col-md-n) | cosmetic | nothing (Tabler uses the same grid) |
| 4 | [Workflow badge is a solid Bootstrap pill](#4-workflow-badgeenum-values-are-bootstrap-colour-names-the-badge-is-a-solid-pill) | annoyance | resolved #319: theme registers `workflow:badge-<colour>` as `badge bg-<colour>-lt`; override removed |
| 5 | [Workflow page has no card frame, history table not responsive](#5-the-workflow-page-is-not-framed-and-its-history-table-is-not-responsive) | cosmetic | resolved #319: upstream frame and `.table-responsive`; theme CSS removed, `workflow:history-table` set |
| 6 | [One permission gates every workflow transition](#6-workflowviewpermissionrequired-has-one-permission-for-every-transition) | annoyance | resolved #320: the order workflow follows upstream's documented per-transition recipe |
| 7 | [No refusal message, `WorkflowForm.clean()` returns None, no transition helper](#7-workflow-no-refusal-with-message-hook-workflowformclean-returns-none-no-helper-outside-the-view) | annoyance | resolved #322: model hook, transition buttons and upstream `run_transition`; form subclass and helper deleted |
| 8 | [Card template has no block above the title](#8-the-card-template-has-no-block-above-the-title) | annoyance | resolved #325: the theme card gains `card_root`/`card_header`; the product card extends it |
| 9 | [Card list as landing page needs `cv_key = "list"`](#9-a-card-list-as-the-landing-page-needs-cv_key--list) | cosmetic | resolved #325: upstream documents the recipe; the demo keeps its `cv_key`/`cv_path`/`cv_home_key` overrides (no new API) |
| 10 | [Polymorphic create-select shows lower-case type names](#10-polymorphic-create-select-shows-lower-case-type-names) | cosmetic | resolved #326: upstream labels; Continue/layout retained |
| 11 | [Polymorphic detail cannot vary property groups per kind](#11-a-polymorphic-detail-view-cannot-give-each-kind-its-own-property-groups) | annoyance | resolved #326: direct model mapping; catalog/check verified |
| 12 | [Object detail prints stored value of a `choices` field](#12-object-detail-prints-the-stored-value-of-a-field-with-choices) | annoyance | resolved #327: plain field names show the choice label |
| 13 | [Object detail shows model `help_text` under values](#13-object-detail-shows-model-help_text-in-the-value-column) | cosmetic | resolved #327: help text back on the model, hidden on detail pages |
| 14 | [Object detail renders a blank text field as an empty row](#14-object-detail-renders-a-blank-text-field-as-an-empty-row) | cosmetic | resolved #327: blank fields keep their row and show a dash |
| 15 | [Accordion pack opens every panel closed](#15-the-accordion-detail-pack-opens-every-panel-closed) | annoyance | resolved #328: the green lot detail uses the accordion, first group open |
| 16 | [`ObjectDetailMixin` + `ObjectDetailViewPermissionRequired` is an MRO error](#16-objectdetailmixin-plus-objectdetailviewpermissionrequired-is-an-mro-error) | cosmetic | documented upstream #327; permission-required class alone |
| 17 | [`tabs.js` reads `globalThis.bootstrap`](#17-tabsjs-looks-up-globalthisbootstrap-directly) | annoyance | resolved #328: tabs init through `cv.adapters.tab`; no theme code needed |
| 18 | [Header icon is drawn beside a custom header template](#18-the-header-icon-is-drawn-beside-a-custom-header-template) | cosmetic | resolved in #329 / PR #345; customer detail uses `cv_icon_header = Icon.NONE` |
| 19 | [Conditional groups toggle only on a checkbox](#19-conditional-groups-only-toggle-on-a-boolean-checkbox) | annoyance | transient `is_wholesale` checkbox drives `Customer.kind` |
| 20 | [No per-row conditional fields in formsets](#20-formsets-have-no-per-row-conditional-fields) | annoyance | `clean()`/`save()` clear the fields; `sales.js` disables them per row |
| 21 | [Bare `<legend>` in toggle groups and formsets](#21-toggle-groups-and-formsets-render-a-bare-legend) | cosmetic | theme CSS sizes `.cv-toggle-group > legend`, `.cv-formset-fieldset > legend` |
| 22 | [Compact formset repeats labels on every row](#22-a-compact-table-like-formset-repeats-its-labels-on-every-row) | cosmetic | **DONE upstream** #347 / PR #348: opt-in compact layouts; Tabler demo adoption remains follow-up |
| 23 | [Guardian child views need their own gate; no child tabs](#23-child-viewsets-under-a-guardian-parent-need-their-own-gate-no-page-tabs-for-children) | annoyance | parent gate implemented upstream (#336) and adopted (`CustomerGrantMixin` removed); child tabs open; context buttons instead of tabs |
| 24 | [Custom no-object permission needs an undocumented recipe](#24-a-no-object-custom-form-needs-an-undocumented-recipe-for-its-own-permission) | annoyance | **DONE** upstream #341 (PR #343); existing demo permission recipe documented and verified; startup check clean |
| 25 | [Manage pages are open to every user under DEBUG](#25-manage-pages-are-open-to-every-signed-in-user-while-debug-is-on) | annoyance | `CRUD_VIEWS_MANAGE_VIEWS_ENABLED = "no"` by default in the demo |
| 26 | [`Table` forces `sequence` and always adds the actions column](#26-table-forces-sequence-and-always-adds-the-actions-column) | annoyance | resolved #337: tables declare `Meta.sequence` (the `__init__` workaround is gone); `Meta.exclude = ("actions",)` drops the column |
| 27 | [Second top-level ViewSet on a child model needs hand-made links](#27-a-second-top-level-viewset-on-a-child-model-needs-hand-made-links) | cosmetic | tracked in #314 (open, backlog); `render_number` and `get_success_url` reverse the nested URLs |
| 28 | [Two ViewSets on one model share every default label](#28-two-viewsets-on-one-model-share-every-default-label) | cosmetic | **DONE** — [PR #342](https://github.com/jacob-consulting/django-crud-views/pull/342) (#338); adopted in both subscription ViewSets; list-header overrides removed |
| 29 | [Snippet templates see the object, not the view](#29-snippet-templates-only-see-the-object-not-the-view) | cosmetic | **DONE** upstream #339 (closed 2026-11-10); adopted: duplicate message names the new draft; nested create heading names the customer |
| 30 | ext: [Datetimepicker assets on every page, need jQuery](#30-ext-the-datetimepicker-assets-load-on-every-page-and-need-jquery) | annoyance | project head include loads jQuery 3.7.1 |
| 31 | ext: [Typeahead skins read Bootstrap's `--bs-*` properties](#31-ext-the-typeahead-skins-read-bootstraps---bs--custom-properties) | annoyance | theme CSS maps `--bs-*` to Tabler's `--tblr-*` |
| 32 | ext: [Datetimepicker keeps its own look](#32-ext-the-datetimepicker-keeps-its-own-look) | cosmetic | nothing |
| 33 | [Workflow transition buttons ignore `variant` and `icon`](#33-workflow-transition-buttons-ignore-the-transitions-variant-and-icon) | cosmetic | nothing (all transitions are primary buttons without icon) |
| 34 | [Compact formsets reject custom `Select` subclasses](#34-compact-formsets-reject-custom-select-subclasses) | cosmetic | order lines keep their classic formset; upstream #349 asks for a bounded compatibility path |

---

## Example project and documentation

### 1. The "show code" panel is example-only upstream

- **What happened:** the `{% snippet_panels %}` tag that renders "the code behind this page" lives in the upstream
  example project, not in the library. Every theme or demo that wants the panel copies it (the extensions repo
  already did). Hooking it in needed no new block: with `CRUD_VIEWS_EXTENDS` pointing at the project's own template,
  the panel goes below the theme page's `content` block and the "Show code" toggle into its `actions` block
  (`{{ block.super }}` keeps `cv_context_actions`). Modal partials render `cv_content_template` without the extends
  chain, so the panel never shows inside a modal. The view is in the context as `view`, which is all a collector
  needs (`type(view).__module__` names the app).
- **Where:** `examples/bootstrap5/project/templatetags/example_tags.py:52` (`snippet_panels`), used at
  `examples/bootstrap5/project/templates/project/crud_views.html:41`; copied in
  `ext:examples/bootstrap5/project/templatetags/example_tags.py`.
- **What we did:** our own collector in the example project, `example/config/showcode.py` (a fixed file set per app,
  the app must live in `example/`, settings.py only as a whitelist of assignments), and the `showcode` tag library in
  `example/config/templatetags/`. The crud page carries only a collapsed shell; `example/static/acme/code-panel.js`
  fetches the highlighted sources from `/_code/<app_label>/` (login required, label checked against the app registry)
  the first time the panel opens. Inlining them, as upstream's tag does, put every label the app can render into the
  page: `assertContains`/`assertNotContains` tests then pass or fail on the source rather than the rendered page, and
  a `sales` page grew by about 390 KB. Pygments uses CSS classes; `/_code/pygments.css` scopes a light and a dark
  style by `data-bs-theme`.
- **Suggested upstream change:** ship the tag (or a documented recipe) in the library, loading the sources on demand.
- **Severity:** annoyance.

### 2. The tooltip recipe still says to replace `init`

- **What happened:** the documented way to add per-location tooltip configuration is to assign
  `cv.adapters.tooltip.init = ...`. That drops upstream's Bootstrap transition guard in the original `init`; the
  tooltip object also carries `hide`/`dispose`, so replacing the whole object (the other example) is worse.
- **Where:** `docs/reference/javascript.md:142` (assigns `init`) and `:123` (`cv.adapters.tooltip = {init() {}}`).
- **What we did:** the theme wraps `init` and calls the original
  (`src/crud_views_tabler/static/crud_views_tabler/tabler-adapters.js`).
- **Suggested upstream change:** change the recipe to wrap the original `init`, or expose a supported per-location
  hook so nobody needs to touch `init`.
- **Severity:** annoyance.

### 3. `Column1..Column12` hard-code `col-md-N`

- **What happened:** the crispy layout helpers `Column1` ... `Column12` set `css_class = "col-md-N"`. Right for
  Tabler (same grid as Bootstrap 5), but a theme on another grid cannot change the breakpoint or the class prefix
  without subclassing every helper.
- **Where:** `src/crud_views/lib/crispy/table.py:4` (`Column1`, and the eleven after it).
- **What we did:** nothing.
- **Suggested upstream change:** a documentation note, or a setting for the breakpoint.
- **Severity:** cosmetic.

## Workflow

### 4. Workflow `BadgeEnum` values are Bootstrap colour names; the badge is a solid pill

- **Implemented upstream:** [issue #319](https://github.com/jacob-consulting/django-crud-views/issues/319)
  (closed 2026-11-05), [PR #323](https://github.com/jacob-consulting/django-crud-views/pull/323) (phase 06.12, merge
  `cb35b1aa`); not a claim about a published release. Themeable workflow state badges, shared with finding 5.
- **Adopted here:** in `c3a4e83`. The theme registers `workflow:badge-<colour>` → `badge bg-<colour>-lt` for every
  `BadgeEnum` value in `src/crud_views_tabler/buttons.py` (only when `crud_views_workflow` is installed, see
  `apps.py`); the `crud_views_workflow/badge.html` override is deleted. Tested in
  `tests/crud_views_tabler/test_theme.py` (`test_all_state_colours_are_light_badges`).

- **What happened:** `BadgeEnum` is documented as "Bootstrap contextual colours for state badges" (`primary`,
  `success`, `danger`, `light`, `dark`, ...), and `crud_views_workflow/badge.html` pastes the value into
  `badge rounded-pill text-bg-<colour>`, a solid pill. Tabler's status badges are the light variants
  (`bg-green-lt`, ...). There is no hook for the class, and CSS could only restyle `text-bg-*` colour by colour, on
  every such badge of a project.
- **Where:** `src/crud_views_workflow/lib/enums.py:10` (`BadgeEnum`),
  `src/crud_views_workflow/templates/crud_views_workflow/badge.html:1`, rendered by `WorkflowModelMixin.get_state_badge`
  (`src/crud_views_workflow/lib/mixins.py:37`).
- **What we did before #319:** a one-line theme override, `src/crud_views_tabler/templates/crud_views_workflow/badge.html`
  (`badge bg-<colour>-lt`; every `BadgeEnum` value has a `-lt` class in Tabler 1.6.1), tested in
  `tests/crud_views_tabler/test_theme.py`. It is deleted now (see "Adopted here").
- **Suggested upstream change:** a class key for the badge (`workflow:badge` → `badge rounded-pill text-bg-{colour}`),
  or let `STATE_BADGES` values be class strings.
- **Severity:** annoyance.

### 5. The workflow page is not framed, and its history table is not responsive

- **Implemented upstream:** [issue #319](https://github.com/jacob-consulting/django-crud-views/issues/319)
  (closed 2026-11-05), [PR #323](https://github.com/jacob-consulting/django-crud-views/pull/323) (phase 06.12, merge
  `cb35b1aa`); not a claim about a published release. The action form uses the shared form frame and the history table is responsive, shared with finding 4.
- **Adopted here:** in `c3a4e83` the sideways-scroll CSS was removed from `crud_views_tabler.css`; upstream's
  `.table-responsive` wrapper (`workflow:history-wrapper`) and the form frame (a card around the action form) now
  apply, asserted in `test_theme.py` (`test_action_frame_history_order_and_error_ownership`). The rendered order
  workflow page's history table was a bare `table` while the theme's list tables are `table table-vcenter card-table`,
  so the theme now sets `workflow:history-table` to `table table-vcenter` (`buttons.py`; `card-table` left out
  because the history is not inside a card), tested by `test_history_table_matches_the_theme_list_table`.

- **What happened:** `view_workflow.content.html` renders the history and the form straight into the page, not
  through `crud_views/snippets/form_frame.html`, so under the theme the workflow page has no card while every
  create/update/delete/custom-form page does. The history is a bare `<table class="table">` with no
  `.table-responsive` wrapper and no class of its own; at 390 px it was 549 px wide and the whole page scrolled
  sideways.
- **Where:** `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.content.html:3-5`,
  `view_workflow.history.html:6` (the table), `view_workflow.action.html:7` (the form).
- **What we did before #319:** theme CSS (`crud_views_tabler.css`): below 768 px the content container that held such
  a table (`.page-body > .container-xl:has(> table.table)`) got `overflow-x: auto`, so it scrolled instead of the
  page; the table stayed a table, so a narrow one still spanned the full width (`display: block` on the table would
  have shrunk it). The scrollbar sat at the bottom of the content, not under the table. There was no frame: the order
  page has its own history and transition buttons; the workflow page was the fallback for steps that need a comment.
  The CSS is removed now (see "Adopted here").
- **Suggested upstream change:** use the form frame for the action form, wrap the history in `.table-responsive`
  (or a `workflow:history` class key).
- **Severity:** cosmetic.

### 6. `WorkflowViewPermissionRequired` has one permission for every transition

- **Implemented upstream:** [issue #320](https://github.com/jacob-consulting/django-crud-views/issues/320)
  (closed 2026-11-06), [PR #324](https://github.com/jacob-consulting/django-crud-views/pull/324) (phase 06.13, merge
  `d7c8e170`); not a claim about a published release. The opt-in per-transition permission recipe is documented and tested; the default `"change"` gate stays.
- **Adopted here:** the code was already upstream's documented opt-in recipe (`docs/reference/workflow_view.md`:
  `cv_permission = "view"`, django-fsm `permission=` per transition, `cv_action_enabled` returning
  `obj is None or obj.workflow_has_any_possible_transition(user)`), so it is unchanged; the `OrderWorkflowView` module
  docstring (`example/sales/views/order_actions.py`) now points at that recipe.

- **What happened:** the workflow view checks one `cv_permission` (`"change"`) before any transition is offered. The
  roastery's Roasters may take one step (confirmed → roasted) and otherwise only view orders. django-fsm's own
  `permission=` on `@transition` supports per-step rules, and upstream filters the offered steps through
  `get_available_user_state_transitions(user)`, so that part works; but the view-level gate has to be lowered to
  `"view"` for it to matter, which nothing documents.
- **Where:** `src/crud_views_workflow/lib/views.py:147` (`cv_permission = "change"`),
  `src/crud_views_workflow/lib/mixins.py:84` (`workflow_get_possible_transitions`).
- **What we did:** `OrderWorkflowView.cv_permission = "view"`; each transition carries `permission=may_change_order`
  or `may_roast_order` (`example/sales/models.py`); `cv_action_enabled` disables the workflow action when the user has
  no step left (`example/sales/views/order_actions.py`). A disallowed step posted anyway is not a choice of the form,
  so it fails validation.
- **Suggested upstream change:** document the `permission=` + `cv_permission = "view"` recipe, or make the default
  gate "any possible transition".
- **Severity:** annoyance.

### 7. Workflow: no refusal-with-message hook, `WorkflowForm.clean()` returns None, no helper outside the view

- **Implemented upstream:** [issue #322](https://github.com/jacob-consulting/django-crud-views/issues/322)
  (closed 2026-11-06), [PR #332](https://github.com/jacob-consulting/django-crud-views/pull/332) (phase 06.13.1, merge
  `fa7cc2d9`); not a claim about a published release. Model business-validation hook, opt-in transition buttons, `clean()` return fix and a reusable execution helper.
- **Adopted here:** `Order.workflow_check_transition` raises `ValidationError(confirm_problem())` for `wf_confirm`
  (`example/sales/models.py`; the guard inside `wf_confirm` stays for direct calls); `OrderWorkflowView` uses
  upstream's `WorkflowForm` with `cv_transition_presentation = "buttons"`, so Confirm shows disabled with its reason;
  `get_initial` and the order page's `?transition=` query string are gone (a step needing a comment links to the
  plain workflow page, where the user types the comment and clicks that step's button). The seed calls upstream's
  `crud_views_workflow.lib.run_transition` and backdates the `WorkflowInfo` row (`example/sales/seed.py`).
  `OrderWorkflowForm` and `example/sales/workflow.py` are deleted. Tested in `example/sales/tests/test_orders.py`
  (`OrderWorkflowTests`, `SeedHistoryTests`).

- **What happened:** (1) "Confirm only with at least one line" can be a django-fsm `conditions=[...]`, but then the
  step silently disappears and a posted confirm fails as "Select a valid choice". To show a reason the project has to
  subclass `WorkflowForm`. (2) `WorkflowForm.clean()` returns `None` instead of `cleaned_data`, so a subclass that
  writes `cleaned = super().clean()` crashes with `'NoneType' object has no attribute 'get'`. (3) Running a
  transition from code (seed data, a scheduled job) with its `WorkflowInfo` row means copying
  `WorkflowView.cv_form_valid`.
- **Where:** `src/crud_views_workflow/lib/forms.py:62` (`clean`), `src/crud_views_workflow/lib/views.py:85`
  (`cv_form_valid`).
- **What we did before #322:** `OrderWorkflowForm.clean()` added the reason to the `transition` field
  (`example/sales/forms.py`), and `example/sales/workflow.py:run_transition` mirrored the view for the seed data. Both
  are deleted now (see "Adopted here").
- **Suggested upstream change:** `clean()` returns `cleaned_data`; a `custom={"refuse": callable}` (or a model hook
  `workflow_check_transition(name) -> str | None`) shown as a form error; a public `run_transition(obj, name, user,
  comment)` used by the view itself.
- **Severity:** annoyance.

## Card views

### 8. The card template has no block above the title

- **Implemented upstream:** [issue #325](https://github.com/jacob-consulting/django-crud-views/issues/325)
  (closed 2026-11-06), [PR #330](https://github.com/jacob-consulting/django-crud-views/pull/330) (phase 06.14, merge
  `f693a38a`); not a claim about a published release. Empty `card_root` and `card_header` insertion blocks, shared with finding 9.
- **Adopted here:** the theme card (`src/crud_views_tabler/templates/crud_views/tags/card.html`) has the two new
  blocks in upstream's positions (`card_root` first in the root `.card`, `card_header` first in `.card-body`), and
  `example/catalog/templates/catalog/product_card.html` extends it: stripe in `card_root`, badge row in
  `card_header`, link in `card_title`, price footer ahead of `{{ block.super }}` in `card_actions`. One visible
  difference: the heading now takes the theme's `card:title` class (`card-title`, which Tabler gives a 1rem bottom
  margin), so the old `mb-1` is restored by an example CSS rule, `[data-product-card] ~ .card-body .card-title` in
  `example/static/acme/acme.css` (tested in `catalog.tests.ProductCardCssTests`). Theme tests: `CardThemeTests` (blocks empty by default, filled in place).

- **What happened:** the product card (type badge row above the title, a `card-status-top` stripe as a direct child of
  `.card`) cannot be built by extending `crud_views/tags/card.html`: `card_content` renders below the title, and
  nothing sits at the card root. The `card:root` / `card:body` class keys exist, but they are global, and putting the
  badge row into `card_title` would nest block elements in the heading.
- **Where:** `src/crud_views/templates/crud_views/tags/card.html:4-8` (class keys `card:root`, `card:body`, blocks
  `card_title`, `card_content`, `card_actions`); `docs/reference/card-list-view.md:158` ("Custom Card Template").
- **What we did before #325:** `example/catalog/templates/catalog/product_card.html` replaced the card and rendered the actions
  itself with `{% cv_card_action_group %}` and the `button/container.html` include, as the theme's card does.
- **Suggested upstream change:** a `card_header` block before the title and a `card_root` block (first child of the
  root element), so projects extend the card instead of copying its action plumbing.
- **Severity:** annoyance.

### 9. A card list as the landing page needs `cv_key = "list"`

- **Implemented upstream:** [issue #325](https://github.com/jacob-consulting/django-crud-views/issues/325)
  (closed 2026-11-06), [PR #330](https://github.com/jacob-consulting/django-crud-views/pull/330) (phase 06.14, merge
  `f693a38a`); not a claim about a published release. The existing cards-first, table-secondary configuration is documented and tested, with no `cv_default_list` API; shared with finding 8.
- **Adopted here:** the recipe is upstream's documented one (`docs/reference/card-list-view.md`), so the overrides
  stay as they are; `ProductCardListView` and `ProductTableListView` in `example/catalog/views.py` now point to it
  in comments.

- **What happened:** `CardListView` is `cv_key = "card"`, `cv_path = "card"`; "home", the cancel/success keys and the
  breadcrumbs all point at `list`. A ViewSet whose default list is the cards (with a table beside it) has to set
  `cv_key = "list"`, `cv_path = ""` on the card view, give the table view another key, and set
  `cv_home_key = "list"` on it. There is no semantic icon for a second list view either, so the table view uses
  `cv_icon_action = "tabler:table"`.
- **Where:** `src/crud_views/lib/views/card.py:22-23`, `src/crud_views/lib/view/base.py:104` (`cv_home_key`).
- **What we did before #325:** the overrides above (`example/catalog/views.py`); they work, and they are still what
  upstream's recipe prescribes.
- **Suggested upstream change:** a documented recipe for "two list views on one ViewSet" (or a `cv_default_list`).
- **Severity:** cosmetic.

## Polymorphic

### 10. Polymorphic create-select shows lower-case type names

- **Resolved:** [upstream issue #326](https://github.com/jacob-consulting/django-crud-views/issues/326),
  verified against phase 06.15 source on 2026-11-06; not a claim about a published release.
- **What happened:** the Type choices used lower-case `ContentType.name`; the consumer rewrote every label.
- **Upstream change:** `capfirst(ct.name)` changes only the first character and preserves the content-type IDs.
- **Adopted here:** removed `ProductContentTypeForm.__init__`; the subclass, `Continue` submit label and
  `Row(Column4("polymorphic_ctype_id"))` remain. The real selector test checks exact IDs/labels and presentation.
- **Verification:** the source-bound catalog suite passed all 18 tests in 5.742s on Python 3.14.7 / Django 6.1.2;
  `check --fail-level WARNING` reported no issues (0 silenced). See finding 11 for source provenance.
- **Severity:** cosmetic (resolved in the verified source).

### 11. A polymorphic detail view cannot give each kind its own property groups

- **Resolved:** [upstream issue #326](https://github.com/jacob-consulting/django-crud-views/issues/326),
  verified against phase 06.15 source on 2026-11-06; not a claim about a published release.
- **What happened:** a dummy Beans list satisfied the static check while `property_display` chose by runtime type.
- **Adopted here:** `ProductDetailView.cv_property_display = PROPERTY_DISPLAY`; removed the override and dummy list.
  Existing Coffee/Equipment/Subscription, Commerce/About groups, stock rules, breadcrumbs and view composition remain.
- **Verification:** 18 catalog tests passed in 5.742s, including sequential Beans/Equipment/Subscription/Beans
  details with actual values and sibling-field absence, stock visibility, all typed forms, permission denials,
  and checks of the real mapping plus invalid non-first Equipment/Subscription values/properties and restoration.
  `check --fail-level WARNING` passed with no issues (0 silenced). The tracer passed twice (1.037s and 0.932s).
- **Provenance:** the execution-only `/tmp/dcv-phase0615-verification/run_catalog.py` validates explicit roots,
  all five package import paths and required test IDs in the same process as each Django command. Core,
  object-detail and polymorphic imports came from `/home/alex/projects/workspaces/cv-phase-06-15/django-crud-views/src`
  at upstream `1d7a0c90e7b1f3c5f8ede748b41464bca05e4290`. Both configured widgets came from a clean detached
  checkout of `https://github.com/jacob-consulting/django-crud-views-extensions.git` at
  `0d84859a08b8bc706a877ce25c89da81d1321bfa`, project version 0.3.2. This is the historical report revision,
  not a Git revision from the editable-path lockfile. No dependency/settings/demo-data edits or installations.
  Commands: launcher modes `catalog` (`test catalog`) and `check` (`check --fail-level WARNING`), with explicit
  phase, extension and consumer roots; logs are retained beside the launcher. Upstream plan 03 separately passed
  10,175 tests on Django 5.2 (one Django-6-only skip), 471 focused tests each on Django 4.2/6.0, and strict docs build.
- **Severity:** annoyance (resolved in the verified source).

## Object detail

### 12. Object detail prints the stored value of a field with `choices`

- **Implemented upstream:** [issue #327](https://github.com/jacob-consulting/django-crud-views/issues/327)
  (closed 2026-11-07), [PR #333](https://github.com/jacob-consulting/django-crud-views/pull/333) (phase 06.16, merge
  `8df4917e`); not a claim about a published release. `PropertyConfig.choices_display` (default `True`)
  renders the choice label for scalar and single-object FK/O2O paths, keeps the automatic title, and passes the
  stored code to badge colour/label maps; `x("process", choices_display=False)` restores the raw value.
- **Adopted here:** `process`, `roast_level`, `interval`, `bag_size` (`example/catalog/views.py`), the green lot's
  `process` (`example/roastery/views.py`) and the customer's `payment_terms` are plain field names; the
  hand-written titles are gone (the field names give the same titles). `test_detail_shows_choice_labels_and_no_model_help_text`
  checks "Net 60" (not `net_60`) under "Payment terms"; the catalog tests still find the process label.
- **What happened:** `"process"` renders `washed`, not `Washed`; the resolver does not use `get_FOO_display`. Showing
  the label needs `x("get_process_display", title=...)` per choice field, plus a hand-written title.
- **Where:** `src/crud_views_object_detail/lib/resolvers.py:171` (`resolve_property`).
- **What we did before #327:** every such property points at `get_<field>_display` with an explicit title.
- **Suggested upstream change:** when the model field has `choices`, resolve to the display value by default.
- **Verification:** against the `../django-crud-views` checkout at `33bcaf44` (phase 06.17 branch, which contains
  the #333 merge): 197 example tests, 79 theme tests, 34 crispy_tabler tests and `check --fail-level WARNING` pass.
- **Severity:** annoyance (resolved in the upstream source).

### 13. Object detail shows model `help_text` in the value column

- **Implemented upstream:** [issue #327](https://github.com/jacob-consulting/django-crud-views/issues/327)
  (closed 2026-11-07), [PR #333](https://github.com/jacob-consulting/django-crud-views/pull/333) (phase 06.16, merge
  `8df4917e`); not a claim about a published release. Model help text is hidden by default; precedence is
  property `detail` → view `cv_object_detail_show_help_text` → setting `CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT`
  → `False`.
- **Adopted here:** "ISO country code, e.g. DE." is back on `Customer.country` and `Address.country`
  (migration `sales/0005_country_help_text`); the two form `__init__` overrides that set it are gone. The demo keeps
  the default (no `CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT`); the customer test checks the text is on the edit form
  and not on the detail page.
- **What happened:** a field's `help_text` (e.g. "ISO country code, e.g. DE.") is printed under its value on the
  detail page, where it reads as noise.
- **Where:** `src/crud_views_object_detail/lib/resolvers.py:155-157`.
- **What we did before #327:** moved the help text from the model to the form field (`example/sales/forms.py`).
- **Suggested upstream change:** an option to omit help text on detail pages (or omit it by default).
- **Severity:** cosmetic (resolved in the upstream source).

### 14. Object detail renders a blank text field as an empty row

- **Implemented upstream:** [issue #327](https://github.com/jacob-consulting/django-crud-views/issues/327)
  (closed 2026-11-07), [PR #333](https://github.com/jacob-consulting/django-crud-views/pull/333) (phase 06.16, merge
  `8df4917e`); not a claim about a published release. The stock `char`, `text` and `default` value
  templates show the muted em dash for `""` as for `None` (rows are kept; `0`/`False` stay values). No hide-empty
  option was added.
- **Adopted here:** `CustomerDetailView.property_display` no longer drops blank `phone`, `notes`, `company` and
  `vat_id`; it only picks the wholesale or consumer groups, and a blank field shows the dash.
  `test_detail_shows_a_dash_for_blank_optional_rows` checks the dash sits in the Phone and Notes value cells.
- **What happened:** the text type shows a dash only for `None`. A blank `CharField`/`TextField` (`""`, Django's
  convention for an empty string field) renders as a label with nothing beside it; a customer without phone or
  notes showed two empty rows.
- **Where:** `src/crud_views_object_detail/templates/crud_views_object_detail/types/default/text.html:1`
  (`{% if value is None %}`).
- **What we did before #327:** `CustomerDetailView.property_display` leaves `phone`, `notes`, `company` and `vat_id` out when
  they are blank (`example/sales/views/customers.py`).
- **Suggested upstream change:** treat `""` like `None` in the text type, or a per-property / setting "hide empty".
- **Severity:** cosmetic (resolved in the upstream source).

### 15. The accordion detail pack opens every panel closed

- **Implemented upstream:** [issue #328](https://github.com/jacob-consulting/django-crud-views/issues/328)
  (closed 2026-11-07), [PR #335](https://github.com/jacob-consulting/django-crud-views/pull/335) (phase 06.17, merge
  `be449c57`); not a claim about a published release. The accordion pack opens the first group initially; users can still close it. Shared with finding 17.
- **Adopted here:** `LotDetailView` (`example/roastery/views.py`) uses `cv_object_detail_layout = "accordion"`; its
  first group, "Origin and producer", opens initially. `test_detail_is_an_accordion_with_the_first_group_open` pins it.
- **Note:** upstream's count badge on each accordion header is the solid `text-bg-secondary`, not the theme's light
  badges. Left as is; no theme CSS added.

- **What happened:** with `cv_object_detail_layout = "accordion"` a detail page shows only the group titles and an
  "N properties" badge until each panel is clicked; the docs say "Accordions remain initially collapsed; the tab
  `selected` flag does not open them". For a page whose point is its facts that reads as an empty page.
- **Where:** `src/crud_views_object_detail/templates/crud_views_object_detail/layouts/accordion/group.html:5`
  (`accordion-button collapsed`), `docs/reference/object_detail_layout_packs.md:130`.
- **What we did before #328:** the green lot detail used `card-rows` instead (products use the project default `tabs-vertical`,
  customers `split-card`).
- **Suggested upstream change:** open the group flagged `selected` (or the first one), like the tab packs.
- **Severity:** annoyance.

### 16. `ObjectDetailMixin` plus `ObjectDetailViewPermissionRequired` is an MRO error

- **Implemented upstream:** [issue #327](https://github.com/jacob-consulting/django-crud-views/issues/327)
  (closed 2026-11-07), [PR #333](https://github.com/jacob-consulting/django-crud-views/pull/333) (phase 06.16, merge
  `8df4917e`); not a claim about a published release. Documentation only, as suggested: the object detail
  docs warn that `ObjectDetailView`/`ObjectDetailViewPermissionRequired` already include `ObjectDetailMixin`. No
  class hierarchy change; nothing to adopt here.

- **What happened:** a detail view declared `(BreadcrumbMixin, ObjectDetailMixin, ObjectDetailViewPermissionRequired)`
  raises "Cannot create a consistent method resolution order": the permission-required class already includes the
  mixin, while the plain `DetailViewPermissionRequired` needs it added (the catalog's product detail does).
- **Where:** `src/crud_views_object_detail/lib/views.py:10` (`ObjectDetailViewPermissionRequired` bases).
- **What we did:** use the permission-required class alone.
- **Suggested upstream change:** state this in the object detail docs next to the mixin recipe.
- **Severity:** cosmetic.

### 17. `tabs.js` looks up `globalThis.bootstrap` directly

- **Implemented upstream:** [issue #328](https://github.com/jacob-consulting/django-crud-views/issues/328)
  (closed 2026-11-07), [PR #335](https://github.com/jacob-consulting/django-crud-views/pull/335) (phase 06.17, merge
  `be449c57`); not a claim about a published release. Object-detail tabs initialise through the theme adapters (`cv.adapters`) instead of `globalThis.bootstrap`. Shared with finding 15.
- **Adopted here:** no theme code needed: upstream's `cv.bootstrapAdapters` now includes `tab`, and
  `tabler-adapters.js` assigns the whole set (`Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler))`).
  `test_upstream_adapter_set_includes_tab_and_theme_takes_all_of_it` pins both halves. Not checked in a browser.

- **What happened:** the object-detail tab initialiser calls `globalThis.bootstrap?.Tab`, bypassing `cv.adapters`.
  Tabler exposes Bootstrap only as `window.tabler`, so the init silently does nothing. The tabs still switch
  (Bootstrap's data API in Tabler's bundle handles `data-bs-toggle="pill"`), but the keyboard handling the init is
  for is lost.
- **Where:** `src/crud_views_object_detail/static/crud_views_object_detail/js/tabs.js:29`, `:41`.
- **What we did before #328:** nothing; not worth a theme shim.
- **Suggested upstream change:** resolve `Tab` through an adapter like modal/tooltip/collapse.
- **Severity:** annoyance.

### 18. The header icon is drawn beside a custom header template

- **Upstream tracking:** [django-crud-views #329](https://github.com/jacob-consulting/django-crud-views/issues/329) —
  resolved by [PR #345](https://github.com/jacob-consulting/django-crud-views/pull/345), squash-merged as
  `fe21953e` on 2026-11-10; adopted here.
- **What happened:** `cv_header_template` replaces only the heading text; the ViewSet's header icon was still drawn
  before it, so the customer page showed the shop icon and then the customer's avatar. Previously an empty string
  fell back to the ViewSet icon, requiring a `cv_get_header_icon()` override returning `None`.
- **Where:** upstream `CrudView.cv_get_header_icon()` in `src/crud_views/lib/view/base.py`; the theme renders it in
  the `page_title` block of `src/crud_views_tabler/templates/crud_views_tabler/page.html`.
- **What we did:** import `Icon` from `crud_views.lib.icons` and set `CustomerDetailView.cv_icon_header = Icon.NONE`
  in `example/sales/views/customers.py`; remove the getter workaround. The existing customer-header regression
  verifies that the avatar remains and the inherited SVG is absent. No theme template override is needed.
- **Upstream contract:** `Icon.NONE` (empty string) suppresses; omitted values, `None` and `Icon.VIEWSET_DEFAULT`
  inherit. Custom header content and dynamic getter overrides remain independent. Other empty-string declarations
  that need inheritance must migrate to `None` or `Icon.VIEWSET_DEFAULT`.
- **Validation:** all 26 customer tests pass with four workers; `manage.py check --fail-level WARNING` is clean.
- **Severity:** cosmetic (resolved).

## Conditional groups and formsets

### 19. Conditional groups only toggle on a boolean checkbox

- **What happened:** `ConditionalGroup` takes a `ToggleSource` that reads a boolean (`ModelFieldToggle` /
  `UIFieldToggle`), and `toggle.js` binds to a *checkbox*. The roastery's `Customer.kind` is a two-value choice
  (wholesale / consumer), so it cannot drive the group. The group also refuses fields whose form field is not a plain
  text/number pair (a `TypedChoiceField` such as `price_tier`) until `empty_values` is given explicitly.
- **Where:** `src/crud_views/lib/conditional/toggle.py:24` (`ToggleSource.is_on`),
  `src/crud_views/lib/conditional/group.py:13` (`resolve_conditional_empty_value`),
  `src/crud_views/static/crud_views/js/toggle.js:23` (`findCheckboxes`).
- **What we did:** the customer form declares a transient `is_wholesale` checkbox (`UIFieldToggle`), derives
  `Customer.kind` from it in `clean()`, seeds it from the stored kind when editing, and passes `empty_values` for the
  choice fields (`example/sales/forms.py`).
- **Suggested upstream change:** a toggle source that compares a field to a value (`ValueToggle("kind", "wholesale")`),
  with the JS reading a select/radio, and choice fields supported by the empty-value resolver.
- **Severity:** annoyance.

### 20. Formsets have no per-row conditional fields

- **What happened:** an order line's grind and bag size only apply when the row's product is coffee. Conditional
  groups toggle on a checkbox of the main form, and `ConditionalFormSet` switches a whole first-level formset; neither
  can follow a select inside each formset row.
- **Where:** `src/crud_views/lib/conditional/group.py:80` (`ConditionalGroup`),
  `src/crud_views/lib/conditional/formset.py:10` (`ConditionalFormSet`).
- **What we did:** `OrderLineForm.clean()` and `OrderLine.save()` clear the two fields for non-coffee products;
  `ProductSelect` marks coffee options `data-beans` and `example/sales/static/sales/sales.js` disables the two
  selects in that row (progressive enhancement, registered with `register_assets`).
- **Suggested upstream change:** a row-scoped toggle (a `ValueToggle` on a field of the same form, see #19) that
  `formset.js` re-binds for added rows.
- **Severity:** annoyance.

### 21. Toggle groups and formsets render a bare `<legend>`

- **What happened:** `ToggleGroup(legend=...)` and the formset title render a bare `<fieldset><legend>`, which
  browsers and Bootstrap size like a heading (about 1.5rem, floated), larger than the page's card titles.
- **Where:** `src/crud_views/templates/crud_views/conditional/toggle_group.html:6`,
  `src/crud_views/templates/crud_views/formsets/formset.html:18`.
- **What we did:** theme CSS (`crud_views_tabler.css`): `.cv-toggle-group > legend, .cv-formset-fieldset > legend` are
  not floated, 1rem, bold.
- **Suggested upstream change:** a class key on each legend (`conditional:legend`, `formset:legend`).
- **Severity:** cosmetic.

### 22. A compact, table-like formset repeats its labels on every row

- **Status: DONE upstream** — [#347](https://github.com/jacob-consulting/django-crud-views/issues/347)
  closed by [PR #348](https://github.com/jacob-consulting/django-crud-views/pull/348), squash merge
  `99fd01e5` on 2026-11-11 (phase 06.24). Public `CompactLayout` / `CompactColumn` declarations opt each
  `FormSet` into shared desktop headings and labelled mobile cards, with independent nested layouts and
  classic/compact mixtures. The formset reference documents adoption and supported widget boundaries;
  automated checks and human grouping/focus UAT passed. **Downstream adoption remains follow-up:** the
  Tabler theme and cupping-score declarations have not been changed by this tracker update.

- **What happened:** the cupping scores are one row per taster with seven narrow number columns.
  `FormSet(form_show_labels=...)` is all or nothing, so either every row carries its labels (what the demo does,
  about twice the height of a table) or none does and the columns have no header.
- **Where:** `src/crud_views/lib/formsets/formsets.py:64` (`form_show_labels`),
  `src/crud_views/lib/formsets/inline_formset.py:56` (`get_helper`, one helper for every form).
- **What we did:** `form_show_labels=True`, and `CuppingScoreForm` gives the inputs `form-control-sm`.
- **Suggested upstream change:** labels on the first row only (or a header row above the formset) as an option.
- **Related follow-up:** the order-line formset cannot adopt compact mode while its `ProductSelect` subclass supplies
  per-option `data-beans` attributes for the grind/bag-size script; see [finding 34](#34-compact-formsets-reject-custom-select-subclasses).
- **Severity:** cosmetic.

## Permissions (Guardian, custom forms, manage)

### 23. Child viewsets under a Guardian parent need their own gate; no page tabs for children

- **Partly implemented upstream:** [PR #336](https://github.com/jacob-consulting/django-crud-views/pull/336) (phase 06.18, merge
  `fe9d5d2e`, merged 2026-11-09; no linked issue). Ancestor authorization: every nested request
  resolves the ancestors in its URL and checks their permissions before the endpoint's own work, so "a plain child
  view without a permission of its own is still protected by its ancestors" (`docs/reference/nested.md`). A child
  view under a Guardian parent needs the parent's `view` (read) or `change` (write) object grant, which is the
  suggested "inherit the parent's grants" mode. `GuardianParentPermissionMixin` still exists, but the
  `cv_guardian_parent_*` fields and `_guardian_child_composition_error` are gone (breaking change, see
  `docs/migrating-1.0.md`). **Not addressed:** the tab/nav rendering of child viewsets on the parent detail page
  (`ChildContextButton` is still the only way).
- **Adopted here:** the parent gate is upstream's ancestor guard; `CustomerGrantMixin` is removed from every
  nested sales view. The customer viewset declares `AncestorPolicy(accept_global_perms=True)`
  (`example/sales/views/customers.py`), so Owner and Roasters pass the gate with their model permissions. The
  default Read and Write pairs cover the built-in views; three custom endpoints fell outside those families and
  made `manage.py check` fail with `viewset.E268`, so each has an action pair: `address` `make_default`
  (`nearest="change"`, `higher="view"`), `order` `duplicate` (`change`/`view`) and `order` `workflow`
  (`view`/`view`). `sales/tests/test_access.py` (`AccessMatrixTests`) pins the nested access per role and passed
  unchanged after the removal. Child tabs are still open: Orders, Subscriptions and Addresses remain context
  buttons on the customer page.

- **What happened:** `GuardianParentPermissionMixin` requires the child views to carry per-object Guardian grants on
  the child rows too, so a child with a plain `ViewSet` (addresses) is not covered by the parent's grants. Also, the
  mockup's tabs (Orders / Addresses / Subscriptions) on the parent detail have no equivalent: `ChildContextButton`
  gives buttons linking to the nested lists.
- **Where:** `src/crud_views_guardian/lib/mixins.py:280` (`_guardian_child_composition_error`),
  `docs/reference/context_buttons.md:156` (`ChildContextButton`).
- **What we did before #336:** a 10-line `CustomerGrantMixin` that checks the URL's customer (view to read, change to write;
  `example/sales/views/addresses.py`); Orders, Subscriptions and Addresses are context buttons on the customer page.
- **Suggested upstream change:** a parent-only mode for Guardian child views (inherit the parent's grants), and a
  tab/nav rendering of child viewsets on the parent detail page.
- **Severity:** annoyance.

### 24. A no-object custom form needs an undocumented recipe for its own permission

- **DONE** upstream: [#341](https://github.com/jacob-consulting/django-crud-views/issues/341) closed on
  2026-11-10 after [PR #343](https://github.com/jacob-consulting/django-crud-views/pull/343) was squash-merged
  (`7466b3d5`, Phase 06.22). The custom form reference now documents and tests the `Meta.permissions` plus
  `cv_permission` recipe. Database-free `viewset.E269` checks undeclared core view keys and effective ancestor
  permission pairs after URL registration completes. It uses concrete-model metadata; migrations and user grants
  remain application responsibilities. Guardian/Resource ViewSets are excluded, and request-time backstops remain.

- **Original finding:** "Run subscriptions" is not a CRUD action, and only the Owner may run it.
  `permission_required` looks `cv_permission` up in `ViewSet.permissions`, which is built from the model's
  `Permission` rows by stripping `_<model>` from each codename. The working recipe is a `Meta.permissions` entry
  `run_customersubscription` on the model plus `cv_permission = "run"` on the view; at the time, nothing in the docs or
  the `custom_form` example explained it (the examples reused `view`). An undeclared `cv_permission` failed at request
  time with an assert rather than being reported by a startup check.
- **Where:** `src/crud_views/lib/view/base.py:1062` (`permission_required`),
  `src/crud_views/lib/viewset/__init__.py:437` (`default_permissions`),
  `src/crud_views/lib/views/form.py:72` (`CustomFormNoObjectViewPermissionRequired`).
- **What we did:** the model permission above; the button shows disabled (`cv_inaccessible_actions = "disable"`) and
  the URL answers 403 for everyone else.
- **Upstream change:** complete; the recipe is at
  [A permission of its own](https://github.com/jacob-consulting/django-crud-views/blob/main/docs/reference/custom_form_view.md#a-permission-of-its-own),
  with executable documentation coverage and startup diagnostics for core model permission declarations.
- **Adopted here (2026-11-10):** the subscription module now references the upstream recipe alongside its existing
  model permission and view key. The demo passes `check --fail-level WARNING`; existing request-level tests verify
  Owner access and denial for Sam and Kim. The startup check validates declarations rather than database permission
  rows or grants, so those access tests remain necessary. No permission behavior changed.
- **Severity:** annoyance.

### 25. Manage pages are open to every signed-in user while DEBUG is on

- **Checked against #336, not addressed:** `CRUD_VIEWS_MANAGE_VIEWS_ENABLED` still defaults to `"debug_only"`, and
  `ManageView._cv_manage_public()` still admits everybody while `DEBUG` is on (`src/crud_views/lib/views/manage.py`).
  The PR only adds the ancestor guard for nested manage pages and shows the ancestor policy on them.

- **What happened:** `CRUD_VIEWS_MANAGE_VIEWS_ENABLED` defaults to `"debug_only"`, which opens every manage page to
  any signed-in user while `DEBUG` is on, whatever their permissions. On a Guardian ViewSet that page lists every
  view's permissions and the groups holding them, so the account manager Sam could read the demo's whole permission
  set. The demo's `DEBUG` defaults to on and the demo is served publicly. The manage tables also have no
  `.table-responsive` wrapper; at 390 px they push the page to about 610 px.
- **Where:** `src/crud_views/lib/settings.py:27` (default), `src/crud_views/lib/views/manage.py:35`
  (`has_permission`); `src/crud_views/lib/viewset/__init__.py:323` adds the "manage" context action.
- **What we did:** `CRUD_VIEWS_MANAGE_VIEWS_ENABLED = os.environ.get('CRUD_VIEWS_MANAGE_VIEWS_ENABLED', 'no')` in
  `example/config/settings.py` (tested in `example/dashboard/tests.py`). The manage URLs stay registered and answer
  403 (`ManageView.has_permission`), even for a superuser, and the toolbar has no manage button unless the
  environment opts in. No CSS for the tables, since the pages are off.
- **Suggested upstream change:** keep `debug_only` but also require staff (or the manage group) in it, or document
  the exposure next to the setting; wrap the manage tables in `.table-responsive`.
- **Severity:** annoyance.

## Tables and ViewSets

### 26. `Table` forces `sequence` and always adds the actions column

- **Implemented upstream:** [issue #337](https://github.com/jacob-consulting/django-crud-views/issues/337)
  (closed 2026-11-09), [PR #340](https://github.com/jacob-consulting/django-crud-views/pull/340) (phase 06.19, merge
  `910d8bb9`); not a claim about a published release. `Table.__init__` applies its default `("...", "actions")` only
  when the table declares no `Meta.sequence`; a declared one is used as written. Upstream re-scoped the second half of
  the ask: the column is not dropped automatically when the view has no list actions. The documented way to drop it is
  the table's own `Meta.exclude = ("actions",)` (`docs/reference/list_view.md`, `docs/faq.md`), which is what the demo
  already did; `actions = None` on a subclass is unsupported and raises `KeyError`. A `Meta.sequence` that leaves out
  `actions` places it at the `"..."` position, so list it explicitly where it must come last.
- **Adopted here:** `OrderTable`, `AllOrdersTable`, `SubscriptionTable` and `AllSubscriptionsTable` declare
  `Meta.sequence`; the `column_sequence` attribute and the `__init__` overrides in `OrderTableBase` and
  `SubscriptionTableBase` are removed (`example/sales/views/orders.py`, `example/sales/views/subscriptions.py`). The
  column order of all four tables is unchanged.
- **Verification:** against the `../django-crud-views` checkout at `910d8bb9` (`main`, the #340 merge): 209 example
  tests and `check --fail-level WARNING` pass.
- **What happened:** `crud_views.lib.table.Table.__init__` passes `sequence=("...", "actions")` unless the caller
  does, which beats a subclass's `Meta.sequence`, so inherited columns come first. A list with `cv_list_actions = []`
  still renders an empty "Actions" column.
- **Where:** `src/crud_views/lib/table/table.py:31-33`.
- **What we did before #337:** `OrderTableBase.__init__` passed the wanted sequence; the top-level table set
  `Meta.exclude = ("actions",)` (`example/sales/views/orders.py`).
- **Suggested upstream change:** honour `Meta.sequence` (append `actions` to it), and drop the column when the view has
  no list actions.
- **Severity:** annoyance (resolved in the upstream source).

### 27. A second, top-level ViewSet on a child model needs hand-made links

- **What happened:** orders live under the customer (`order`, the full editor) and in a top-level list (`orders`,
  list + create). The top-level ViewSet has no detail view, so `LinkDetailColumn` and row actions cannot point at the
  nested pages; the create view cannot redirect into the other ViewSet with a success key either.
- **Where:** `src/crud_views/lib/table/columns.py:53` (`LinkDetailColumn` uses the table's own ViewSet),
  `src/crud_views/lib/view/base.py:244` (`get_success_url`).
- **What we did:** `AllOrdersTable.render_number` reverses `order-detail`; `AllOrdersCreateView.get_success_url`
  reverses `order-update` (`example/sales/views/orders.py`).
- **Tracked upstream:** filed as [#311](https://github.com/jacob-consulting/django-crud-views/issues/311) (derive a
  missing parent pk from the object inside the existing URL builders). The maintainer closed it on 2026-11-04 in favour
  of [#314](https://github.com/jacob-consulting/django-crud-views/issues/314), an opt-in, request-free helper that
  builds a URL from a target ViewSet, a key and an object. #314 is open backlog work, not part of 1.0, and leaves the
  existing URL builders, columns, row actions and success redirects unchanged.
- **Suggested upstream change:** the #314 helper, nothing more. A `LinkColumn(viewset=..., key=...)` or a success
  target in another ViewSet is not asked for upstream: #314 rules out that kind of core integration. If wanted, such a
  column is a thin wrapper over the helper in the theme or the demo.
- **When #314 lands:** both call sites are its plain case (one level, ForeignKey `Order.customer`) and switch to the
  helper; they can serve as the downstream example its acceptance criteria ask for. The helper builds a route, not an
  access check; here they agree because `AllOrdersListView.get_queryset` already limits the rows to
  `customers_for(user)`.
- **Severity:** cosmetic.

### 28. Two ViewSets on one model share every default label

- **What happened:** the nested and top-level subscription lists both default to the header "Customer subscriptions"
  (from `CustomerSubscription._meta.verbose_name`), also in the breadcrumb; only the page header can be changed per
  view (`cv_header_template_code`), the breadcrumb and create/update headers keep the model name.
- **Where:** `src/crud_views/lib/viewset/__init__.py:478-487` (`get_meta`: `verbose_name` from the model's `_meta`).
- **Previous workaround:** `cv_header_template_code = "Subscriptions"` on the two lists; the breadcrumb kept the model name.
- **DONE** upstream: [#338](https://github.com/jacob-consulting/django-crud-views/issues/338) closed on
  2026-11-10 after [PR #342](https://github.com/jacob-consulting/django-crud-views/pull/342) was squash-merged
  (`59f85769`, Phase 06.20). Implemented `ViewSet(verbose_name=..., verbose_name_plural=...)` as two optional
  `LazyStr` fields that `get_meta()`
  resolves independently (singular and plural each fall back to the model), so every default snippet, the breadcrumb
  container item, `LinkChildColumn` and `ChildContextButton` follow; per-view template codes still win. Model-centric
  texts (delete summaries, 404s) stay on the model. The issue carries the decisions and acceptance criteria for the
  upstream phase.
- **Upstream change:** complete; the #338 fields, with default-label propagation and regression coverage.
- **Adopted here (2026-11-10):** `cv_subscription` and `cv_all_subscriptions` declare
  `verbose_name=_("subscription")`, `verbose_name_plural=_("subscriptions")`; the two list
  `cv_header_template_code` overrides are removed. Rendered-page tests cover "Subscriptions" in both list headings
  and breadcrumbs, "Subscription" in create/update/delete headings (including the delete modal), and preservation of
  the custom "Run subscriptions" heading. Model-centric delete text and custom success messages retain their wording.
- **Severity:** cosmetic.

### 29. Snippet templates only see the object, not the view

- **Status:** **DONE** upstream; [#339](https://github.com/jacob-consulting/django-crud-views/issues/339) closed on
  2026-11-10 at 10:36 UTC. Adopted in the demo on 2026-11-10 (below).
- **Original finding:** header, paragraph and message template codes rendered with a context that had `object` but not
  `view`, so "Created {{ view.duplicate }} from {{ object }}" or "a draft for {{ view.cv_get_parent_object }}" rendered
  empty.
- **Where:** `src/crud_views/lib/view/base.py:436` (`render_snippet` builds its context from the caller's dict at
  `:442`).
- **Previous workaround:** plainer texts omitted the new draft's identity and the nested create page's customer.
- **Tracked upstream:** filed as [#339](https://github.com/jacob-consulting/django-crud-views/issues/339) on
  2026-11-09: `cv_get_meta()` adds `view` (the instance) and, on child ViewSets, a lazy `parent_object` (absent on
  top-level ViewSets, reusing the parent the ancestor guard resolved, so no extra query) for the snippets a view renders
  for its own page: header, paragraph, filter header, success and error message. Class-level labels (action, short
  action, breadcrumb current-page label, buttons) intentionally omit `view` and `parent_object`: the hosting page's
  view is not the labelled view. The issue carries the decisions and acceptance criteria for the upstream phase.
- **Upstream change:** #339 is closed; the requested scope is the snippet context keys described above.
- **Adopted here (2026-11-10):** the duplicate action's message is "Created {{ view.duplicate }} from {{ object }}"
  and the nested order create heading is "New order for {{ parent_object }}" (`example/sales/views/order_actions.py`,
  `orders.py`). Rendered-output tests cover both order identities in the success message, its display after redirect,
  and the safely escaped customer heading on GET and invalid form redisplay. The top-level create heading stays
  "New order"; action and breadcrumb labels are unchanged.
- **Severity:** cosmetic.

## django-crud-views-extensions

### 30. ext: The datetimepicker assets load on every page and need jQuery

- **What happened:** with `crud_views_widget_datetimepicker` installed, `jquery.datetimepicker.full.min.js` and
  `init.js` load at the end of `<body>` on every crud_views page, including pages with no date field. The package
  expects the project to load jQuery first, but only a docstring says so. With no jQuery, every page logged
  `jQuery is not defined` and `$ is not defined`.
- **Where:** `ext:src/crud_views_widget_datetimepicker/assets.py:25` (the `source_files` docstring is the only
  mention of the requirement).
- **What we did:** `example/templates/django_tabler/includes/head.html` loads jQuery 3.7.1 (pinned, SRI,
  `crossorigin`) from code.jquery.com before the plugin. The sweep found no console errors on any page.
- **Suggested upstream change:** emit the picker assets only through the widget's `Media` on pages whose form uses a
  picker, and/or a system check or a docs section stating the jQuery requirement.
- **Severity:** annoyance.

### 31. ext: The typeahead skins read Bootstrap's `--bs-*` custom properties

- **What happened:** the select popup of `crud_views_widget_typeahead` uses `var(--bs-body-bg)`,
  `--bs-border-color-translucent`, `--bs-border-radius`, `--bs-secondary-color`, `--bs-highlight-bg`. Tabler names its
  properties `--tblr-*`, so the popup had no background or border and the form's buttons showed through the result
  list. Tabler's `.dropdown-item` is also a flex row with a gap, which split the `<mark>` highlight off the word.
- **Where:** `ext:src/crud_views_widget_typeahead/static/crud_views_widget_typeahead/typeahead-select.css:42`,
  `typeahead.css:26`, `:37`.
- **What we did:** theme CSS (`crud_views_tabler.css`): `.cv-typeahead, .cv-typeahead-select` define the `--bs-*`
  properties from Tabler's, plus a dropdown shadow and `display: block` for the items. No template override, and no
  import of the extensions package.
- **Suggested upstream change:** fall back in the CSS (`var(--bs-body-bg, var(--tblr-bg-surface, #fff))`) or expose
  `--cv-typeahead-*` properties a theme sets.
- **Severity:** annoyance (the popup is broken without the fix).

### 32. ext: The datetimepicker keeps its own look

- **What happened:** the xdsoft jQuery picker brings its own stylesheet (blue selection, its own font and shadow), so
  it does not follow Tabler's primary colour, radius or dark mode.
- **Where:** `ext:src/crud_views_widget_datetimepicker/assets.py` (the plugin's CDN stylesheet).
- **What we did:** nothing; theming a third-party widget's CSS is out of scope for the theme.
- **Suggested upstream change:** a documented set of CSS variables (or a small Bootstrap-variable bridge stylesheet)
  that themes can feed.
- **Severity:** cosmetic.

### 33. Workflow transition buttons ignore the transition's `variant` and `icon`

- **What happened:** with `cv_transition_presentation = "buttons"` every transition is rendered as the same
  `form:submit:label` button (`btn btn-primary` in the theme) with only its label. A transition's
  `custom["variant"]` (the order's Cancel is `danger`) and `custom["icon"]` are not read, so Cancel is a primary
  button without an icon next to Confirm.
- **Where:** `src/crud_views_workflow/templates/crud_views_workflow/widgets/transitions.html:8`
  (`{% cv_button_class 'form' 'submit' 'label' %}` for every action).
- **What we did:** nothing; the demo keeps `variant`/`icon` in the transition's `custom` for the order page's own
  buttons, and the workflow page shows uniform primary buttons.
- **Suggested upstream change:** honour `custom["variant"]` and `custom["icon"]` in the widget, or offer a
  per-transition class key (`workflow:transition-<name>`).
- **Severity:** cosmetic.

### 34. Compact formsets reject custom `Select` subclasses

- **Tracked upstream:** [issue #349](https://github.com/jacob-consulting/django-crud-views/issues/349) (open;
  follow-up to compact formsets #347 / PR #348). The request is for a narrow compatibility rule, not blanket support
  for arbitrary widget subclasses.
- **What happened:** order lines use `ProductSelect(forms.Select)` to add `data-beans="1"` to coffee options. The
  per-row `sales.js` handler reads that attribute to enable grind and bag-size fields only for coffee. Compact mode
  rejects the `product` field before crispy rendering because its widget class is a subclass, even though this
  subclass calls `super().create_option()` and keeps the stock select and option templates.
- **Where:** `src/crud_views/lib/formsets/compact.py` (`_compact_schema` requires exact stock widget classes);
  `example/sales/forms.py` (`ProductSelect` and `ORDER_FORMSETS`), `example/sales/static/sales/sales.js`.
- **What we do:** keep the order-line formset classic, with its working product option metadata and row behavior.
  Cupping scores can adopt compact mode independently because their widgets are supported stock classes (#22).
- **Upstream ask:** allow an explicitly compatible single-select subclass to retain ordinary compact headings,
  associated labels, mobile cards, errors, row controls and option attributes. Keep custom templates, multiple
  selection and changed markup outside the supported boundary unless independently validated. The issue leaves
  the precise opt-in contract to upstream.
- **Severity:** cosmetic.

---

## Not shown in the demo

Features from the spec's feature map that were dropped or reduced, with the reason.

- **Object-detail packs:** the demo shows `split-card` (customers), `accordion` (green lots, first group open, #15)
  and the project default `tabs-vertical` (products and the rest). `card-rows` is not used.
- **`ConditionalFormSet`:** not used. The spec's "grind/bag size only for beans" needs a per-row toggle, which
  upstream does not have (#20); the demo clears the fields in `clean()`/`save()` and disables them with a small script.
  No other formset in the domain switches as a whole.
- **Tabs for a customer's orders, addresses and subscriptions** (mockup): context buttons to the nested lists instead
  (#23).
- **Typeahead product picker in order lines:** a plain select with `data-beans` options; the typeahead is the
  customer picker on the top-level order create. Per-row typeahead plus the per-row disable script was not worth it
  for ~30 products.
- **"Restock" action view:** only "Mark default address" shows an `ActionView`; a restock button would duplicate it.
- **Category-driven sidebar:** categories (ordered, up/down) drive the product filter, not the sidebar.
- **Guardian manage page:** off by default (`CRUD_VIEWS_MANAGE_VIEWS_ENABLED = "no"`, #25). Set the environment
  variable `CRUD_VIEWS_MANAGE_VIEWS_ENABLED=debug_only` locally to see it.
- **Upstream's tooltip-per-location recipe:** shown only as the theme's own wrapper (#2).

## Known rough edges

Left as they are, each more than a quick fix or outside this repo:

- The cupping score formset repeats its labels on every row (#22).
- The workflow page has no card frame, and the datetimepicker keeps its blue look (#5, #32).
- *django_tabler gap, not crud_views:* Tabler's primary-colour themes (`data-bs-theme-primary`,
  `?theme-primary=green`) need Tabler's separate `tabler-themes.min.css`, which `django_tabler` does not load. With such a choice stored the brand's sienna steps
  aside (`acme.css` applies only to `:root:not([data-bs-theme-primary])`) and Tabler's base blue shows. Picking
  "blue" is Tabler's default and is not stored, so sienna stays. The layout switch offers no colour choice, so this
  only shows when the URL parameter is used.
- Sam (roastery view permission) sees the order numbers of customers he has no grant for on a roast batch's detail;
  the order links answer 403 for him. Accepted: the roastery is shared production data.
