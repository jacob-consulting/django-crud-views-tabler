# Bulk actions in the CoreUI and Tabler themes: implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the AdminLTE theme's bulk-action demo and theme coverage (django-crud-views #392) to the CoreUI and
Tabler themes, unchanged in behaviour, native in look, with findings logged per repo.

**Architecture:** Two repos, one feature branch `feature/bulk-actions` in each (already created, design committed).
Per repo: a theme task (a bulk ViewSet in the theme testapp, a theme `test_bulk.py`, `bulk:*` keys or CSS only where
the kit needs them, the log) and a demo task (the AdminLTE demo copied, its tests, a browser pass). CoreUI first
(Tasks 1-2), then Tabler (Tasks 3-4).

**Tech Stack:** Django 6.1 / Python 3.15 locally, django-crud-views at `75a42851` (editable `../django-crud-views`),
crud_views_workflow + django-fsm, django-tables2, crispy-forms, pytest-django + xdist, lxml, uv, Task,
chrome-devtools MCP for the browser pass.

**Spec:** `superpowers/specs/2026-11-21-bulk-actions-design.md` (same file in both repos).

**Repos:**
- CoreUI: `/home/alex/projects/alex/django-crud-views-core-ui` (theme package `src/crud_views_coreui`, tests
  `tests/crud_views_coreui`, log `superpowers/notes/upstream-tracker.md`, `U<n>` IDs, next free U13).
- Tabler: `/home/alex/projects/alex/tabler-test` (theme package `src/crud_views_tabler`, tests
  `tests/crud_views_tabler`, log `dev/crud_views_upstream_status.md`).
- Reference (read-only): AdminLTE `/home/alex/projects/alex/PythonProject/django-crud-views-adminlte`, commit
  `99d5f4e` (`git -C <adminlte> show 99d5f4e` shows the whole bulk change). Upstream (read-only):
  `/home/alex/projects/alex/django-crud-views` at `75a42851`.

## Global Constraints

- Straight copy of the AdminLTE demo: same actions (`bulk_roast` "Mark roasted", `bulk_cancel` "Cancel orders" with a
  required reason), same labels, permissions (`roast` for roast, `change` for cancel), views (`/orders/` table and
  cards), `ALL_ORDERS_BULK_ACTIONS = ("bulk_roast", "bulk_cancel")`, same demo test names and assertions. A deviation
  needs a logged reason.
- Both repos' pre-bulk `example/sales/views/orders.py` are byte-identical to AdminLTE's at `5c6d5a6`, so AdminLTE's
  `git diff 5c6d5a6 99d5f4e -- example/sales/views/orders.py` applies as is.
- `BulkSelectionMixin` goes before `ListViewTableMixin` (its `get_table_kwargs` does not call `super()`).
- Set a `bulk:*` key only where the kit needs a value other than crud_views' default (AdminLTE's seven keys equal the
  defaults; there they are restated only because AdminLTE's `buttons.py` lists every key).
- C10 (toolbar shows every action to every viewer) and C11 (no danger variant for bulk buttons) are known upstream
  gaps from the AdminLTE tracker: cross-reference them, do not open new IDs for them. Same for C9 (bare
  `.table-container`), if the kit's table override already solves it say so.
- Each repo's `CLAUDE.md` binds: its tracker rule (entry in the same commit as the workaround), comment style at the
  workaround, ruff (`uv run ruff format . && uv run ruff check .`), `unset VIRTUAL_ENV` before uv, `pytest -n auto`.
- `../django-crud-views` and `../django-crud-views-extensions` are read-only. App code in `example/` never imports the
  theme package.
- Demo accounts `alex` / `sam` / `kim`, password `demo`; kim is in Roasters (`roast_order`, no `change_order`).
- No push, no PR, no merge: commits on `feature/bulk-actions` only.
- Baseline (2026-11-21, before this plan) `task test`: CoreUI 37 / 135 / 87 / 256 passed, check clean; Tabler
  36 / 97 / 36 / 273 passed, check clean. Every task ends with `task test` green in its repo.

## Review Focus

1. **Card checkboxes and the toolbar form.** Row and card checkboxes post through `form="{{ view.cv_bulk_form_id }}"`;
   inside a theme's card/table wrapper the attribute must still name the toolbar's `<form>` on the same page. Pinned by
   `test_bulk_checkboxes_point_at_the_toolbar_form` (Tasks 1, 3).
2. **Tabler's card grid override drops bulk.** `crud_views/view_card.content.html` in Tabler has no toolbar include
   and no card checkbox; the card view must show both, and the copied markup must stay upstream's. Pinned by
   `test_bulk_card_view` and `test_card_bulk_markup_is_upstreams` (Task 3).
3. **Narrow screens.** The select column widens the orders table; at 375px the page must not scroll sideways
   (`document.documentElement.scrollWidth == 375`). Checked in the browser pass (Tasks 2, 4) and, where a theme
   needs CSS for it, by a theme test.
4. **A prefixed table.** A table with `Meta.prefix` (sort parameter `a-sort`) keeps the select column and the toolbar;
   the theme testapp's bulk table is prefixed, as AdminLTE's is (Tasks 1, 3).
5. **An empty list.** With no rows the table and card views still render without error and offer no checkboxes;
   Tabler's empty state stays. Pinned by `test_bulk_empty_list` (Tasks 1, 3).

---

### Task 1: CoreUI theme: bulk coverage

**Files (CoreUI repo):**
- Create: `tests/crud_views_coreui/testapp/views_bulk.py`, `tests/crud_views_coreui/test_bulk.py`
- Modify: `tests/crud_views_coreui/testapp/urls.py`; if needed `src/crud_views_coreui/buttons.py`,
  `src/crud_views_coreui/static/crud_views_coreui/crud_views_coreui.css`; `docs/theme_internals.md`;
  `superpowers/notes/upstream-tracker.md`

**Interfaces:**
- Consumes: the testapp's `Customer` model (`name`, `country`); crud_views `BulkSelectionMixin`,
  `BulkFormViewPermissionRequired` (`crud_views.lib.bulk`), `CardListViewPermissionRequired`.
- Produces: ViewSet `cv_bulk_customer` (name `bulk_customer`, prefix `bulk-customer`) with views `list` (prefixed
  table `Meta.prefix = "c-"`, actions `clear_country`, `set_country`), `card` (action `clear_country`),
  `clear_country` (no input, blocks customers with no country: "No country to clear."), `set_country` (form with
  `country`, message "Country set for N customers."). Same shape as AdminLTE's
  `tests/crud_views_adminlte/testapp/views_bulk.py` with Author → Customer; icons through the repo's own icon library.

- [ ] **Step 1: Write the failing tests** in `tests/crud_views_coreui/test_bulk.py`, porting AdminLTE's
  `tests/crud_views_adminlte/test_bulk.py` test by test, in this repo's test style (match `test_theme.py`):
  `test_bulk_toolbar`, `test_bulk_card_view`, `test_bulk_form_page_renders`, `test_bulk_form_page_all_blocked`,
  `test_bulk_form_page_with_input`, `test_bulk_result_message_through_host`, `test_bulk_default_message_through_host`,
  `test_bulk_empty_selection_warning_through_host`. Assertions on classes read the resolved value
  (`get_button_class("bulk", "<slot>")`), not literals, so they hold whether or not the theme sets the key; where the
  AdminLTE test asserts AdminLTE markup (host message partial, card classes), assert CoreUI's equivalent. Add:
  - `test_bulk_checkboxes_point_at_the_toolbar_form`: on list and card pages every `input[data-cv-bulk-item]`'s
    `form` attribute equals the `id` of exactly one `<form>` in the page.
  - `test_bulk_table_inside_coreui_card`: the list page's select column sits inside `.card.cv-coreui-table`, the
    header row has the select-all control and each body row one `input[data-cv-bulk-item]`.
  - `test_bulk_empty_list`: with no customers, list and card pages answer 200 and contain no `[data-cv-bulk-item]`.
- [ ] **Step 2: Run them; expected FAIL** (no `bulk-customer` URLs):
  `uv run pytest tests/crud_views_coreui/test_bulk.py --ds tests.crud_views_coreui.settings`
- [ ] **Step 3: Add `views_bulk.py`** and append `cv_bulk_customer.urlpatterns` to `testapp/urls.py`.
- [ ] **Step 4: Run them; fix the theme where they show a CoreUI gap.** Any `bulk:*` key goes into `buttons.py` with
  a one-line reason; any CSS into `crud_views_coreui.css` with a comment naming its tracker ID. Run:
  `uv run pytest -n auto tests/crud_views_coreui --ds tests.crud_views_coreui.settings`; expected all pass (135 + new).
- [ ] **Step 5: Docs and log.** `docs/theme_internals.md`: a short "Bulk actions" section (which keys the theme
  sets, or that it uses upstream's defaults; how the select column sits in the table card). Tracker: a new U13+
  entry per new CoreUI finding in the file's format; a short note under the close-out or a new "Bulk actions
  (2026-11-21, upstream 75a42851)" section that C9/C10/C11 of the AdminLTE tracker apply here as well (state
  whether CoreUI's `table-responsive` already covers C9).
- [ ] **Step 6: Verify and commit.** `uv run ruff format . && uv run ruff check .`, `task test` green.
  `git commit -m "feat: bulk selection under CoreUI (theme tests, docs, tracker)"`

### Task 2: CoreUI demo: bulk orders and browser pass

**Files (CoreUI repo):**
- Create: `example/sales/views/order_bulk.py`, `example/sales/templates/sales/order_card.html`,
  `example/sales/tests/test_bulk.py`
- Modify: `example/sales/views/orders.py`, `example/sales/views/__init__.py`, `example/static/acme/acme.css` (if
  the indeterminate select-all needs the brand colour, as in AdminLTE), `docs/demo.md` (orders row: bulk actions),
  `superpowers/notes/upstream-tracker.md`

**Interfaces:**
- Consumes: Task 1's findings (nothing in code); the demo's `customers_for`, `BreadcrumbMixin`, `OrderTestCase`
  (`example/sales/tests/test_orders.py`), `cv_all_orders`.
- Produces: `/orders/` table and card views with the two bulk actions.

- [ ] **Step 1: Copy the demo tests.** `example/sales/tests/test_bulk.py` from AdminLTE unchanged except for
  imports and helpers this demo names differently: `test_list_offers_the_two_actions`,
  `test_card_view_offers_the_actions`, `test_roast_runs_the_transition_when_all_are_confirmed`,
  `test_roast_shows_blocked_orders`, `test_cancel_asks_for_a_reason`, `test_roasters_may_not_cancel`,
  `test_sam_cannot_touch_other_customers_orders`.
- [ ] **Step 2: Run them; expected FAIL** (no bulk views): `cd example && uv run pytest sales/tests/test_bulk.py`
- [ ] **Step 3: Copy the views.** `order_bulk.py` from AdminLTE (adjust only its module docstring if it names
  AdminLTE); apply the `orders.py` diff (`git -C <adminlte> diff 5c6d5a6 99d5f4e -- example/sales/views/orders.py`);
  the `__init__.py` import line. `order_card.html` keeps AdminLTE's content (fields, order, wording) with CoreUI's card
  markup conventions.
- [ ] **Step 4: Run the demo suite:** `cd example && uv run pytest -n auto`; expected 256 + 7 passed. Then
  `uv run python example/manage.py check --fail-level WARNING` clean. If an existing test trips (for example a test
  that lists context actions on `/orders/`), update it to the new actions and say so in the report.
- [ ] **Step 5: Browser pass** (per the spec's "browser pass" call): `task up` (or `task setup` + runserver on a free
  port), chrome-devtools MCP. `/orders/` as table and as cards, as `alex` and as `kim`, at 1280px and 375px:
  checkboxes and select-all visible and styled in none/some/all states (indeterminate uses the brand colour), "Mark
  roasted" submits and moves confirmed orders to roasted, "Cancel orders" asks for the reason and cancels, kim's
  "Cancel orders" answers 403 (C10), at 375px `document.documentElement.scrollWidth === 375` on both views. Fix what
  fails in the theme or the demo CSS (each fix logged); record the results (pass/fail per check, measurements) in the
  tracker's bulk section. No screenshots kept.
- [ ] **Step 6: Verify and commit.** ruff, `task test` green.
  `git commit -m "feat(example): bulk order actions, as in the AdminLTE demo"`

### Task 3: Tabler theme: bulk coverage and the card grid override

**Files (Tabler repo):**
- Create: `tests/crud_views_tabler/testapp/views_bulk.py`, `tests/crud_views_tabler/test_bulk.py`
- Modify: `src/crud_views_tabler/templates/crud_views/view_card.content.html`,
  `tests/crud_views_tabler/testapp/urls.py`; if needed `src/crud_views_tabler/buttons.py` (or wherever the theme's
  button classes live; see `apps.py`), `src/crud_views_tabler/static/crud_views_tabler/crud_views_tabler.css`;
  `docs/theme_internals.md` (the overrides table and a "Bulk actions" section); `dev/crud_views_upstream_status.md`

**Interfaces:**
- Consumes: the testapp's `Customer`; same crud_views API as Task 1.
- Produces: `cv_bulk_customer` with the same shape as Task 1's (copy CoreUI's `views_bulk.py`, Tabler icon names).

- [ ] **Step 1: Write the failing tests** in `tests/crud_views_tabler/test_bulk.py`: the same tests as Task 1
  (CoreUI's `test_bulk.py` is the template; Tabler markup in place of CoreUI's, `test_bulk_table_inside_coreui_card`
  becomes `test_bulk_table_inside_tabler_card` against Tabler's `card table-container` / `table-responsive`
  wrapper), plus:
  - `test_card_bulk_markup_is_upstreams`: the bulk toolbar include and the card-cell block (`{% if view.cv_bulk_actions %}<div class="{% cv_button_class 'bulk' 'card-cell' %}">` … `{% else %}{% cv_card object %}{% endif %}`)
    in the theme's `view_card.content.html` equal the corresponding text of the installed upstream
    `crud_views/view_card.content.html` (read both files; compare the extracted fragments, whitespace-normalised), so
    an upstream change to the bulk card markup fails the suite.
  - `test_bulk_card_view` must assert the toolbar and one `[data-cv-bulk-item]` per card inside `.row-deck`.
- [ ] **Step 2: Run them; expected FAIL** (no URLs; then, after Step 3, the card tests fail on the override):
  `uv run pytest tests/crud_views_tabler/test_bulk.py --ds tests.crud_views_tabler.settings`
- [ ] **Step 3: Add `views_bulk.py`** and its urlpatterns.
- [ ] **Step 4: Fix the override.** In `view_card.content.html` add upstream's toolbar include after the
  `card_order.html` include and wrap `{% cv_card object %}` in upstream's card-cell markup, keeping
  `row row-deck row-cards` and the Tabler empty state. Update the template's header comment to say which parts are
  upstream's copied bulk markup and which test guards them.
- [ ] **Step 5: Run the theme suite; fix Tabler gaps** as in Task 1 Step 4:
  `uv run pytest -n auto tests/crud_views_tabler --ds tests.crud_views_tabler.settings`; expected all pass (97 + new).
- [ ] **Step 6: Docs and log.** `docs/theme_internals.md`: overrides table line for `view_card.content.html` gains
  "bulk toolbar and card checkbox (upstream's, guarded by `test_card_bulk_markup_is_upstreams`)", plus a "Bulk
  actions" section as in CoreUI. `dev/crud_views_upstream_status.md`: a new top section
  `## Update 2026-11-21: bulk actions, upstream 75a42851` in the file's prose style: the card grid finding (upstream's
  `view_card.content.html` has no block for the card cell, so a theme that restyles the grid must copy the bulk
  markup; possible fix: a `card_cell` block or an include for the checkbox), C9/C10/C11 cross-referenced to the
  AdminLTE tracker, and any further Tabler finding.
- [ ] **Step 7: Verify and commit.** ruff, `task test` green.
  `git commit -m "feat: bulk selection under Tabler (card grid override, theme tests, docs, log)"`

### Task 4: Tabler demo: bulk orders and browser pass

**Files (Tabler repo):** as Task 2, in the Tabler repo; the log is `dev/crud_views_upstream_status.md`
(the bulk section from Task 3).

**Interfaces:**
- Consumes: CoreUI's Task 2 files as the template (they are AdminLTE's, already adapted to a sibling layout).
- Produces: `/orders/` table and card views with the two bulk actions in the Tabler demo.

- [ ] **Step 1: Copy the demo tests** (CoreUI's `example/sales/tests/test_bulk.py`; same seven tests).
- [ ] **Step 2: Run them; expected FAIL:** `cd example && uv run pytest sales/tests/test_bulk.py`
- [ ] **Step 3: Copy the views** (`order_bulk.py`, the `orders.py` change, `__init__.py`), and `order_card.html` with
  Tabler card markup and the same content.
- [ ] **Step 4: Run the demo suite:** `cd example && uv run pytest -n auto`; expected 273 + 7 passed; check clean.
- [ ] **Step 5: Browser pass** as Task 2 Step 5, against the Tabler demo; results into the Tabler log's bulk
  section.
- [ ] **Step 6: Verify and commit.** ruff, `task test` green.
  `git commit -m "feat(example): bulk order actions, as in the AdminLTE demo"`
