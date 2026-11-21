# Adopt upstream fixes and updates (2026-11-21) — short design

**Status:** approved by the maintainer on 2026-11-21. Branch `feature/upstream-sync` (from `feature/bulk-actions`).

## Intent

Keep the theme and the demo in step with today's upstream work in the sibling checkouts: django-crud-views #391, #393
and #394 (PRs #395–#397), and django-crud-views-extensions 0.4.0 (#6). Drop the workarounds they make unnecessary and
log every change in `dev/`. Bulk selection (#392) was adopted earlier on `feature/bulk-actions`.

## Goals

- Green suites again: upstream #394 adds `gx-3` to the compact formset rows, so three example tests fail
  (`roastery/tests.py` cupping headings, `sales/tests/test_orders.py` order lines) because they match the exact
  string `class="row cv-formset-compact-headings"`.
- Replace the theme's `--bs-*` re-definitions with one `--cv-*` token mapping.
- Bring findings 31 and 35 and the status notes up to date.

## Non-goals

- New features from #391 (data-attribute prefix): Tabler uses `bs`, the default, so there's nothing to do.
- Breadcrumb class keys (#393): the theme has no breadcrumb workaround.
- Removing the theme's `table/bootstrap5.html` override: it stays for the card layout. It already renders `aria-sort`
  from the bound column, as upstream now does.

## Approaches

Only one approach made sense: map the tokens upstream documents (`docs/reference/theme.md#css-tokens`) on Tabler's
theme roots. Keeping the scoped `--bs-*` blocks would still work through the fallback chains. But it ties the theme
to upstream's selector list, which is the problem #394 fixes. Overriding templates goes against the fix order in
CLAUDE.md.

## Design

- `crud_views_tabler.css`: a single `:root, [data-bs-theme] { --cv-* : var(--tblr-*) }` block covering upstream's
  six tokens (`secondary-color`, `secondary-text-emphasis`, `body-bg`, `border-color`, `border-radius`,
  `tertiary-bg`) and the typeahead's (`border-color-translucent`, `highlight-bg`). It replaces the `--bs-*` blocks
  on `.cv-formset-compact`, `.cv-typeahead, .cv-typeahead-select` and `[data-cv-manage]`. Before using
  `--tblr-tertiary-bg`, check that Tabler 1.6.1 defines it.
- Remove the `--tblr-gutter-x: 1rem` rule on the compact rows if Tabler's `gx-3` already produces that value. Keep it
  only if the browser shows otherwise.
- Keep: the typeahead dropdown shadow, `display: block` on its items, and `manage:help` = `btn btn-sm`. The help
  button doesn't use the stock `.btn-outline-secondary` class, so upstream's help-button contrast rule doesn't apply.
- Tests: the three failing example tests match the classes, not the whole attribute. Theme tests check the token
  mapping and that the old `--bs-*` blocks are gone.
- Logs: findings 31 and 35 and the summary table in `dev/crud_views_upstream_findings_roastery.md`; a line in
  `dev/crud_views_upstream_status.md` noting #391/#393 needed no change. Commit `uv.lock` (extensions 0.4.0).
- Verify: every suite (`task test`), `manage.py check --fail-level WARNING`, and a browser pass in light and dark
  mode over the manage page, cupping and order-line formsets, and the typeahead popup.

## Left to the builder

- The exact selector list for the theme roots, if Tabler sets `data-bs-theme` on elements other than `<html>`.
- Whether the token tests read the CSS file or the rendered page.
