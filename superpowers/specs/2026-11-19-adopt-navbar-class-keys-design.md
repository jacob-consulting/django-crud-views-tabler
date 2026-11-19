# Adopt upstream navbar class keys and owner-heading contract (#384, findings 36 and 38)

Short design, approved 2026-11-19.

## Intent

Upstream's #384 branch (checked out in `../django-crud-views`) adds six navbar class keys (finding 36) and rewords
the ViewSet Navigation contract so a theme may show the owner as the page heading, with a published
"owner as page heading" recipe (finding 38). Adopt both so the theme uses real Tabler classes instead of CSS that
imitates tabs, and record both findings as resolved.

## Goals

- Register `navbar:nav` = `nav nav-bordered flex-wrap` (Tabler's underline tabs, as in `tasks.html`) and
  `navbar:link` = `nav-link mw-100 text-break gap-2` in `TABLER_BUTTON_CLASSES`; item and active keep defaults.
- Drop the pill-to-tab CSS; keep only the active-tab colour (`--tblr-link-color`, the plain primary is too dim in
  dark mode, about 2.9:1) and the smaller view-title rule.
- `page.html`: structure unchanged (already matches the recipe: breadcrumb once, owner `h1`, tabs, view `h2`);
  comments updated. `cv_tabler_heading_repeats_tab` stays theme-owned (upstream leaves duplicate-title handling to
  themes).
- Tests: rendered tabs carry `nav-bordered`, not `nav-pills`.
- Docs: findings 36 and 38 resolved by #384 (table rows and entries), PR #383 now merged; `docs/crud_views_tabler.md`.
- Browser check, light and dark.

## Non-goals

- `navbar:wrapper` / `navbar:identity` keys: the theme never renders those leaves.
- The view heading as `h1` without a navbar (upstream recipe): separate earlier choice, unchanged.

## Approaches

1. **Class keys + Tabler `nav-bordered`** (picked): no template override, least CSS.
2. Keys with `nav-tabs`: Tabler's boxed tabs, not the underline look the demo has.
3. Keep the CSS on `nav-pills`: ignores the new hook; the theme fix order prefers hooks.
