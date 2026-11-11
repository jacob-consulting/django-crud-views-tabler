# Compact Order Lines Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render order lines with shared desktop headings and labelled mobile cards while preserving the custom product select and coffee-only fields.

**Architecture:** Mark `ProductSelect` as compatible with upstream compact formsets, then give the existing order-line declaration the 4 + 2 + 2 + 2 + 2 layout. Upstream owns rendering; `sales.js` and server cleaning retain their current behavior.

**Tech Stack:** Django, django-crud-views at PR #350 or later, django-crispy-forms, Tabler.

**Spec:** `docs/superpowers/specs/2026-11-11-adopt-compact-order-lines-design.md`

## Global Constraints

- Change only `ORDER_FORMSETS["lines"]` and `ProductSelect` for compact adoption; preserve field order and spans 4, 2, 2, 2, controls 2.
- Preserve `data-beans` on coffee options, coffee-only grind and bag-size behavior, validation, saving, and add/delete controls.
- Do not edit the upstream checkout or broaden widget compatibility beyond `ProductSelect`.
- Update finding 34 with adoption and actual verification. Add theme CSS only for a reproduced mismatch.

## Review Focus

- Blank create form: compact metadata and one heading strip render without evaluating product choices prematurely.
- Saved order update: product options retain `data-beans` and labels remain associated with prefixed inputs.
- Invalid quantity POST: compact rows retain field errors and entered values.
- Dynamically added line: the new row retains select metadata and the coffee-only controls respond to product changes.
- Equipment selection: grind and bag size disable in the browser and are cleared on the server if posted anyway.

---

### Task 1: Adopt and verify compact order lines

**Files:**
- Modify: `example/sales/forms.py`
- Test: `example/sales/tests/test_orders.py`
- Modify: `docs/crud_views_upstream_findings_roastery.md`
- Conditional modify: `src/crud_views_tabler/static/crud_views_tabler/crud_views_tabler.css` for a reproduced Tabler mismatch only

**Interfaces:**
- Consumes: `CompactWidgetCompatible`, `CompactColumn(field: str, *, span: int)`, `CompactLayout(columns, *, controls_span: int)`, and `FormSet.compact_layout` from `crud_views.lib.formsets`.
- Produces: `ProductSelect(CompactWidgetCompatible, forms.Select)` and compact `ORDER_FORMSETS["lines"]`; no new public API.

- [x] **Step 1: Write failing rendered-page tests.** In `OrderFormTests`, assert create and update GET each have one `.cv-formset-compact-headings` and compact rows with associated product/quantity labels; assert a coffee option has `data-beans="1"`; assert an invalid quantity POST redisplays its error in a compact row. Keep the existing persistence and equipment-cleaning tests.
- [x] **Step 2: Verify the red test.** Run `uv run python example/manage.py test sales.tests.test_orders.OrderFormTests`; expect the new compact markup assertions to fail.
- [x] **Step 3: Implement the declaration.** Import the three upstream compact types; inherit `CompactWidgetCompatible` before `forms.Select` in `ProductSelect`. Add `CompactLayout` with columns `product` span 4, `grind` span 2, `bag_size` span 2, `quantity` span 2, and `controls_span=2` to the `lines` declaration. Remove its obsolete `form_show_labels=True` and `get_helper_layout_fields()` override.
- [x] **Step 4: Verify the green test and project check.** Run `uv run python example/manage.py test sales.tests.test_orders.OrderFormTests` and `uv run python example/manage.py check --fail-level WARNING`; expect both to pass.
- [x] **Step 5: Inspect the page in a browser.** Check create/update at desktop and mobile widths, an invalid quantity, add/delete controls, and changing a new row from coffee to equipment and back. Confirm the new row's options retain `data-beans`. Add narrowly scoped Tabler CSS only if a mismatch is visible, then repeat the affected check.
- [x] **Step 6: Update the tracker.** Mark finding 34 adopted, citing upstream #349 / PR #350 and recording the checks actually performed. Remove the stale order-line limitation from finding 22.
- [x] **Step 7: Final verification and commit.** Run `uv run python example/manage.py test sales` and `git diff --check`; expect passing tests and no whitespace errors. Commit the changed task files.
