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
- **Where:** `examples/bootstrap5/project/templatetags/example_tags.py:52` (`snippet_panels`), used by
  `examples/bootstrap5/project/templates/project/crud_views.html`; copied in
  `../django-crud-views-extensions/examples/bootstrap5/project/templatetags/example_tags.py`.
- **What we did:** vendored our own version in the example project.
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

## Workflow `BadgeEnum` values are Bootstrap colour names

- **What happened:** `BadgeEnum` is documented as "Bootstrap contextual colours for state badges" (`primary`,
  `success`, `danger`, `light`, `dark`, ...). Tabler has the same names but also its own palette (`bg-orange-lt`,
  `bg-green-lt`, ...) and uses `-lt` (light) variants for status pills. The enum has no way to name those.
  To be checked in detail when the order workflow badges are built.
- **Where:** `src/crud_views_workflow/lib/enums.py:10` (`BadgeEnum`).
- **What we did:** (to be completed by the workflow task) map the Bootstrap names to Tabler classes through the
  theme's class keys where possible.
- **Suggested upstream change:** let the enum, or the badge template, take a class string so a theme can supply
  `bg-green-lt`.
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
  `init.js` load on every crud_views page, including ones with no date field. The theme loads no jQuery, so each page
  logs `jQuery is not defined` and `$ is not defined` in the console. Harmless to the page, noisy for a demo.
- **Where:** `../django-crud-views-extensions/src/crud_views_widget_datetimepicker/` (asset registration).
- **What we did:** nothing yet; the demo has no date pickers on these pages.
- **Suggested upstream change:** register the assets only for views whose form has a picker widget, or load jQuery
  as a declared dependency of the asset.
- **Severity:** annoyance.
