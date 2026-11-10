# Adopt upstream findings 24 and 29 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Demonstrate upstream snippet context in the order pages and document the existing custom-permission recipe.

**Architecture:** Change two lazy translated snippets on existing order views; upstream supplies their context. Keep the existing subscription permission declarations and request-level access tests, document the upstream recipe, and reconcile the tracker with verified demo adoption.

**Tech Stack:** Python 3.14, Django 6.1, editable django-crud-views dependency, Django TestCase.

**Spec:** `docs/superpowers/specs/2026-11-10-adopt-upstream-findings-24-29-design.md`

## Global Constraints

- Finding 28 is already adopted and is outside this change.
- Use `_("Created {{ view.duplicate }} from {{ object }}")` for `OrderDuplicateView.cv_message_template_code`.
- Use `_("New order for {{ parent_object }}")` for nested `OrderCreateView.cv_header_template_code`; keep top-level `AllOrdersCreateView` heading `New order`.
- No broader cleanup, dependencies, migrations, permission changes, theme/template overrides, or edits to either upstream checkout.
- Preserve creation/duplication behavior, redirects, action labels, breadcrumbs, and unrelated tracker edits.
- Do not infer GitHub issue closure from local implementation. `viewset.E269` does not verify database permission rows or grants and excludes Guardian/Resource ViewSets.

## Review Focus

- Nested create GET must name the URL's customer before any order object exists.
- Invalid nested create POST must retain the customer heading and safely escape customer-provided text.
- Duplicate success must distinguish the created draft from its source and redirect to the draft.
- Top-level create must retain `New order`, without depending on an absent `parent_object`.
- Subscription and nested-order access must remain restricted; use existing request-level tests alongside the startup check.

---

### Task 1: Adopt and verify findings 24 and 29

**Files:**
- Modify: `example/sales/views/order_actions.py` — duplicate success snippet.
- Modify: `example/sales/views/orders.py` — nested create heading only.
- Modify: `example/sales/views/subscriptions.py` — module documentation of the existing permission recipe.
- Test: `example/sales/tests/test_orders.py` — rendered headings and duplicate message.
- Modify: `docs/crud_views_upstream_findings_roastery.md` — findings 24 and 29 summaries and adoption details.

**Interfaces:**
- Consumes: upstream `cv_get_meta()` supplies `view` and child-only lazy `parent_object`; existing `OrderDuplicateView.cv_form_valid(context: dict)` sets `self.duplicate` while `self.object` remains the source.
- Consumes: existing `OrderTestCase.make_order()`, `order_kwargs()`, `order_post()` and `login()` fixtures; existing subscription permission tests.
- Produces: unchanged routes and business behavior, with the approved order text and accurate adoption documentation. No new production interface.

- [ ] **Step 1: Add rendered-behavior assertions before implementation.** In `OrderPageTests.test_duplicate_order`, capture the actual success message after POST with `get_messages(response.wsgi_request)` before following the redirect and assert its text is exactly `f"Created {copy} from {source}"`; keep the existing redirect and copied-line assertions. Also verify that the redirect destination renders the escaped message in its alert. Add `OrderFormTests.test_nested_create_heading_names_customer`: set the fixture customer's displayed name to `Roast <script>alert(1)</script> & Co`, GET `order-create` for its `customer_pk`, and assert the `.page-title` heading text is `New order for Roast <script>alert(1)</script> & Co` while the raw heading contains escaped markup and no literal `<script>`. Add `test_invalid_nested_create_keeps_customer_heading`: POST an invalid order form, assert HTTP 200 and form errors, and assert the same safely escaped customer heading on redisplay. Add `OrderPageTests.test_top_level_create_keeps_generic_heading`: GET `orders-create`, assert HTTP 200 and exact heading text `New order`. Scope all heading assertions to the rendered heading, excluding inline SVG and normalizing whitespace; use a small local helper or existing HTML parsing pattern without new dependencies. Use the real response and existing fixtures, not mocked snippet context.

- [ ] **Step 2: Watch the naming assertions fail.** Run `uv run python example/manage.py test sales.tests.test_orders.OrderFormTests sales.tests.test_orders.OrderPageTests`. Expected: failures for the missing customer heading and old duplicate success wording; the generic top-level heading still passes. Confirm failures come from those differences, not malformed fixture data or message consumption.

- [ ] **Step 3: Change the two snippets.** Set the exact values from Global Constraints on `OrderDuplicateView` and nested `OrderCreateView`. Leave `AllOrdersCreateView`, duplication logic, redirects, and every action/breadcrumb label untouched.

- [ ] **Step 4: Document finding 24's existing recipe.** Add a reference to upstream `docs/reference/custom_form_view.md#a-permission-of-its-own` in the subscription module docstring, connecting `CustomerSubscription.Meta.permissions` to `RunSubscriptionsView.cv_permission = "run"`. Preserve the declarations and all grants. Do not add a local implementation or synthetic test of upstream's `viewset.E269`.

- [ ] **Step 5: Verify the focused adoption.** Run `uv run python example/manage.py test sales.tests.test_orders sales.tests.test_subscriptions sales.tests.test_access`. Expected: all tests pass, including new rendering assertions, Owner-only subscription runs, and denied/cross-parent order requests. Run `uv run python example/manage.py check --fail-level WARNING`. Expected: no system-check issues.

- [ ] **Step 6: Reconcile tracker entries.** Update only findings 24 and 29's summary rows and detailed entries. For 24, retain upstream implementation details, label old undocumented/assert behavior as historical, and record the documented existing recipe plus verification. For 29, record that local upstream context support is present and the two snippets are now adopted; replace obsolete “plainer texts”/“When #339 lands” descriptions with historical/adoption wording. Retain the recorded GitHub issue status unless independently verified; do not claim local adoption closes the issue. Preserve unrelated work.

- [ ] **Step 7: Run repository verification.** Run `task test`. Expected: crispy, theme, and example suites all pass and the system check is clean. Report every failure by name if any occurs. Run `git diff --check`; expected: no whitespace errors. Review the diff against the spec, especially escaping, unchanged permissions, and the top-level heading.

- [ ] **Step 8: Commit and hand off for review.** Mark the completed plan steps, stage only the five adoption files and this plan, and commit as `fix: adopt upstream findings 24 and 29`. Use the preserved inline execution method and its final independent review. Leave integration into `main` for the user's choice.
