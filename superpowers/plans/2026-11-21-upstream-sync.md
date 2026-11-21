# Upstream sync (2026-11-21) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adopt django-crud-views #391/#393/#394 and django-crud-views-extensions 0.4.0 in the Tabler theme: get the suites green again, replace the `--bs-*` re-definitions with one `--cv-*` token mapping, and update the logs.

**Architecture:** CSS only in `src/crud_views_tabler/static/crud_views_tabler/crud_views_tabler.css`, plus test and `dev/` updates. No template overrides and no Python API changes.

**Tech Stack:** Django, django-crud-views (sibling checkout), Tabler 1.6.1 CSS (`--tblr-*`), pytest / pytest-django.

**Spec:** `superpowers/specs/2026-11-21-upstream-sync-design.md`

## Global Constraints

- Branch `feature/upstream-sync`. Every theme CSS rule change gets an entry in `dev/crud_views_upstream_findings_roastery.md` in the same commit (CLAUDE.md).
- The theme must not import django-crud-views-extensions; the typeahead mapping stays plain CSS.
- Upstream's token names, verbatim: `--cv-secondary-color`, `--cv-secondary-text-emphasis`, `--cv-body-bg`, `--cv-border-color`, `--cv-border-radius`, `--cv-tertiary-bg`; typeahead (extensions 0.4.0): `--cv-border-color-translucent`, `--cv-highlight-bg` (plus the shared `--cv-secondary-color`, `--cv-body-bg`, `--cv-border-radius`).
- Tabler 1.6.1 defines all source properties: `--tblr-secondary-color`, `--tblr-secondary-text-emphasis`, `--tblr-bg-surface`, `--tblr-border-color`, `--tblr-border-radius`, `--tblr-tertiary-bg`, `--tblr-border-color-translucent`, `--tblr-highlight-bg` (verified against the CDN CSS). Tabler's `.gx-3` is `--tblr-gutter-x:1rem`.
- Run suites with `-n auto`. Lint: `uv run ruff format . && uv run ruff check .`.

## Review Focus

1. **Nested dark section:** the example's dark sidebar/navbar (`data-bs-theme="dark"` on a sub-element) must resolve tokens against its own mode. Mapping on `:root, [data-bs-theme]` covers this; the Task 1 test pins the selector.
2. **Body background on formset rows:** upstream's row card uses `--cv-body-bg`. Map it to `--tblr-bg-surface` (the card surface), not `--tblr-body-bg`, or the rows look like holes in the card. Pinned in Task 1.
3. **Typeahead popup still opaque** after its `--bs-*` block goes (the original finding 31 symptom). Pinned by asserting `--cv-body-bg` is in the root mapping and the popup's shadow and `display: block` rules stay. Checked in the browser in Task 3.
4. **Compact row gutter unchanged at 1rem** once the theme's rule is gone: upstream's `gx-3` sets it. Task 1 asserts the rule is gone; Task 3 checks it in the browser.
5. **Manage help button contrast:** `manage:help` stays `btn btn-sm` (not `.btn-outline-secondary`), so upstream's Bootstrap-only contrast rule doesn't apply. Task 1 asserts the registry value is unchanged.

---

### Task 1: Token mapping in the theme CSS, theme tests

**Files:**
- Modify: `src/crud_views_tabler/static/crud_views_tabler/crud_views_tabler.css:51-82` (the `.cv-formset-compact`, compact gutter, `.cv-typeahead, .cv-typeahead-select` and `[data-cv-manage]` blocks)
- Test: `tests/crud_views_tabler/test_theme.py` (`BareTableTests`, ~line 856-877)
- Modify: `dev/crud_views_upstream_findings_roastery.md` (findings 31 and 35 and their summary rows; the "Status" line of each points to upstream #394 / ext #6, and "What we did" describes the token mapping)

**Interfaces:**
- Produces: a single CSS block with the selector `:root,\n[data-bs-theme]` that declares the eight `--cv-*` tokens.

- [ ] **Step 1: Write the failing tests** in `BareTableTests` (read the CSS the way the neighbouring tests do):
  - `test_tokens_map_tabler_properties_on_theme_roots`: regex `:root,\s*\[data-bs-theme\] \{` followed by a body (`[^}]*`). The body contains each of these pairs: `--cv-secondary-color: var(--tblr-secondary-color)`, `--cv-secondary-text-emphasis: var(--tblr-secondary-text-emphasis)`, `--cv-body-bg: var(--tblr-bg-surface)`, `--cv-border-color: var(--tblr-border-color)`, `--cv-border-radius: var(--tblr-border-radius)`, `--cv-tertiary-bg: var(--tblr-tertiary-bg)`, `--cv-border-color-translucent: var(--tblr-border-color-translucent)`, `--cv-highlight-bg: var(--tblr-highlight-bg)`.
  - `test_no_bootstrap_property_redefinitions_remain`: `assertNotRegex(css, r"--bs-[a-z-]+:")`; `assertNotIn("--tblr-gutter-x: 1rem", css)`; `assertIn(".cv-typeahead-select-popup", css)`; `TABLER_BUTTON_CLASSES["manage:help"] == "btn btn-sm"`.
  - Delete `test_manage_page_reads_tabler_secondary_colours`, and the `--bs-body-bg` assertion in `test_workflow_no_longer_scrolls_the_whole_content_container`. The new tests supersede both.
- [ ] **Step 2: Run them to see them fail:** `uv run pytest tests/crud_views_tabler/test_theme.py --ds tests.crud_views_tabler.settings -k "tokens_map or no_bootstrap_property"`. Expected: 2 failures.
- [ ] **Step 3: Edit the CSS.** Replace the four blocks with the root mapping. Its comment: upstream #394 and extensions 0.4.0 read `--cv-*` tokens; they are declared on every theme root so nested dark sections resolve on their own; and Tabler's `gx-3` gives the 1rem gutter upstream now adds. Keep the shadow and dropdown-item rules unchanged.
- [ ] **Step 4: Run the theme suite:** `uv run pytest -n auto tests/crud_views_tabler --ds tests.crud_views_tabler.settings`. Expected: all pass.
- [ ] **Step 5: Update findings 31/35** (the entries and the summary table rows), then commit: `git add src tests dev && git commit -m "feat: map upstream --cv-* CSS tokens (#394, ext 0.4.0), drop --bs-* re-definitions"`.

### Task 2: Example tests follow upstream's `gx-3` rows; lockfile

**Files:**
- Modify: `example/roastery/tests.py:85`, `example/sales/tests/test_orders.py:90`
- Modify: `dev/crud_views_upstream_status.md` (a new "Update 2026-11-21: upstream #391, #393, #394, ext 0.4.0" section above the bulk-actions one; one bullet each. #391: Tabler uses `bs`, nothing to do. #393: no breadcrumb workaround; the theme's table override already renders `aria-sort` from the bound column and stays for the card layout. #394 / ext 0.4.0: see findings 31/35. The `gx-3` row class broke three exact-class assertions in the example)
- Commit: `uv.lock` (extensions 0.4.0)

- [ ] **Step 1: Confirm the failure:** `cd example && uv run pytest -n auto`. Expected: 3 failures, `0 != 1` on `class="row cv-formset-compact-headings"`.
- [ ] **Step 2: Change both assertions** so they count the headings row by its classes. Use `assertEqual(len(re.findall(r'class="[^"]*\bcv-formset-compact-headings\b[^"]*"', html)), 1)` (import `re` if missing), with `create_html` in the roastery test and `html` in the order test.
- [ ] **Step 3: Run:** `cd example && uv run pytest -n auto`. Expected: all pass.
- [ ] **Step 4: Write the status update,** then commit: `git add example dev uv.lock && git commit -m "test(example): match compact headings by class after upstream gx-3; status for #391/#393/#394"`.

### Task 3: Full verification and browser pass

- [ ] **Step 1:** `task test`. Expected: every suite passes, check clean. `uv run python example/manage.py check --fail-level WARNING`. Expected: no issues. `uv run ruff format --check . && uv run ruff check .`. Expected: clean.
- [ ] **Step 2: Browser,** as `alex`, light and dark (layout switch): the manage page (header colour and dimmed default rows readable in dark mode), cupping create (compact score rows: surface background, border, 1rem gutter), order create (line rows, customer typeahead popup opaque, with border and highlight), and the dark sidebar. Use DevTools to compare the computed `--tblr-gutter-x` on `.cv-formset-compact-fields` (`1rem`) and the row card's `background-color` with the card's.
- [ ] **Step 3:** If the browser pass needs a fix, make it test-first under Task 1's pattern, log it in the findings file, and commit.
