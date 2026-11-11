# Compact Cupping Formset Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show shared headings for cupping scores on desktop and labelled score cards on mobile using upstream compact formsets.

**Architecture:** Opt only the cupping score `FormSet` into `CompactLayout` with the existing 3 + 7 + 2 grid spans. Let upstream render rows and headings; retain Tabler theme conventions and add CSS only if inspection finds a concrete mismatch.

**Tech Stack:** Django, django-crud-views editable checkout at #348 or later, django-crispy-forms, Tabler.

**Spec:** `docs/superpowers/specs/2026-11-11-adopt-compact-cupping-formset-design.md`

## Global Constraints

- Change only the cupping score presentation; keep order lines classic, as tracked in finding 34 / upstream #349.
- Preserve score fields, stock widgets, quarter-point validation, add/delete controls, permissions and persistence.
- Do not edit either upstream checkout.
- Record any theme CSS in `docs/crud_views_upstream_findings_roastery.md`.

## Review Focus

- Create GET with no saved scores: one heading strip and labelled blank rows render without a configuration error.
- Update GET with saved scores: headings still appear once and row labels remain associated with inputs.
- Invalid score POST: the compact row redisplays its value and validation error.
- Valid create/update POST: scores and totals still persist, with add/delete controls intact.
- Responsive styling: below 768 px row labels are visible and rows are readable; at desktop width shared headings align with columns.

---

### Task 1: Adopt and verify the compact cupping score declaration

**Files:**
- Modify: `example/roastery/forms.py`
- Test: `example/roastery/tests.py`
- Modify: `docs/crud_views_upstream_findings_roastery.md`
- Conditional modify: `src/crud_views_tabler/static/crud_views_tabler/crud_views_tabler.css` only for a reproduced Tabler mismatch

**Interfaces:**
- Consumes: upstream `CompactColumn(field: str, *, span: int)`, `CompactLayout(columns, *, controls_span: int)`, `FormSet.compact_layout`.
- Produces: `CUPPING_FORMSETS` with `scores` compact columns ordered `taster`, `CuppingScore.ATTRIBUTES`; no new public API.

- [x] **Step 1: Add a failing rendered-page test.** In `CuppingTests`, assert create and update GET contain one `.cv-formset-compact-headings`, a heading for each score field, two `.cv-formset-row-compact` blank create rows, and associated labels for score and taster inputs. Assert an invalid out-of-range POST redisplays the compact heading and error. Preserve the existing create/update persistence tests.
- [x] **Step 2: Run the focused test and see it fail.** Run `uv run python example/manage.py test roastery.tests.CuppingTests`; expect the new compact markup assertions to fail before implementation.
- [x] **Step 3: Implement the declaration.** Import `CompactColumn` and `CompactLayout` in `example/roastery/forms.py`. Set `compact_layout=CompactLayout(columns=[CompactColumn("taster", span=3), *(CompactColumn(name, span=1) for name in CuppingScore.ATTRIBUTES)], controls_span=2)` on `CUPPING_FORMSETS["scores"]`. Remove the unused cupping-specific `get_helper_layout_fields()` override and its subclass if no behavior depends on it; retain `InlineFormSet` in the factory. Remove the obsolete `form_show_labels=True` setting from that declaration.
- [x] **Step 4: Run focused verification.** Run `uv run python example/manage.py test roastery.tests.CuppingTests` and `uv run python example/manage.py check --fail-level WARNING`; expect both to pass.
- [x] **Step 5: Inspect the Tabler output.** Render create/update at desktop and mobile widths. Confirm one aligned heading strip at desktop, labelled cards at mobile, row controls and an invalid score error. Add theme CSS only for an observed mismatch, and rerun the focused test and check after any adjustment.
- [x] **Step 6: Update the tracker.** Mark finding 22 adopted, describe the declaration and actual verification, and remove the known rough edge about repeated cupping labels. Keep finding 34 open for order lines.
- [x] **Step 7: Verify and commit.** Run `uv run python example/manage.py test roastery` plus `git diff --check`; expect pass and no whitespace errors. Commit the task files with a message such as `Demo: adopt compact cupping score formset`.
