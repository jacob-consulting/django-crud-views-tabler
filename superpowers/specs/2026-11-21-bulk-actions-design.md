# Bulk actions in the CoreUI and Tabler themes: design

Date: 2026-11-21. The same document is committed to both repos (`django-crud-views-core-ui` and `tabler-test`, which
is `django-crud-views-tabler`) on branch `feature/bulk-actions`.

## Intent

django-crud-views #392 (merge `75a42851`) added current-page bulk selection and bulk action forms. The AdminLTE theme
(`../PythonProject/django-crud-views-adminlte`, commit `99d5f4e`) was the first sibling built after it and carries
bulk in its demo and its theme tests. The CoreUI and Tabler themes have no bulk code yet.

Why: the three sibling themes exist to find where django-crud-views is hard to theme before its 1.0 release. Bulk is
the newest upstream feature, so it is the one most likely to still have theming gaps, and it has only been tried
under one page shell. Bringing it to the other two shows which gaps are general and which were AdminLTE's.

## Goals

- The same bulk demo in all three Acme Roasters apps: on `/orders/` (all orders), a table view and a card view with
  "Mark roasted" (`bulk_roast`) and "Cancel orders" (`bulk_cancel`, with a required reason), each running the order's
  django-fsm transition through `crud_views_workflow`'s `run_transition`, as AdminLTE's
  `example/sales/views/order_bulk.py` and `example/sales/views/orders.py` do.
- Bulk looks native in each kit: the toolbar, the select-all checkbox (including its indeterminate state), the row and
  card checkboxes and the action buttons, at desktop width and at 375px.
- Each theme's test suite proves the theme's part: a theme `test_bulk.py` modelled on AdminLTE's
  `tests/crud_views_adminlte/test_bulk.py` (with a small bulk view in the theme testapp), and the demo's
  `example/sales/tests/test_bulk.py` copied over.
- What is found goes into each repo's own upstream log, cross-referenced with the AdminLTE tracker.

## Non-goals

- No bulk feature beyond the AdminLTE demo (no new actions, no bulk on other ViewSets, no select-across-pages).
- No shared demo module between the three repos; each keeps its own copy.
- No upstream change. django-crud-views and django-crud-views-extensions stay read-only; gaps are worked around and
  logged.
- No push, no PR without the user's go.

## Anti-goals

- The copies drift: a demo whose actions, labels, permissions or tests differ from AdminLTE's without a logged
  reason defeats the side-by-side comparison.
- Re-filing what is already known: C10 (toolbar shows every action to every viewer) and C11 (no danger variant for
  bulk buttons) from the AdminLTE tracker are general upstream gaps; the siblings cross-reference them instead of
  opening new IDs for the same thing.
- Restating upstream defaults as theme code with no reason: AdminLTE's seven `bulk:*` keys equal crud_views'
  defaults. A sibling sets a `bulk:*` key only where its kit's markup needs a different value.

## Constraints

- Each repo's own conventions (its `CLAUDE.md`) bind: tracker rule, comment format at workarounds, ruff, test
  commands, Taskfile.
- CoreUI logs in `superpowers/notes/upstream-tracker.md` with `U<n>` IDs (next free: U13). Tabler has no tracker file;
  it logs in `dev/crud_views_upstream_status.md` as a dated `## Update 2026-11-21: bulk actions, upstream 75a42851`
  section, in that file's prose style.
- Both repos run crud_views `@main` in nox and the local editable `../django-crud-views` at `75a42851` in development.
- Both repos override `crud_views/table/bootstrap5.html` already (CoreUI extends upstream's; Tabler's wraps it in
  `card table-container` + `table-responsive`). The bulk select column must render through those overrides; whether
  AdminLTE's 375px fix (C9) is needed depends on each override.
- Icons: both demos already map `roasted` and `cancelled` in `example/config/icons.py`.
- The demos' `Order` models match AdminLTE's except Tabler's `steps()` display helper, which bulk does not use.
- `BulkSelectionMixin` goes before `ListViewTableMixin` (whose `get_table_kwargs` does not call `super()`), as in
  AdminLTE's `AllOrdersListView`.

## Approaches

1. **Full port per repo (chosen).** Copy the demo; set `bulk:*` keys or CSS only where the kit needs them; a theme
   `test_bulk.py`; a browser pass at desktop and 375px; log findings in each repo's format with cross-references to
   C9/C10/C11. Keeps the three comparable and still catches per-shell differences.
2. **Demo only.** Copy the demo, rely on upstream defaults, no theme tests or browser pass. Cheaper, but skips the
   part that finds theming weaknesses, which is why the siblings exist.
3. **Shared demo module.** Factor the bulk demo into something the three repos share. Cleaner long term, but adds
   coupling the three projects have avoided so far.

The user picked approach 1 and a straight copy of the demo.

## Decided

- Straight copy of AdminLTE's bulk demo: `order_bulk.py` (both views, the cancel form, the transition mixin),
  the `orders.py` changes (`AllOrdersScopeMixin`, `BulkSelectionMixin` on the list, the new `AllOrdersCardView` with
  `sales/order_card.html`, the `list`/`card` context actions, `ALL_ORDERS_BULK_ACTIONS`), the `views/__init__.py`
  registration, the demo tests. Kit-specific markup in `order_card.html` follows the kit's card conventions; text,
  actions, permissions and behaviour stay the same.
- CoreUI first, then Tabler; one feature branch `feature/bulk-actions` per repo.
- One plan covering both repos.
- (My call) Where a theme's own template override drops or breaks bulk markup (for example Tabler's
  `crud_views/view_card.content.html` or `crud_views/tags/card.html` replacing the grid wrapper that renders the card
  checkboxes), the theme fixes its override, logs it in that repo's format and pins it with a theme test. The
  override belongs to the theme, so fixing it is not an upstream workaround.
- (My call) The browser pass is done on `/orders/` table and cards, logged in as `alex` and `kim`, at desktop width
  and 375px: checkboxes and select-all (none, some, all selected) are visible and styled, both actions submit, and at
  375px `document.documentElement.scrollWidth` equals the viewport width (the C9 measurement). The results go into
  the repo's upstream log; screenshots are not kept.

## Left to the builder

- Which `bulk:*` keys, if any, each kit needs, and any theme CSS (for example the indeterminate select-all colour,
  which AdminLTE's demo styles in `example/static/acme/acme.css`).
- The shape of each theme testapp's bulk view, modelled on AdminLTE's `tests/crud_views_adminlte/testapp/views_bulk.py`.
- Whether each theme's docs (`docs/`) need a bulk section; AdminLTE documents its bulk keys in
  `docs/theme_internals.md`.
- Adapting copied tests to each demo's existing helpers and fixtures, keeping their assertions.
