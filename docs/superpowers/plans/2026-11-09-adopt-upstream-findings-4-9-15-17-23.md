# Adopt Upstream Fixes for Findings 4–9, 15, 17 and 23: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Acme demo's and the theme's workarounds with the upstream fixes for roastery findings 4–9, 15,
17 and 23, and use the new upstream features in the demo.

**Architecture:** Step 1 makes the example check green again by declaring the customer ancestor policy, and adds
access tests while `CustomerGrantMixin` is still in place. Then workflow, cards and object detail each adopt their
upstream hooks with matching findings-doc updates. The last task removes `CustomerGrantMixin` and leaves the access
tests unchanged.

**Tech Stack:** Django 6.1, django-crud-views (editable `../django-crud-views`, at `fe9d5d2e` or later), django-fsm,
django-guardian, Tabler 1.6.1.

**Spec:** `docs/superpowers/specs/2026-11-09-adopt-upstream-findings-4-9-15-17-23-design.md`

## Global Constraints

- `../django-crud-views` and `../django-crud-views-extensions` are read-only. Gaps are worked around here and logged
  in `docs/crud_views_upstream_findings_roastery.md`.
- Example apps never import `django_tabler` or `crud_views_tabler`.
- Theme fix order: upstream hook, then CSS in `crud_views_tabler.css`, then an override template. Every theme change
  gets its findings-doc entry in the same commit.
- Each finding's "Adopted here:" line is rewritten from "not yet; …" to what was done and where. Its summary-table row
  (doc lines ~40–59) drops "not yet adopted" and names the new state.
- `task test` (three suites plus `manage.py check --fail-level WARNING`) is red at the start (three `viewset.E268`)
  and must be green after Task 1 and at the end of every later task.
- Commits end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

Test commands used below:
- Example: `uv run python example/manage.py test django_tabler dashboard sales catalog roastery shipping showcase`
- Theme: `uv run --group test pytest tests/crud_views_tabler --ds tests.crud_views_tabler.settings`
- Check: `uv run python example/manage.py check --fail-level WARNING`

## Review Focus

1. **Kim's roast POST after the mixin is gone.** A view-only customer user must still run a permitted transition.
   This is pinned by `test_kim_roasts_any_customers_order` (Task 1), which must pass unchanged in Task 5.
2. **Sam on another manager's customer gets 403, not 404 or 200,** for every nested endpoint, GET and POST. Pinned by
   `test_sam_is_refused_on_other_customers_nested_pages` (Task 1).
3. **Seeding with upstream `run_transition`** refuses a step when the actor lacks permission or a required comment
   is missing. `seed_demo --reset` must still build the world. Pinned by the existing `SeedTests` plus
   `SeedHistoryTests.test_seed_history_is_backdated` (Task 2).
4. **A blocked Confirm in buttons mode** stays visible and disabled with its reason on GET, and a forced POST is
   refused with the message. Pinned by `test_blocked_confirm_shows_disabled_button_with_reason` (Task 2) and the
   existing `test_confirm_without_lines_is_refused`.
5. **A custom card template that fills no new block** renders exactly as before under the theme (no stray empty
   elements). Pinned by `test_card_new_blocks_are_empty_by_default` (Task 3).

---

### Task 1: Customer ancestor policy and access tests (mixin kept)

**Files:**
- Modify: `example/sales/views/customers.py:34` (`cv_customer`)
- Modify: `example/sales/views/addresses.py:31` (`cv_address`), `example/sales/views/orders.py:38` (`cv_order`)
- Create: `example/sales/tests/test_access.py`
- Modify: `docs/crud_views_upstream_findings_roastery.md` (finding 23: note the policy)

**Interfaces:**
- Produces: `cv_customer.ancestor_policy == AncestorPolicy(accept_global_perms=True)`. The `cv_address` policy has
  `actions={"make_default": AncestorPermissions(nearest="change", higher="view")}`. The `cv_order` policy has
  `actions={"duplicate": AncestorPermissions(nearest="change", higher="view"), "workflow":
  AncestorPermissions(nearest="view", higher="view")}`. `AncestorPolicy` and `AncestorPermissions` are imported
  from `crud_views.lib.viewset`.
- Produces: `sales.tests.test_access.AccessMatrixTests`, which Task 5 runs unchanged.

- [ ] **Step 1: Confirm the starting state**

Run the check. Expected: exactly three `viewset.E268` (address `make_default`, order `duplicate`, order `workflow`).

- [ ] **Step 2: Declare the policies**

Add the three `ancestor_policy=` values above. The pairs reproduce what `CustomerGrantMixin` enforces today:
`cv_permission == "view"` reads the customer, anything else writes it. `make_default` is `"change"`,
`duplicate` is `"add"` and workflow is `"view"`. The default Read and Write pairs (`view/view`, `change/view`)
already cover the built-in views.

- [ ] **Step 3: Run the check**

Expected: `System check identified no issues`.

- [ ] **Step 4: Write `example/sales/tests/test_access.py`**

`class AccessMatrixTests(OrderTestCase)` (import from `.test_orders`). Use `self.mine` (Sam's), `self.other` (not
Sam's), `make_order`, and an `Address`/`CustomerSubscription` from each customer. Define the endpoints once as
`(url_name, kwargs_fn, method)` tuples. Cover the list, detail, create, update and delete views of address, order
and subscription, plus `address-make_default`, `order-packing_slip`, `order-duplicate` and `order-workflow`.
Tests:

```python
def test_sam_is_refused_on_other_customers_nested_pages(self):
    # every endpoint under self.other: GET and POST -> 403, and nothing in the DB changes
def test_sam_reaches_his_customers_nested_pages(self):
    # every read endpoint under self.mine -> 200; address-update GET -> 200; order-workflow POST wf_confirm -> 302
def test_kim_reads_every_customers_nested_lists(self):
    # address-list, order-list, subscription-list for self.mine and self.other -> 200
def test_kim_cannot_write_addresses_or_subscriptions(self):
    # address-create, address-update, address-make_default, subscription-create GET -> 403
def test_kim_roasts_any_customers_order(self):
    # confirmed order of self.other; POST order-workflow {"transition": "wf_roast"} -> 302, state ROASTED
def test_alex_reaches_everything(self):
    # every endpoint GET under self.other -> 200 (workflow on a draft with lines)
```

Each 403 assertion passes the URL name as `msg`, so a failure says which endpoint broke. Where a 403 here
disagrees with the existing `OrderRoleTests`/`AddressTests`, the existing test describes today's access. Fix the
new test, never the code.

- [ ] **Step 5: Run the sales tests**

Run: `uv run python example/manage.py test sales`. Expected: all pass, including the new class. The mixin and the
guard are both active.

- [ ] **Step 6: Run `task test`.** Expected: green.

- [ ] **Step 7: Findings doc, finding 23**

Add an "Adopted here (step 1)" note. The customer is `AncestorPolicy(accept_global_perms=True)`, with action pairs
for `make_default`, `duplicate` and `workflow`. Explain why the three E268 entries were needed, and that the mixin
stays until Task 5.

- [ ] **Step 8: Commit** — `Sales: declare the customer ancestor policy (#336), pin nested access`

---

### Task 2: Workflow (findings 4–7)

**Files:**
- Modify: `example/sales/models.py:204-244` (`Order`: add `workflow_check_transition`)
- Modify: `example/sales/forms.py:248-258` (delete `OrderWorkflowForm`)
- Modify: `example/sales/views/order_actions.py:1-38` (`OrderWorkflowView`)
- Modify: `example/sales/templates/sales/order_detail.html:9-10` (comment-step link)
- Modify: `example/sales/seed.py:14,167`; delete `example/sales/workflow.py`
- Modify: `example/sales/tests/test_orders.py` (`OrderWorkflowTests`, new `SeedHistoryTests`)
- Maybe modify: `src/crud_views_tabler/buttons.py` (`workflow:history-table`), `tests/crud_views_tabler/test_theme.py`
- Modify: `docs/crud_views_upstream_findings_roastery.md` (4, 5, 6, 7), `docs/crud_views_tabler.md` (~137–140, ~297–309)

**Interfaces:**
- Produces: `Order.workflow_check_transition(self, name, *, user) -> None`, which raises
  `django.core.exceptions.ValidationError(problem)` when `name == "wf_confirm"` and
  `(problem := self.confirm_problem())`.
- Consumes: `crud_views_workflow.lib.run_transition(object, name, *, user, comment=None) -> WorkflowInfo`.

- [ ] **Step 1: Write the failing tests** in `OrderWorkflowTests`

```python
def test_blocked_confirm_shows_disabled_button_with_reason(self):
    self.login()
    order = self.make_order(lines=False)
    html = self.client.get(reverse("order-workflow", kwargs=self.order_kwargs(order))).content.decode()
    self.assertRegex(html, r'<button[^>]*name="transition"[^>]*value="wf_confirm"[^>]*disabled')
    self.assertIn("Add at least one line item before confirming the order.", html)

def test_workflow_page_uses_buttons(self):
    self.login()
    html = self.client.get(reverse("order-workflow", kwargs=self.order_kwargs(self.make_order()))).content.decode()
    self.assertNotIn('type="radio"', html)
    self.assertIn('value="wf_cancel"', html)

def test_model_hook_refuses_confirm_without_lines(self):
    with self.assertRaisesMessage(ValidationError, "Add at least one line item"):
        self.make_order(lines=False).workflow_check_transition("wf_confirm", user=self.sam)
```

Match the button regex to upstream's real markup (`crud_views_workflow` templates). The point is a disabled native
submit for `wf_confirm`. In `test_detail_shows_steps_and_transition_buttons`, change the `?transition=wf_cancel`
href assertion to the plain workflow URL (Step 4 drops the query string).

- [ ] **Step 2: Run them to see them fail.** `uv run python example/manage.py test sales.tests.test_orders.OrderWorkflowTests` fails on radios or the missing hook.

- [ ] **Step 3: Implement**

Add `Order.workflow_check_transition`. Keep the guard in `wf_confirm` for direct calls. Delete `OrderWorkflowForm`;
`OrderWorkflowView` uses upstream's default form (drop `form_class`, or set `WorkflowForm` if the view requires
one) and `cv_transition_presentation = "buttons"`, and loses `get_initial`. Rewrite the module docstring: per-step
permissions follow upstream's documented opt-in recipe (`docs/reference/workflow_view.md`, finding 6). On the order
page, the required-comment link becomes the plain workflow URL. On the workflow page, the user types the comment
and clicks that step's button.

- [ ] **Step 4: Swap the seed to upstream `run_transition`**

Write a test first, in `sales/tests/test_orders.py` as `class SeedHistoryTests(OrderTestCase)` (it needs `history()`; `test_customers` can't import it without a cycle):

```python
def test_seed_history_is_backdated(self):
    shipped = Order.objects.filter(state=OrderState.SHIPPED).first()
    steps = history(shipped).order_by("timestamp")
    self.assertLess(steps.last().timestamp, timezone.now() - timedelta(minutes=4))
    self.assertLessEqual(steps.first().timestamp, shipped.created_at + timedelta(days=1))
```

Then, in `seed.py`, call `info = run_transition(order, name, user=by, comment=COMMENTS.get(name) or None)` and
backdate with `WorkflowInfo.objects.filter(pk=info.pk).update(timestamp=when)`. Delete `sales/workflow.py`. If
upstream refuses a seeded step, fix the seed data (actor or comment). Never bypass the check.

- [ ] **Step 5: History table classes (finding 5)**

Render an order's workflow page under the theme and compare its history table with a theme list table. If they
differ, register `"workflow:history-table"` in `TABLER_BUTTON_CLASSES` with the theme table's classes, and add a theme
test next to `test_all_state_colours_are_light_badges` asserting the key resolves to them. Confirm that the action
form sits inside the form frame (`card`), using the existing workflow composition test in `test_theme.py`. If it's
not covered there, add an assertion.

- [ ] **Step 6: Run the example and theme suites and the check.** Expected: all pass. Then run `uv run python example/manage.py seed_demo --reset`. Expected: it completes with no error.

- [ ] **Step 7: Docs.** Findings 4 and 5: adopted in `c3a4e83` (class keys in `buttons.py`, override and CSS removed), plus Step 5's result. Finding 6: the recipe is now upstream's documented one, and the code is unchanged. Finding 7: hook, buttons presentation and `run_transition` adopted, form subclass and helper deleted. In `docs/crud_views_tabler.md`, remove the `badge.html` override text and the tree entries for the badge and the overflow CSS, and describe the class keys.

- [ ] **Step 8: Commit** — `Workflow: adopt upstream business hook, transition buttons and run_transition (#319, #320, #322)`

---

### Task 3: Card insertion blocks (findings 8, 9)

**Files:**
- Modify: `src/crud_views_tabler/templates/crud_views/tags/card.html`
- Modify: `tests/crud_views_tabler/test_theme.py` (`CardThemeTests`) plus a test card template under the theme
  test app's templates
- Modify: `example/catalog/templates/catalog/product_card.html`
- Modify: `example/catalog/views.py:76-120` (comments only), `example/catalog/tests.py` (only if selectors move)
- Modify: `docs/crud_views_upstream_findings_roastery.md` (8, 9), `docs/crud_views_tabler.md` (card section)

**Interfaces:**
- Produces: theme card blocks `card_root` (first child of the `card:root` div) and `card_header` (first child of the
  `card:body` div), both empty by default, alongside the existing `card_title`, `card_content` and `card_actions`.

- [ ] **Step 1: Write the failing theme tests** in `CardThemeTests`

```python
def test_card_new_blocks_are_empty_by_default(self):
    # render the stock theme card; the root div's first child is the card body, the body's first child the heading
def test_card_root_and_header_blocks_render_in_place(self):
    # a test template {% extends "crud_views/tags/card.html" %} filling card_root with <i data-root></i> and
    # card_header with <i data-head></i>: data-root directly after the root div's opening tag,
    # data-head directly after the body div's opening tag and before the heading
```

- [ ] **Step 2: Run them to see them fail** (theme suite, `-k CardThemeTests`). The second test fails because the blocks are missing.

- [ ] **Step 3: Add the two blocks** to the theme card, in upstream's positions, and list them in the template's comment block.

- [ ] **Step 4: Run the theme suite.** Expected: it passes.

- [ ] **Step 5: Rewrite `product_card.html`** as `{% extends "crud_views/tags/card.html" %}`. The stripe goes in
`card_root`, the badge/corner row in `card_header`, and the title link in `card_title`. The heading's level and class
now come from the theme (`card:title`). If that changes the look compared with today's `card-title mb-1` h3, record
it in finding 8, don't re-copy the card. Subtitle and badges go in `card_content`. In `card_actions`, put the
price/stock `card-footer` before `{{ block.super }}`. Put `data-product-card="{{ object.pk }}"` on the stripe
element in `card_root`, so the existing count assertions in `catalog/tests.py` stay valid unchanged. The comment
block is updated: the card now extends the theme card.

- [ ] **Step 6: Run the example suite, then look at the page.** `catalog` tests pass. Run `task up` (or reuse a running
server), open `/catalog/products/` as alex and compare the cards with `git stash` before and after: stripe, badge row,
title, footer and actions should look the same.

- [ ] **Step 7: Comments and docs.** In `catalog/views.py`, the comments on `ProductCardListView` and `ProductTableListView` point to upstream's cards-first recipe (`docs/reference/card-list-view.md`, #325). The code stays as it is. Update findings 8 and 9 and the card section of `docs/crud_views_tabler.md` (new blocks).

- [ ] **Step 8: Commit** — `Cards: theme card gains card_root/card_header; product card extends it (#325)`

---

### Task 4: Accordion on the green lot, tabs through the adapters (findings 15, 17)

**Files:**
- Modify: `example/roastery/views.py:118-122` (`LotDetailView`)
- Modify: `example/roastery/tests.py` (`LotTests`)
- Modify: `tests/crud_views_tabler/test_theme.py` (adapter tests near line 235)
- Modify: `docs/crud_views_upstream_findings_roastery.md` (15, 17), plus any demo text or doc that lists lots as
  `card-rows` (search for `card-rows` with grep)

- [ ] **Step 1: Write the failing tests**

```python
# roastery/tests.py, LotTests
def test_detail_is_an_accordion_with_the_first_group_open(self):
    self.login()
    html = self.client.get(reverse("lot-detail", kwargs={"pk": self.lot.pk})).content.decode()
    self.assertEqual(html.count('class="accordion-collapse collapse show"'), 1)
    self.assertLess(html.index("Origin and producer"), html.index("Stock and price"))
    self.assertLess(html.index("collapse show"), html.index("Stock and price"))
```

```python
# test_theme.py, next to the tooltip adapter tests
def test_upstream_adapter_set_includes_tab_and_theme_takes_all_of_it(self):
    # crud_views/js/adapters.js's bootstrapAdapters returns a `tab:` entry using component(ns, "Tab");
    # tabler-adapters.js assigns Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler))
```

- [ ] **Step 2: Run them.** The lot test fails. The adapter test passes immediately, since it pins existing behaviour, which is expected for finding 17.

- [ ] **Step 3: Switch the layout.** Set `cv_object_detail_layout = "accordion"` and keep the group order. The docstring says that lots show upstream's accordion (first group open, #328), customers `split-card` and products `tabs-vertical`.

- [ ] **Step 4: Run the roastery and theme suites.** Expected: they pass.

- [ ] **Step 5: Look at the page.** Open a lot detail: "Origin and producer" is open and the others are closed and can be toggled. Open a product detail and check the vertical tabs: arrow keys move between tabs. Upstream's accordion count badge is `text-bg-secondary`, a solid badge. If it clashes with the theme's light badges, record it as a new note under finding 15, without fixing it here.

- [ ] **Step 6: Docs.** Finding 15: adopted on the green lot detail. Finding 17: no theme code needed, because `bootstrapAdapters` includes `tab` and the theme assigns the whole set. Pinned by the test, keyboard checked by hand.

- [ ] **Step 7: Commit** — `Object detail: green lot uses the accordion; tab adapter pinned (#328)`

---

### Task 5: Remove `CustomerGrantMixin` (finding 23)

**Files:**
- Modify: `example/sales/views/addresses.py:43-51` (delete the class) and every view that lists it in
  `addresses.py`, `orders.py`, `order_actions.py`, `subscriptions.py`
- Modify: module docstrings in `orders.py:3` and `subscriptions.py:3`, plus the comment in `seed.py:84`
- Modify: `example/sales/permissions.py` (delete `can_on_customer` only if nothing else uses it; check with grep)
- Modify: `docs/crud_views_upstream_findings_roastery.md` (finding 23 and its table row)

**Interfaces:**
- Consumes: `AccessMatrixTests` from Task 1, unchanged.

- [ ] **Step 1: Remove the mixin** from all bases and delete the class. The docstrings and comments name upstream's ancestor guard (`docs/reference/nested.md`, "Ancestor authorization") as the gate.

- [ ] **Step 2: Run the sales suite.** Expected: everything passes, `AccessMatrixTests` and the existing role tests included, with no test edits. If something fails, stop. Find out which access row the guard can't reproduce. Restore a minimal mixin for that case only, and write the gap up as a note under finding 23.

- [ ] **Step 3: Run `task test`.** Expected: green.

- [ ] **Step 4: Docs.** Finding 23's "Adopted here" says the parent gate is upstream's ancestor guard and `CustomerGrantMixin` is removed. Child tabs are still open, and the context buttons stay. Update the table row.

- [ ] **Step 5: Commit** — `Sales: drop CustomerGrantMixin for upstream ancestor authorization (#336)`
