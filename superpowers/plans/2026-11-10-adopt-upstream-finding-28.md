# Adopt upstream finding 28 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Adopt upstream ViewSet names for consistent subscription labels and remove the list-header workaround.

**Architecture:** Configure both existing subscription ViewSets with upstream's singular and plural naming fields. Let the existing snippet and breadcrumb rendering propagate those names; keep custom action and message text.

**Tech Stack:** Python 3.14, Django 6.1, django-crud-views (editable sibling checkout), Django TestCase.

**Spec:** `docs/superpowers/specs/2026-11-10-adopt-upstream-finding-28-design.md`

## Global Constraints

- Both ViewSets use `verbose_name=_("subscription")` and `verbose_name_plural=_("subscriptions")`.
- Remove only the two list-header overrides; keep custom “Run subscriptions” labels and existing subscription success messages.
- No broader subscription cleanup, model renaming, migrations, permission changes, theme changes, or edits to either upstream checkout.
- Preserve existing uncommitted upstream-status edits in the tracker.

## Review Focus

- Nested and top-level lists must both say “Subscriptions”; check the heading and breadcrumb independently.
- Nested create/update/delete headers must use the singular ViewSet name even though the model name differs.
- Delete modal requests must also receive the new header, rather than testing only full pages.
- Custom run-page wording must continue to take precedence over generated names.
- Model-centric delete text may still say “Customer subscription”; scope assertions to headings and breadcrumbs rather than banning the phrase from the entire response.

---

### Task 1: Adopt the subscription ViewSet names and record finding 28 as resolved

**Files:**
- Modify: `example/sales/views/subscriptions.py` — ViewSet configuration and list headers.
- Test: `example/sales/tests/test_subscriptions.py` — rendered naming regression coverage.
- Modify: `docs/crud_views_upstream_findings_roastery.md` — finding 28 summary row and detailed adoption entry.

**Interfaces:**
- Consumes: existing `ViewSet(verbose_name=..., verbose_name_plural=...)`, lazy `_`, and `SubscriptionTestCase.subscribe()` / `login()` fixtures.
- Produces: unchanged subscription routes and behavior, with ViewSet names propagated through generated labels.

- [x] **Step 1: Add focused rendered-label tests to `SubscriptionViewTests`.** Log in as alex and create a subscription with `self.subscribe(self.mine)`. Add `test_subscription_lists_use_viewset_names` for `subscriptions-list` and `subscription-list` (the latter with `customer_pk=self.mine.pk`): assert HTTP 200, heading text `Subscriptions`, and a breadcrumb item with text `Subscriptions`, with no `Customer subscriptions` in that breadcrumb. Add `test_subscription_form_headers_use_viewset_name` for nested create/update/delete: assert HTTP 200 and exact heading text `Subscription` on each page (the upstream header snippets contain the name alone). Supply `customer_pk` for all three and the subscription `pk` for update/delete. Add `test_subscription_delete_modal_uses_viewset_name`: request delete with `headers={"X-CV-Modal": "true"}` and assert `.modal-title` text `Subscription`. Add `test_run_subscription_header_keeps_custom_label`: GET `subscriptions-run` and assert heading `Run subscriptions`. Extract rendered text from `.page-title`, `.modal-title`, and breadcrumb elements with Python's standard HTML parser or an existing available parser; normalize whitespace and ignore inline SVG contents. Do not assert against unrelated body text.

- [x] **Step 2: Run the new tests before changing configuration.**

Run: `uv run python example/manage.py test sales.tests.test_subscriptions.SubscriptionViewTests`

Expected: naming assertions fail on model-derived headers/breadcrumbs; existing permission and custom run-page behavior passes.

- [x] **Step 3: Configure both ViewSets and remove redundant headers.** Add `verbose_name=_("subscription")` and `verbose_name_plural=_("subscriptions")` to `cv_subscription` and `cv_all_subscriptions`. Remove `cv_header_template_code` from `SubscriptionListView` and `AllSubscriptionsListView`, including the obsolete comment. Retain every other custom label/message declaration.

- [x] **Step 4: Verify the subscription suite and Django configuration.**

Run: `uv run python example/manage.py test sales.tests.test_subscriptions`

Expected: all subscription tests pass, including the naming tests and existing permissions, messages, and order-generation behavior.

Run: `uv run python example/manage.py check --fail-level WARNING`

Expected: no system-check issues.

- [x] **Step 5: Update finding 28.** Change its table row from adoption pending to resolved/adopted. Rewrite “What we did” as the historical workaround and replace “Demo adoption pending” with an adoption note describing both ViewSet declarations, removal of the two header overrides, and the verified generated labels. Preserve the user's upstream merge/status updates and every other finding.

- [x] **Step 6: Review and commit the adoption.** Run `git diff --check` (expected: no whitespace errors) and review `git diff` for the three files. Confirm model metadata, permissions, custom messages, and custom run labels were not modified. Stage only these files and commit with `fix: adopt subscription ViewSet names from upstream finding 28`. Preserve the existing tracker edits in the same file; do not revert them or stage unrelated files.
