# Upstream findings from the Acme Roasters demo

Candidates for django-crud-views and django-crud-views-extensions that came up while building the roastery demo.
Not filed as issues; to be triaged. Each entry: what happened, where (upstream path:line, read from the sibling
checkout at `b73337ce`, "Examples: restructure the example app for 1.0 (#309)"), what the theme/demo did instead,
the suggested upstream change, and a severity (blocker / annoyance / cosmetic).

The rule for this file: every theme CSS fix or override template, and every upstream bug or awkwardness, is logged
here in the same commit that introduces it.

## The "show code" panel is example-only upstream

- **What happened:** the `{% snippet_panels %}` tag that renders "the code behind this page" lives in the upstream
  example project, not in the library. Every theme or demo that wants the panel has to copy it (the extensions repo
  already did). The roastery demo does the same for the "How this is themed" page (Task 12) and keeps an empty
  `{% block code_panel %}` in `example/templates/project/crud_views.html`.
- **Hooking it in needed no new block:** with `CRUD_VIEWS_EXTENDS` pointing at the project's own template, the panel
  goes below the theme page's `content` block and the "Show code" toggle into its `actions` block
  (`{{ block.super }}` keeps `cv_context_actions`). Modal partials render `cv_content_template` without the extends
  chain, so the panel never shows inside a modal. The view is in the context as `view`, which is all the collector
  needs (`type(view).__module__` names the app).
- **Where:** `examples/bootstrap5/project/templatetags/example_tags.py:52` (`snippet_panels`), used by
  `examples/bootstrap5/project/templates/project/crud_views.html`; copied in
  `../django-crud-views-extensions/examples/bootstrap5/project/templatetags/example_tags.py`.
- **What we did:** wrote our own in the example project: `example/config/showcode.py` (collector; a fixed file set
  per app, the app must live in `example/`, settings.py only as a whitelist of assignments) and the `showcode` tag
  library in `example/config/templatetags/` (registered through `TEMPLATES['OPTIONS']['libraries']`, since `config`
  is not an app). Side effect worth knowing for an upstream version: the inline source mentions every label the app
  can render, so `assertNotContains` tests on a page see it; the demo's tests strip it with `without_code_panel()`.
  Lazy loading the sources (a fetch when the panel opens) would avoid that and the page weight (~390 KB of
  highlighted HTML on a `sales` page).
- **Suggested upstream change:** ship the tag (or a documented recipe) in the library.
- **Severity:** annoyance.

## The tooltip recipe still says to replace `init`

- **What happened:** the documented way to add per-location tooltip configuration is to assign
  `cv.adapters.tooltip.init = ...`. That drops upstream's Bootstrap transition guard in the original `init`; the
  tooltip object also carries `hide`/`dispose`, so replacing the whole object is worse. The theme wraps `init` and
  calls the original instead (`src/crud_views_tabler/static/crud_views_tabler/tabler-adapters.js`).
- **Where:** `docs/reference/javascript.md:142` (and the `cv.adapters.tooltip = {init() {}}` example around line 123);
  also noted in `docs/crud_views_upstream_status.md` here, from the 2026-11-04 tidy-up.
- **What we did:** wrap, never replace.
- **Suggested upstream change:** change the recipe to wrap the original `init`, or expose a supported per-location
  hook so nobody needs to touch `init`.
- **Severity:** annoyance.

## `Column1..Column12` hard-code `col-md-N`

- **What happened:** the crispy layout helpers `Column1` ... `Column12` set `css_class = "col-md-N"`. That is right
  for Tabler (same grid as Bootstrap 5), but a theme on a non-Bootstrap grid cannot change the breakpoint or the class
  prefix without subclassing every helper.
- **Where:** `src/crud_views/lib/crispy/table.py:4` (`Column1`; exported from
  `src/crud_views/lib/crispy/__init__.py`).
- **What we did:** nothing, Tabler uses the same classes.
- **Suggested upstream change:** a documentation note, or a setting for the breakpoint.
- **Severity:** cosmetic.

## Workflow `BadgeEnum` values are Bootstrap colour names; the badge template is a solid pill

- **What happened:** `BadgeEnum` is documented as "Bootstrap contextual colours for state badges" (`primary`,
  `success`, `danger`, `light`, `dark`, ...), and `crud_views_workflow/badge.html` pastes the value into
  `badge rounded-pill text-bg-<colour>`, a solid pill. Tabler's status badges are the light variants
  (`bg-green-lt`, ...). There is no hook for the class, and CSS could only restyle `text-bg-*` colour by colour, on
  every such badge of a project.
- **Where:** `src/crud_views_workflow/lib/enums.py:10` (`BadgeEnum`), `src/crud_views_workflow/templates/crud_views_workflow/badge.html`,
  rendered by `WorkflowModelMixin.get_state_badge` (`src/crud_views_workflow/lib/mixins.py:37`).
- **What we did:** a one-line theme override, `src/crud_views_tabler/templates/crud_views_workflow/badge.html`
  (`badge bg-<colour>-lt`; every `BadgeEnum` value has a `-lt` class in Tabler 1.6.1). The orders keep `BadgeEnum`
  values in `STATE_BADGES` (`example/sales/models.py`). Tested in `tests/crud_views_tabler/test_theme.py`.
- **Suggested upstream change:** a class key for the badge (`workflow:badge` → `badge rounded-pill text-bg-{colour}`),
  or let `STATE_BADGES` values be class strings.
- **Severity:** annoyance.

## `WorkflowViewPermissionRequired` has one permission for every transition

- **What happened:** the workflow view checks one `cv_permission` (`"change"`) before any transition is offered. The
  roastery's Roasters may only take one step (confirmed → roasted) and otherwise only view orders. django-fsm's own
  `permission=` on `@transition` supports per-step rules, and upstream filters the offered steps through
  `get_available_user_state_transitions(user)`, so that part works; but the view-level gate has to be lowered to
  `"view"` for it to matter, which nothing documents.
- **Where:** `src/crud_views_workflow/lib/views.py:147` (`cv_permission = "change"`), `lib/mixins.py:84`
  (`workflow_get_possible_transitions`).
- **What we did:** `OrderWorkflowView.cv_permission = "view"`; each transition carries `permission=may_change_order`
  or `may_roast_order` (`example/sales/models.py`); `cv_action_enabled` disables the workflow action when the user has
  no step left (`example/sales/views/order_actions.py`). A disallowed step posted anyway is not a choice of the form,
  so it fails validation.
- **Suggested upstream change:** document the `permission=` + `cv_permission = "view"` recipe, or make the default
  gate "any possible transition".
- **Severity:** annoyance.

## Workflow: no refusal-with-message hook, `WorkflowForm.clean()` returns None, no helper outside the view

- **What happened:** (1) "Confirm only with at least one line" can be a django-fsm `conditions=[...]`, but then the
  step silently disappears and a posted confirm fails as "Select a valid choice". To show a reason the project has to
  subclass `WorkflowForm`. (2) `WorkflowForm.clean()` returns `None` instead of `cleaned_data`, so a subclass that
  writes `cleaned = super().clean()` crashes with `'NoneType' object has no attribute 'get'`. (3) Running a transition
  from code (seed data, a scheduled run) with its `WorkflowInfo` row means copying `WorkflowView.cv_form_valid`.
- **Where:** `src/crud_views_workflow/lib/forms.py:62` (`clean`), `src/crud_views_workflow/lib/views.py:85`
  (`cv_form_valid`).
- **What we did:** `OrderWorkflowForm.clean()` adds the reason to the `transition` field (`example/sales/forms.py`);
  `example/sales/workflow.py:run_transition` mirrors the view for the seed (Task 7 can reuse it).
- **Suggested upstream change:** `clean()` returns `cleaned_data`; a `custom={"refuse": callable}` (or a model hook
  `workflow_check_transition(name) -> str | None`) shown as a form error; a public `run_transition(obj, name, user,
  comment)` used by the view itself.
- **Severity:** annoyance.

## The card template has no block above the heading or at the card root

- **What happened:** the product card (type badge row above the title, a `card-status-top` stripe as a direct child of
  `.card`) cannot be built from `crud_views/tags/card.html`: `card_content` renders below the heading, and nothing
  sits at the card root. Putting the badge row into `card_title` would nest block elements in the `<h3>`.
- **Where:** `src/crud_views/templates/crud_views/tags/card.html` (blocks `card_title`, `card_content`,
  `card_actions`) at `b73337ce`; documented in `docs/reference/card-list-view.md` ("Custom Card Template").
- **What we did:** `example/catalog/templates/catalog/product_card.html` replaces the card outright and renders the
  actions itself with `{% cv_card_action_group %}` and the `button/container.html` include, as the theme's card does.
- **Suggested upstream change:** add a `card_header` block before the heading and a `card_root` hook (or an
  `attrs`/extra-class hook) so projects can extend the card instead of copying its action plumbing.
- **Severity:** annoyance.

## Polymorphic create-select shows lower-case type names

- **What happened:** the "Type" choices are `ContentType.name`, i.e. the model's lower-case `verbose_name`
  ("beans", "equipment"). Every project capitalises them in its own form subclass.
- **Where:** `src/crud_views_polymorphic/lib/create_select.py` (`get_form`) builds `(ct.id, ct.name)`.
- **What we did:** `ProductContentTypeForm.__init__` capitalises the labels.
- **Suggested upstream change:** use `capfirst(model._meta.verbose_name)` (or `ct.model_class()._meta.verbose_name`
  with capfirst) for the labels.
- **Severity:** cosmetic.

## Object detail prints the stored value of a field with `choices`

- **What happened:** `"process"` renders `washed`, not `Washed`; the resolver does not use `get_FOO_display`. Showing
  the label needs `x("get_process_display", title=...)` per choice field, plus a hand-written title.
- **Where:** `src/crud_views_object_detail/lib/resolvers.py` (`resolve_property`).
- **What we did:** point such properties at `get_<field>_display` with an explicit title.
- **Suggested upstream change:** when the model field has `choices`, resolve to the display value by default.
- **Severity:** annoyance.

## A polymorphic detail view cannot give each kind its own property groups

- **What happened:** `ObjectDetailMixin.cv_property_display` is a single class attribute (and check `E240` demands
  it), but a polymorphic ViewSet shows a different set of fields per kind. The demo overrides the `property_display`
  property to pick the groups by `type(self.object)` and still sets a dummy `cv_property_display` for the check.
- **Where:** `src/crud_views_object_detail/lib/mixins.py` (`property_display`, `E240`);
  `examples/bootstrap5/polymorphic_demo/views.py` sidesteps it with one shared group.
- **What we did:** `ProductDetailView.property_display` returns `PROPERTY_DISPLAY[type(self.object)]`.
- **Suggested upstream change:** document the `property_display` hook, or accept a `{Model: groups}` dict.
- **Severity:** annoyance.

## A card list as the landing page needs `cv_key = "list"` on the card view

- **What happened:** `CardListView` is `cv_key="card"`, `cv_path="card"`; "home", the cancel/success keys and the
  breadcrumbs all point at `list`. A ViewSet whose default list is the cards (with a table beside it) has to set
  `cv_key = "list"`, `cv_path = ""` on the card view and give the table view another key, plus `cv_home_key = "list"`
  on it. There is no semantic icon for a second list view either, so the table view uses `cv_icon_action =
  "tabler:table"`.
- **Where:** `src/crud_views/lib/views/card.py:15-17`, `src/crud_views/lib/view/base.py:104` (`cv_home_key`).
- **What we did:** the overrides above; they work.
- **Suggested upstream change:** a documented recipe for "two list views on one ViewSet" (or a `cv_default_list`).
- **Severity:** cosmetic.

## `tabs.js` looks up `globalThis.bootstrap` directly

- **What happened:** the object-detail tab initialiser calls `globalThis.bootstrap?.Tab`, bypassing `cv.adapters`.
  Tabler exposes Bootstrap only as `window.tabler`, so the init silently does nothing. The tabs still switch (Bootstrap's
  own data API in Tabler's bundle handles `data-bs-toggle="pill"`; checked with a script click), but the
  keyboard-readiness the init is for is lost.
- **Where:** `src/crud_views_object_detail/static/crud_views_object_detail/js/tabs.js` (`const Tab = globalThis.bootstrap?.Tab`).
- **What we did:** nothing (works for pointer use); not worth a theme shim.
- **Suggested upstream change:** resolve `Tab` through an adapter like modal/tooltip/collapse.
- **Severity:** annoyance.

## The datetimepicker assets load on every page and need jQuery

- **What happened:** with `crud_views_widget_datetimepicker` installed, `jquery.datetimepicker.full.min.js` and
  `init.js` load at the end of `<body>` on every crud_views page, including pages with no date field. The package
  expects the project to load jQuery first ("jQuery precedes both, loaded by the project"), but nothing checks or
  documents it where a project would look. With no jQuery, every page logged `jQuery is not defined` and
  `$ is not defined` in the console.
- **Where:** `../django-crud-views-extensions/src/crud_views_widget_datetimepicker/assets.py` (`source_files`
  docstring is the only mention of the requirement).
- **What we did:** `example/templates/django_tabler/includes/head.html` loads jQuery 3.7.1 (pinned, with SRI and
  `crossorigin`) from code.jquery.com, so it precedes the plugin. Verified in Playwright: no console errors on the
  product card list, table list, product detail or a showcase page.
- **Suggested upstream change:** emit the picker assets only through the widget's `Media` on pages whose form uses a
  picker, and/or add a system check or a docs section stating the jQuery requirement.
- **Severity:** annoyance.

## Conditional groups only toggle on a boolean checkbox

- **What happened:** `ConditionalGroup` takes a `ToggleSource` that reads a boolean (`ModelFieldToggle` / `UIFieldToggle`),
  and `toggle.js` binds to a *checkbox* named by `ToggleGroup`. The roastery's `Customer.kind` is a two-value choice
  (wholesale / consumer), so it cannot drive the group. The group also refuses fields whose form field is not a plain
  text/number pair (a `TypedChoiceField` such as `price_tier`) until `empty_values` is given explicitly.
- **Where:** `src/crud_views/lib/conditional/toggle.py` (`ToggleSource.is_on`), `group.py` (`resolve_conditional_empty_value`),
  `static/crud_views/js/toggle.js` (`findCheckboxes`).
- **What we did:** the customer form declares a transient `is_wholesale` checkbox (`UIFieldToggle`), derives
  `Customer.kind` from it in `clean()`, seeds it from the stored kind when editing, and passes `empty_values` for the
  choice fields (`example/sales/forms.py`). A POST of `kind=...` alone does nothing; tests post `is_wholesale`.
- **Suggested upstream change:** a toggle source that compares a field to a value (`ValueToggle("kind", "wholesale")`),
  with the JS reading a select/radio, and choice fields supported by the empty-value resolver (empty string / None
  according to `null`).
- **Severity:** annoyance.

## `ToggleGroup(legend=...)` has an unstyled legend

- **What happened:** the legend of the toggle fieldset renders at the browser/Bootstrap `legend` size (about 1.5rem,
  floated), far larger than any label around it.
- **Where:** `src/crud_views/templates/crud_views/conditional/toggle_group.html`.
- **What we did:** CSS in `crud_views_tabler.css` (`.cv-toggle-group > legend`): not floated, 1rem, bold.
- **Suggested upstream change:** a class on the legend (or a `legend` size in the stock template) so themes can style it.
- **Severity:** cosmetic.

## Object detail shows model `help_text` in the value column

- **What happened:** a field's `help_text` (e.g. "ISO country code, e.g. DE.") is printed under its value on the detail
  page, where it reads as noise.
- **Where:** `crud_views_object_detail` property rendering.
- **What we did:** moved the help text from the model to the form field (`example/sales/forms.py`).
- **Suggested upstream change:** option to omit help text on detail pages (or omit it by default).
- **Severity:** cosmetic.

## Child viewsets under a Guardian parent need their own gate; no page tabs for children

- **What happened:** `GuardianParentPermissionMixin` requires the child views to also carry per-object Guardian grants
  on the child rows (`GuardianObjectPermissionMixin`/`GuardianQuerysetMixin`), so a child with a plain `ViewSet`
  (addresses) is not covered by the parent's grants. The demo adds a 10-line `CustomerGrantMixin` that checks the URL
  customer (view to read, change to write). Also, the mockup's tabs (Orders / Addresses / Subscriptions) on the parent
  detail have no equivalent: `ChildContextButton` gives buttons linking to the nested lists instead.
- **Where:** `src/crud_views_guardian/lib/mixins.py` (`_guardian_child_composition_error`),
  `docs/reference/context_buttons.md` (ChildContextButton).
- **What we did:** `example/sales/views/addresses.py` (`CustomerGrantMixin`); "Addresses" is a context button on the customer detail.
- **Suggested upstream change:** a parent-only mode for Guardian child views (inherit the parent's grants), and a
  tab/nav rendering of child viewsets on the parent detail page.
- **Severity:** annoyance.

## The detail header icon sits beside a custom avatar header

- **What happened:** `cv_header_template` replaces only the heading text; the viewset icon is still drawn before it, so
  a customer page shows the shop icon and then the avatar.
- **Where:** the theme's `page_title` block (`src/crud_views_tabler/templates/crud_views_tabler/page.html`), `cv_header_icon`.
- **What we did:** left as is.
- **Suggested upstream change:** a per-view switch to hide the header icon.
- **Severity:** cosmetic.

## Formsets have no per-row conditional fields

- **What happened:** an order line's grind and bag size only apply when the row's product is coffee. Conditional
  groups toggle on a checkbox of the main form, and `ConditionalFormSet` switches a whole first-level formset; neither
  can follow a select inside each formset row.
- **Where:** `src/crud_views/lib/conditional/` (`ConditionalGroup`, `ConditionalFormSet`), `static/crud_views/js/toggle.js`.
- **What we did:** `OrderLineForm.clean()` clears the two fields for non-coffee products and `OrderLine.save()` does
  too; `ProductSelect` marks coffee options `data-beans` and `example/sales/static/sales/sales.js` disables the two
  selects in that row (progressive enhancement, registered with `register_assets`).
- **Suggested upstream change:** a row-scoped toggle (a `ValueToggle` on a field of the same form, see the
  conditional-groups finding above) that `formset.js` re-binds for added rows.
- **Severity:** annoyance.

## The formset title is an unstyled `<legend>`

- **What happened:** `crud_views/formsets/formset.html` renders the formset title as a bare `<legend>` (about 1.5rem,
  floated), larger than the page's card titles.
- **Where:** `src/crud_views/templates/crud_views/formsets/formset.html` (`<legend>{{ x_formset.title }}</legend>`).
- **What we did:** the existing legend rule in `crud_views_tabler.css` now covers `.cv-formset-fieldset > legend` too.
- **Suggested upstream change:** a class key on the legend, as for the toggle group.
- **Severity:** cosmetic.

## The typeahead skins read Bootstrap's `--bs-*` custom properties

- **What happened:** the select popup of `crud_views_widget_typeahead` uses `var(--bs-body-bg)`,
  `--bs-border-color-translucent`, `--bs-border-radius`, `--bs-secondary-color`, `--bs-highlight-bg`. Tabler names its
  properties `--tblr-*`, so the popup had no background or border and the form's buttons showed through the result
  list. Tabler's `.dropdown-item` is also a flex row with a gap, which split the `<mark>` highlight off the word.
- **Where:** `../django-crud-views-extensions/src/crud_views_widget_typeahead/static/crud_views_widget_typeahead/typeahead-select.css`
  and `typeahead.css`.
- **What we did:** CSS in `crud_views_tabler.css`: `.cv-typeahead, .cv-typeahead-select` define the `--bs-*`
  properties from Tabler's, plus a dropdown shadow and `display: block` for the items. No template override needed.
- **Suggested upstream change:** fall back in the CSS (`var(--bs-body-bg, var(--tblr-bg-surface, #fff))`) or expose
  `--cv-typeahead-*` properties a theme sets.
- **Severity:** annoyance (broken popup without the fix).

## `Table` forces `sequence=("...", "actions")` and always adds the actions column

- **What happened:** `crud_views.lib.table.Table.__init__` passes `sequence` unless the caller does, which beats a
  subclass's `Meta.sequence`, so inherited columns come first. A list with `cv_list_actions = []` still renders an
  empty "Actions" column.
- **Where:** `src/crud_views/lib/table/table.py:28-33`.
- **What we did:** `OrderTableBase.__init__` passes the wanted sequence; the top-level table sets
  `Meta.exclude = ("actions",)` (`example/sales/views/orders.py`).
- **Suggested upstream change:** honour `Meta.sequence` (append `actions` to it), and drop the column when the view has
  no list actions.
- **Severity:** annoyance.

## Snippet templates only see the object, not the view

- **What happened:** header, paragraph and message template codes render with a context that has `object` but not
  `view`, so "Created {{ view.duplicate }} from {{ object }}" or "a draft for {{ view.cv_get_parent_object }}"
  render empty.
- **Where:** `src/crud_views/lib/view/base.py:436` (`render_snippet` builds `Context(data)` from the caller's dict).
- **What we did:** plainer texts.
- **Suggested upstream change:** add `view` (and the parent object on child views) to the snippet data.
- **Severity:** cosmetic.

## A second, top-level ViewSet on a child model needs hand-made links

- **What happened:** orders live under the customer (`order`, the full editor) and in a top-level list (`orders`,
  list + create). The top-level ViewSet has no detail view, so `LinkDetailColumn` and row actions cannot point at the
  nested pages; the create view cannot redirect into the other ViewSet with a success key either.
- **Where:** `src/crud_views/lib/table/columns.py` (`LinkDetailColumn` uses the table's own ViewSet),
  `src/crud_views/lib/view/base.py:244` (`get_success_url`).
- **What we did:** `AllOrdersTable.render_number` reverses `order-detail`; `AllOrdersCreateView.get_success_url`
  reverses `order-update` (`example/sales/views/orders.py`).
- **Suggested upstream change:** a `LinkColumn(viewset=..., key=...)` and a success target in another ViewSet.
- **Severity:** cosmetic.

## The workflow page is not framed like the other form pages

- **What happened:** `crud_views_workflow/view_workflow.content.html` renders history and form directly, not through
  `crud_views/snippets/form_frame.html`, so under the theme it has no card while create/update/delete pages do. The
  xdsoft date picker likewise keeps its own (blue) look.
- **Where:** `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html`.
- **What we did:** nothing; the order page shows its own history and transition buttons, the workflow page is the
  fallback for steps that need a comment.
- **Suggested upstream change:** use the form frame in the workflow templates.
- **Severity:** cosmetic.

## A no-object custom form has no way to carry a custom permission except `cv_permission` plus a model `Meta.permissions` entry

- **What happened:** "Run subscriptions" is not a CRUD action, and only the Owner may run it, so it needs its own
  permission. `permission_required` looks `cv_permission` up in `ViewSet.permissions`, which is built from the model's
  `Permission` rows by stripping `_<model>` from each codename. The working recipe is a `Meta.permissions` entry
  `run_customersubscription` on the model and `cv_permission = "run"` on the view. It works, but nothing in the docs
  or the `custom_form` example says so; the examples reuse `view`. A `cv_permission` naming a permission that does
  not exist yet fails at request time with an assert, not at check time.
- **Where:** `src/crud_views/lib/view/base.py:1062` (`permission_required`), `src/crud_views/lib/viewset/__init__.py:437`
  (`default_permissions`).
- **What we did:** the model permission above; the button shows disabled (`cv_inaccessible_actions = "disable"`)
  and the URL answers 403.
- **Suggested upstream change:** document the recipe next to `CustomFormNoObjectViewPermissionRequired`, and add a system
  check that `cv_permission` resolves to a permission of the viewset's model.
- **Severity:** annoyance.

## A top-level ViewSet's list header is the model's verbose name

- **What happened:** the nested and top-level subscription lists both default to the header "Customer subscriptions"
  (from `CustomerSubscription._meta.verbose_name`), also in the breadcrumb; only the page header can be changed per
  view (`cv_header_template_code`), the breadcrumb and create/update headers keep the model name. Both ViewSets on
  one model therefore read the same.
- **Where:** `src/crud_views/lib/view/base.py` (header and breadcrumb defaults).
- **What we did:** `cv_header_template_code = "Subscriptions"` on the two lists; the breadcrumb keeps the model name.
- **Suggested upstream change:** a `ViewSet(verbose_name=...)` override, so every default label follows it.
- **Severity:** cosmetic.

## The accordion detail pack opens every panel closed

- **What happened:** with `cv_object_detail_layout = "accordion"` a detail page shows only the group titles and a
  "N properties" badge until each panel is clicked; the docs say "Accordions remain initially collapsed; the tab
  `selected` flag does not open them". For a lot page whose whole point is its facts that reads as an empty page.
- **Where:** `src/crud_views_object_detail/templates/crud_views_object_detail/layouts/accordion/group.html:5`
  (`accordion-button collapsed`, `aria-expanded="false"`), `docs/reference/object_detail_layout_packs.md:130`.
- **What we did:** the green lot detail uses `card-rows` instead (the catalog uses tabs, customers `split-card`); the
  accordion pack is not shown anywhere in the demo.
- **Suggested upstream change:** open the group flagged `selected` (or the first one), like the tab packs.
- **Severity:** annoyance.

## A compact, table-like formset repeats its labels on every row

- **What happened:** the cupping scores are one row per taster with seven narrow number columns. `FormSet(
  form_show_labels=...)` is all or nothing, so either every row carries its labels (what the demo does, about twice
  the height of a table) or none does and the columns have no header.
- **Where:** `src/crud_views/lib/formsets/formsets.py:64` (`form_show_labels`),
  `src/crud_views/lib/formsets/inline_formset.py:get_helper` (one helper for every form).
- **What we did:** `form_show_labels=True`, and `CuppingScoreForm` gives the number inputs `form-control-sm`.
- **Suggested upstream change:** labels on the first row only (or a header row above the formset) as an option.
- **Severity:** cosmetic.

## `ObjectDetailMixin` plus `ObjectDetailViewPermissionRequired` is an MRO error

- **What happened:** a detail view declared `(BreadcrumbMixin, ObjectDetailMixin, ObjectDetailViewPermissionRequired)`
  raises "Cannot create a consistent method resolution order"; the permission-required class already includes the
  mixin, while the plain `DetailViewPermissionRequired` needs it added (the catalog's product detail does).
- **Where:** `src/crud_views_object_detail/lib/` (`ObjectDetailViewPermissionRequired` bases).
- **What we did:** use the permission-required class alone.
- **Suggested upstream change:** state this in the object detail docs next to the mixin recipe.
- **Severity:** cosmetic.
