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
[#327](https://github.com/jacob-consulting/django-crud-views/issues/327). The remaining findings are candidates to
triage into issues for django-crud-views (and, where marked, django-crud-views-extensions).

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
| 4 | [Workflow badge is a solid Bootstrap pill](#4-workflow-badgeenum-values-are-bootstrap-colour-names-the-badge-is-a-solid-pill) | annoyance | theme template override `crud_views_workflow/badge.html` |
| 5 | [Workflow page has no card frame, history table not responsive](#5-the-workflow-page-is-not-framed-and-its-history-table-is-not-responsive) | cosmetic | theme CSS lets the content scroll sideways around a bare table on phones; no frame |
| 6 | [One permission gates every workflow transition](#6-workflowviewpermissionrequired-has-one-permission-for-every-transition) | annoyance | `cv_permission = "view"` plus django-fsm `permission=` per step |
| 7 | [No refusal message, `WorkflowForm.clean()` returns None, no transition helper](#7-workflow-no-refusal-with-message-hook-workflowformclean-returns-none-no-helper-outside-the-view) | annoyance | form subclass; `sales/workflow.py:run_transition` copies the view |
| 8 | [Card template has no block above the title](#8-the-card-template-has-no-block-above-the-title) | annoyance | demo replaces the product card template outright |
| 9 | [Card list as landing page needs `cv_key = "list"`](#9-a-card-list-as-the-landing-page-needs-cv_key--list) | cosmetic | overrides `cv_key`/`cv_path`/`cv_home_key` on both list views |
| 10 | [Polymorphic create-select shows lower-case type names](#10-polymorphic-create-select-shows-lower-case-type-names) | cosmetic | resolved #326: upstream labels; Continue/layout retained |
| 11 | [Polymorphic detail cannot vary property groups per kind](#11-a-polymorphic-detail-view-cannot-give-each-kind-its-own-property-groups) | annoyance | resolved #326: direct model mapping; catalog/check verified |
| 12 | [Object detail prints stored value of a `choices` field](#12-object-detail-prints-the-stored-value-of-a-field-with-choices) | annoyance | resolved #327: plain field names show the choice label |
| 13 | [Object detail shows model `help_text` under values](#13-object-detail-shows-model-help_text-in-the-value-column) | cosmetic | resolved #327: help text back on the model, hidden on detail pages |
| 14 | [Object detail renders a blank text field as an empty row](#14-object-detail-renders-a-blank-text-field-as-an-empty-row) | cosmetic | resolved #327: blank fields keep their row and show a dash |
| 15 | [Accordion pack opens every panel closed](#15-the-accordion-detail-pack-opens-every-panel-closed) | annoyance | accordion pack not used; card-rows, tabs, split-card instead |
| 16 | [`ObjectDetailMixin` + `ObjectDetailViewPermissionRequired` is an MRO error](#16-objectdetailmixin-plus-objectdetailviewpermissionrequired-is-an-mro-error) | cosmetic | documented upstream #327; permission-required class alone |
| 17 | [`tabs.js` reads `globalThis.bootstrap`](#17-tabsjs-looks-up-globalthisbootstrap-directly) | annoyance | nothing (Bootstrap's data API still switches tabs) |
| 18 | [Header icon is drawn beside a custom header template](#18-the-header-icon-is-drawn-beside-a-custom-header-template) | cosmetic | customer detail overrides `cv_get_header_icon()` to return None |
| 19 | [Conditional groups toggle only on a checkbox](#19-conditional-groups-only-toggle-on-a-boolean-checkbox) | annoyance | transient `is_wholesale` checkbox drives `Customer.kind` |
| 20 | [No per-row conditional fields in formsets](#20-formsets-have-no-per-row-conditional-fields) | annoyance | `clean()`/`save()` clear the fields; `sales.js` disables them per row |
| 21 | [Bare `<legend>` in toggle groups and formsets](#21-toggle-groups-and-formsets-render-a-bare-legend) | cosmetic | theme CSS sizes `.cv-toggle-group > legend`, `.cv-formset-fieldset > legend` |
| 22 | [Compact formset repeats labels on every row](#22-a-compact-table-like-formset-repeats-its-labels-on-every-row) | cosmetic | labels on every row, `form-control-sm` inputs |
| 23 | [Guardian child views need their own gate; no child tabs](#23-child-viewsets-under-a-guardian-parent-need-their-own-gate-no-page-tabs-for-children) | annoyance | `CustomerGrantMixin` on addresses; context buttons instead of tabs |
| 24 | [Custom no-object permission needs an undocumented recipe](#24-a-no-object-custom-form-needs-an-undocumented-recipe-for-its-own-permission) | annoyance | `Meta.permissions` entry + `cv_permission = "run"` |
| 25 | [Manage pages are open to every user under DEBUG](#25-manage-pages-are-open-to-every-signed-in-user-while-debug-is-on) | annoyance | `CRUD_VIEWS_MANAGE_VIEWS_ENABLED = "no"` by default in the demo |
| 26 | [`Table` forces `sequence` and always adds the actions column](#26-table-forces-sequence-and-always-adds-the-actions-column) | annoyance | table `__init__` passes the sequence; `Meta.exclude = ("actions",)` |
| 27 | [Second top-level ViewSet on a child model needs hand-made links](#27-a-second-top-level-viewset-on-a-child-model-needs-hand-made-links) | cosmetic | `render_number` and `get_success_url` reverse the nested URLs |
| 28 | [Two ViewSets on one model share every default label](#28-two-viewsets-on-one-model-share-every-default-label) | cosmetic | `cv_header_template_code` on the lists; breadcrumb keeps the model name |
| 29 | [Snippet templates see the object, not the view](#29-snippet-templates-only-see-the-object-not-the-view) | cosmetic | plainer message texts |
| 30 | ext: [Datetimepicker assets on every page, need jQuery](#30-ext-the-datetimepicker-assets-load-on-every-page-and-need-jquery) | annoyance | project head include loads jQuery 3.7.1 |
| 31 | ext: [Typeahead skins read Bootstrap's `--bs-*` properties](#31-ext-the-typeahead-skins-read-bootstraps---bs--custom-properties) | annoyance | theme CSS maps `--bs-*` to Tabler's `--tblr-*` |
| 32 | ext: [Datetimepicker keeps its own look](#32-ext-the-datetimepicker-keeps-its-own-look) | cosmetic | nothing |

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

- **Upstream tracking:** [django-crud-views #319](https://github.com/jacob-consulting/django-crud-views/issues/319)
  — phase 1, shared with finding 5; filed, not yet implemented.

- **What happened:** `BadgeEnum` is documented as "Bootstrap contextual colours for state badges" (`primary`,
  `success`, `danger`, `light`, `dark`, ...), and `crud_views_workflow/badge.html` pastes the value into
  `badge rounded-pill text-bg-<colour>`, a solid pill. Tabler's status badges are the light variants
  (`bg-green-lt`, ...). There is no hook for the class, and CSS could only restyle `text-bg-*` colour by colour, on
  every such badge of a project.
- **Where:** `src/crud_views_workflow/lib/enums.py:10` (`BadgeEnum`),
  `src/crud_views_workflow/templates/crud_views_workflow/badge.html:1`, rendered by `WorkflowModelMixin.get_state_badge`
  (`src/crud_views_workflow/lib/mixins.py:37`).
- **What we did:** a one-line theme override, `src/crud_views_tabler/templates/crud_views_workflow/badge.html`
  (`badge bg-<colour>-lt`; every `BadgeEnum` value has a `-lt` class in Tabler 1.6.1). Tested in
  `tests/crud_views_tabler/test_theme.py`.
- **Suggested upstream change:** a class key for the badge (`workflow:badge` → `badge rounded-pill text-bg-{colour}`),
  or let `STATE_BADGES` values be class strings.
- **Severity:** annoyance.

### 5. The workflow page is not framed, and its history table is not responsive

- **Upstream tracking:** [django-crud-views #319](https://github.com/jacob-consulting/django-crud-views/issues/319)
  — phase 1, shared with finding 4; filed, not yet implemented.

- **What happened:** `view_workflow.content.html` renders the history and the form straight into the page, not
  through `crud_views/snippets/form_frame.html`, so under the theme the workflow page has no card while every
  create/update/delete/custom-form page does. The history is a bare `<table class="table">` with no
  `.table-responsive` wrapper and no class of its own; at 390 px it was 549 px wide and the whole page scrolled
  sideways.
- **Where:** `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.content.html:3-5`,
  `view_workflow.history.html:6` (the table), `view_workflow.action.html:7` (the form).
- **What we did:** theme CSS (`crud_views_tabler.css`): below 768 px the content container that holds such a table
  (`.page-body > .container-xl:has(> table.table)`) gets `overflow-x: auto`, so it scrolls instead of the page; the
  table stays a table, so a narrow one still spans the full width (`display: block` on the table would shrink it).
  The scrollbar sits at the bottom of the content, not under the table. No frame: the order page has its own history and transition buttons; the workflow page is the
  fallback for steps that need a comment.
- **Suggested upstream change:** use the form frame for the action form, wrap the history in `.table-responsive`
  (or a `workflow:history` class key).
- **Severity:** cosmetic.

### 6. `WorkflowViewPermissionRequired` has one permission for every transition

- **Upstream tracking:** [django-crud-views #320](https://github.com/jacob-consulting/django-crud-views/issues/320)
  — phase 2, document and test the opt-in permission recipe while retaining the default `"change"` gate;
  filed, not yet implemented.

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

- **Upstream tracking:** [django-crud-views #322](https://github.com/jacob-consulting/django-crud-views/issues/322)
  — phase 3, shared model business-validation hook, opt-in transition buttons with explanations and comment
  requirements, `clean()` return fix, and reusable execution helper; filed, not yet implemented.
  Reuse phase 1 (#319)'s action form frame; implement that template integration after #319.

- **What happened:** (1) "Confirm only with at least one line" can be a django-fsm `conditions=[...]`, but then the
  step silently disappears and a posted confirm fails as "Select a valid choice". To show a reason the project has to
  subclass `WorkflowForm`. (2) `WorkflowForm.clean()` returns `None` instead of `cleaned_data`, so a subclass that
  writes `cleaned = super().clean()` crashes with `'NoneType' object has no attribute 'get'`. (3) Running a
  transition from code (seed data, a scheduled job) with its `WorkflowInfo` row means copying
  `WorkflowView.cv_form_valid`.
- **Where:** `src/crud_views_workflow/lib/forms.py:62` (`clean`), `src/crud_views_workflow/lib/views.py:85`
  (`cv_form_valid`).
- **What we did:** `OrderWorkflowForm.clean()` adds the reason to the `transition` field (`example/sales/forms.py`);
  `example/sales/workflow.py:run_transition` mirrors the view for the seed data.
- **Suggested upstream change:** `clean()` returns `cleaned_data`; a `custom={"refuse": callable}` (or a model hook
  `workflow_check_transition(name) -> str | None`) shown as a form error; a public `run_transition(obj, name, user,
  comment)` used by the view itself.
- **Severity:** annoyance.

## Card views

### 8. The card template has no block above the title

- **Upstream tracking:** [django-crud-views #325](https://github.com/jacob-consulting/django-crud-views/issues/325)
  — one small GSD phase shared with finding 9; add empty `card_root` and `card_header` insertion blocks,
  documentation, and regression tests. Theme template overrides must adopt the new blocks downstream;
  filed, not yet implemented.

- **What happened:** the product card (type badge row above the title, a `card-status-top` stripe as a direct child of
  `.card`) cannot be built by extending `crud_views/tags/card.html`: `card_content` renders below the title, and
  nothing sits at the card root. The `card:root` / `card:body` class keys exist, but they are global, and putting the
  badge row into `card_title` would nest block elements in the heading.
- **Where:** `src/crud_views/templates/crud_views/tags/card.html:4-8` (class keys `card:root`, `card:body`, blocks
  `card_title`, `card_content`, `card_actions`); `docs/reference/card-list-view.md:158` ("Custom Card Template").
- **What we did:** `example/catalog/templates/catalog/product_card.html` replaces the card and renders the actions
  itself with `{% cv_card_action_group %}` and the `button/container.html` include, as the theme's card does.
- **Suggested upstream change:** a `card_header` block before the title and a `card_root` block (first child of the
  root element), so projects extend the card instead of copying its action plumbing.
- **Severity:** annoyance.

### 9. A card list as the landing page needs `cv_key = "list"`

- **Upstream tracking:** [django-crud-views #325](https://github.com/jacob-consulting/django-crud-views/issues/325)
  — one small GSD phase shared with finding 8; document and test the existing cards-first/table-secondary
  configuration, including switching and navigation behavior, without adding a `cv_default_list` API;
  filed, not yet implemented.

- **What happened:** `CardListView` is `cv_key = "card"`, `cv_path = "card"`; "home", the cancel/success keys and the
  breadcrumbs all point at `list`. A ViewSet whose default list is the cards (with a table beside it) has to set
  `cv_key = "list"`, `cv_path = ""` on the card view, give the table view another key, and set
  `cv_home_key = "list"` on it. There is no semantic icon for a second list view either, so the table view uses
  `cv_icon_action = "tabler:table"`.
- **Where:** `src/crud_views/lib/views/card.py:22-23`, `src/crud_views/lib/view/base.py:104` (`cv_home_key`).
- **What we did:** the overrides above (`example/catalog/views.py`); they work.
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

- **What happened:** with `cv_object_detail_layout = "accordion"` a detail page shows only the group titles and an
  "N properties" badge until each panel is clicked; the docs say "Accordions remain initially collapsed; the tab
  `selected` flag does not open them". For a page whose point is its facts that reads as an empty page.
- **Where:** `src/crud_views_object_detail/templates/crud_views_object_detail/layouts/accordion/group.html:5`
  (`accordion-button collapsed`), `docs/reference/object_detail_layout_packs.md:130`.
- **What we did:** the green lot detail uses `card-rows` instead (products use the project default `tabs-vertical`,
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

- **What happened:** the object-detail tab initialiser calls `globalThis.bootstrap?.Tab`, bypassing `cv.adapters`.
  Tabler exposes Bootstrap only as `window.tabler`, so the init silently does nothing. The tabs still switch
  (Bootstrap's data API in Tabler's bundle handles `data-bs-toggle="pill"`), but the keyboard handling the init is
  for is lost.
- **Where:** `src/crud_views_object_detail/static/crud_views_object_detail/js/tabs.js:29`, `:41`.
- **What we did:** nothing; not worth a theme shim.
- **Suggested upstream change:** resolve `Tab` through an adapter like modal/tooltip/collapse.
- **Severity:** annoyance.

### 18. The header icon is drawn beside a custom header template

- **What happened:** `cv_header_template` replaces only the heading text; the viewset's header icon is still drawn
  before it, so the customer page showed the shop icon and then the customer's avatar. `cv_icon_header = ""` does not
  help (`view_icon or viewset.icon_header` falls back); overriding `cv_get_header_icon()` to return `None` works,
  since `render_icon(None)` renders nothing, but that is not documented.
- **Where:** `src/crud_views/lib/view/base.py:467` (`cv_get_header_icon`),
  `src/crud_views/templatetags/crud_views.py:331` (`cv_header_icon`); the theme renders it in the `page_title` block
  of `src/crud_views_tabler/templates/crud_views_tabler/page.html`.
- **What we did:** `CustomerDetailView.cv_get_header_icon()` returns `None` (`example/sales/views/customers.py`).
- **Suggested upstream change:** document that, or let `cv_icon_header = None` on a view mean "no icon".
- **Severity:** cosmetic.

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

- **What happened:** the cupping scores are one row per taster with seven narrow number columns.
  `FormSet(form_show_labels=...)` is all or nothing, so either every row carries its labels (what the demo does,
  about twice the height of a table) or none does and the columns have no header.
- **Where:** `src/crud_views/lib/formsets/formsets.py:64` (`form_show_labels`),
  `src/crud_views/lib/formsets/inline_formset.py:56` (`get_helper`, one helper for every form).
- **What we did:** `form_show_labels=True`, and `CuppingScoreForm` gives the inputs `form-control-sm`.
- **Suggested upstream change:** labels on the first row only (or a header row above the formset) as an option.
- **Severity:** cosmetic.

## Permissions (Guardian, custom forms, manage)

### 23. Child viewsets under a Guardian parent need their own gate; no page tabs for children

- **What happened:** `GuardianParentPermissionMixin` requires the child views to carry per-object Guardian grants on
  the child rows too, so a child with a plain `ViewSet` (addresses) is not covered by the parent's grants. Also, the
  mockup's tabs (Orders / Addresses / Subscriptions) on the parent detail have no equivalent: `ChildContextButton`
  gives buttons linking to the nested lists.
- **Where:** `src/crud_views_guardian/lib/mixins.py:280` (`_guardian_child_composition_error`),
  `docs/reference/context_buttons.md:156` (`ChildContextButton`).
- **What we did:** a 10-line `CustomerGrantMixin` that checks the URL's customer (view to read, change to write;
  `example/sales/views/addresses.py`); Orders, Subscriptions and Addresses are context buttons on the customer page.
- **Suggested upstream change:** a parent-only mode for Guardian child views (inherit the parent's grants), and a
  tab/nav rendering of child viewsets on the parent detail page.
- **Severity:** annoyance.

### 24. A no-object custom form needs an undocumented recipe for its own permission

- **What happened:** "Run subscriptions" is not a CRUD action, and only the Owner may run it.
  `permission_required` looks `cv_permission` up in `ViewSet.permissions`, which is built from the model's
  `Permission` rows by stripping `_<model>` from each codename. The working recipe is a `Meta.permissions` entry
  `run_customersubscription` on the model plus `cv_permission = "run"` on the view; nothing in the docs or the
  `custom_form` example says so (the examples reuse `view`). A `cv_permission` naming a permission that does not exist
  fails at request time with an assert, not at check time.
- **Where:** `src/crud_views/lib/view/base.py:1062` (`permission_required`),
  `src/crud_views/lib/viewset/__init__.py:437` (`default_permissions`),
  `src/crud_views/lib/views/form.py:72` (`CustomFormNoObjectViewPermissionRequired`).
- **What we did:** the model permission above; the button shows disabled (`cv_inaccessible_actions = "disable"`) and
  the URL answers 403 for everyone else.
- **Suggested upstream change:** document the recipe next to `CustomFormNoObjectViewPermissionRequired`, and a system
  check that `cv_permission` resolves to a permission of the viewset's model.
- **Severity:** annoyance.

### 25. Manage pages are open to every signed-in user while DEBUG is on

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

- **What happened:** `crud_views.lib.table.Table.__init__` passes `sequence=("...", "actions")` unless the caller
  does, which beats a subclass's `Meta.sequence`, so inherited columns come first. A list with `cv_list_actions = []`
  still renders an empty "Actions" column.
- **Where:** `src/crud_views/lib/table/table.py:31-33`.
- **What we did:** `OrderTableBase.__init__` passes the wanted sequence; the top-level table sets
  `Meta.exclude = ("actions",)` (`example/sales/views/orders.py`).
- **Suggested upstream change:** honour `Meta.sequence` (append `actions` to it), and drop the column when the view has
  no list actions.
- **Severity:** annoyance.

### 27. A second, top-level ViewSet on a child model needs hand-made links

- **What happened:** orders live under the customer (`order`, the full editor) and in a top-level list (`orders`,
  list + create). The top-level ViewSet has no detail view, so `LinkDetailColumn` and row actions cannot point at the
  nested pages; the create view cannot redirect into the other ViewSet with a success key either.
- **Where:** `src/crud_views/lib/table/columns.py:53` (`LinkDetailColumn` uses the table's own ViewSet),
  `src/crud_views/lib/view/base.py:244` (`get_success_url`).
- **What we did:** `AllOrdersTable.render_number` reverses `order-detail`; `AllOrdersCreateView.get_success_url`
  reverses `order-update` (`example/sales/views/orders.py`).
- **Suggested upstream change:** a `LinkColumn(viewset=..., key=...)` and a success target in another ViewSet.
- **Severity:** cosmetic.

### 28. Two ViewSets on one model share every default label

- **What happened:** the nested and top-level subscription lists both default to the header "Customer subscriptions"
  (from `CustomerSubscription._meta.verbose_name`), also in the breadcrumb; only the page header can be changed per
  view (`cv_header_template_code`), the breadcrumb and create/update headers keep the model name.
- **Where:** `src/crud_views/lib/viewset/__init__.py:478-487` (`get_meta`: `verbose_name` from the model's `_meta`).
- **What we did:** `cv_header_template_code = "Subscriptions"` on the two lists; the breadcrumb keeps the model name.
- **Suggested upstream change:** a `ViewSet(verbose_name=..., verbose_name_plural=...)` override that every default
  label follows.
- **Severity:** cosmetic.

### 29. Snippet templates only see the object, not the view

- **What happened:** header, paragraph and message template codes render with a context that has `object` but not
  `view`, so "Created {{ view.duplicate }} from {{ object }}" or "a draft for {{ view.cv_get_parent_object }}" render
  empty.
- **Where:** `src/crud_views/lib/view/base.py:436` (`render_snippet` builds its context from the caller's dict at
  `:442`).
- **What we did:** plainer texts.
- **Suggested upstream change:** add `view` (and the parent object on child views) to the snippet data.
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

---

## Not shown in the demo

Features from the spec's feature map that were dropped or reduced, with the reason.

- **Accordion object-detail pack:** not used; it opens every panel closed (#15). The demo shows `split-card`
  (customers), `card-rows` (green lots) and the project default `tabs-vertical` (products and the rest).
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
