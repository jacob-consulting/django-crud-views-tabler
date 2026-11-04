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
