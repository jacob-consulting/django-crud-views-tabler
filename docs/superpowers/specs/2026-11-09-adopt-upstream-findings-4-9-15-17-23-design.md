# Adopt upstream fixes for roastery findings 4–9, 15, 17 and 23

Date: 2026-11-09. Source of truth for the findings: `docs/crud_views_upstream_findings_roastery.md`.

## Intent

django-crud-views has merged fixes for nine of the roastery findings (#319, #320, #322, #325, #328 and PR #336).
The findings doc lists each one as "Adopted here: not yet". This pass has two goals. First, drop the
workarounds in the theme and in the Acme demo wherever upstream now covers them. Second, put the new upstream
features to use in the demo so it shows them off, not only tolerates them. The upstream checkout
(`../django-crud-views`, at `fe9d5d2e` or later) is read-only. A gap we find stays worked around here and goes
in the findings doc.

## Goals

- Remove every workaround upstream now covers. Where upstream only documented our existing recipe, keep the
  code and point its comments at the upstream docs.
- Showcase: native transition buttons on the order workflow page, the business-validation hook with its
  refusal message, the accordion pack on the green lot detail, and the extended product card.
- Update each finding's "Adopted here" line and the summary table row, plus `docs/crud_views_tabler.md` where
  it still describes removed overrides. Update the tests that check the old workarounds.

## Non-goals

- Child-viewset tabs on the customer detail (the open half of finding 23). The context buttons stay.
- Findings 18, 24, 25 and every finding not listed above.
- Any change to the upstream checkouts.

## Anti-goals

- A permission regression. After `CustomerGrantMixin` is removed, the demo accounts must have exactly the
  access they have today (see finding 23 below). If they don't, this pass has failed even with the tests green.
- A visual regression on the product cards or the order page.

## Per finding

### 4, 5 — workflow badge and history (already adopted in code)

Commit `c3a4e83` already registers `workflow:badge-<colour>` → `badge bg-<colour>-lt` in
`src/crud_views_tabler/buttons.py`. It also deleted the theme's `badge.html` override and the
`:has(> table.table)` CSS, and `tests/crud_views_tabler/test_theme.py` covers all of that. Only the docs are
stale: the findings entries and `docs/crud_views_tabler.md` (lines ~137–140, the override tree ~297–309) still
describe the override. Fix the docs.
Check the workflow page under the theme: upstream's `workflow:history-table` default is plain `table`. Register
Tabler table classes for it if the history looks unlike the theme's other tables (builder's call; match what the
theme's own table override uses). Confirm that the action form renders in the form frame (card).

### 6 — per-transition permissions

Our setup (`OrderWorkflowView.cv_permission = "view"` plus django-fsm `permission=` on each step) is now
upstream's documented opt-in recipe (`docs/reference/workflow_view.md`). No code change. Point the module
docstring of `example/sales/views/order_actions.py` at the upstream recipe.

### 7 — refusal message, `clean()`, `run_transition`

- Move the "confirm needs at least one line" rule from `OrderWorkflowForm.clean()` into
  `Order.workflow_check_transition(self, name, *, user)`, raising `ValidationError(self.confirm_problem())` for
  `wf_confirm`. Delete `OrderWorkflowForm` if nothing else remains in it, and point the view at the default
  form.
- Set `cv_transition_presentation = "buttons"` on `OrderWorkflowView`. Requirement: a blocked step (Confirm on
  an order without lines) shows as a button and its reason is visible. Upstream's buttons mode shows a "business
  preview" on GET; use it.
- **Order detail page:** keep its own quick-action buttons (`sales/order_detail.html`). They post to the
  workflow view, so a refused step comes back with upstream's message. Check that the GET link with
  `?transition=<name>` (steps that need a comment) still preselects or highlights the step in buttons mode.
  If buttons mode has no preselection, the builder may keep `get_initial` or drop it, as long as the
  required-comment flow still works.
- Delete `example/sales/workflow.py:run_transition` and use upstream's
  `crud_views_workflow.lib.run_transition(obj, name, *, user, comment=None)`. Upstream has no `when=`. The seed
  backdates history rows, so it updates the returned `WorkflowInfo`'s `timestamp` after the call, as our helper
  already does internally. Upstream's helper runs `workflow_check_transition` and permission checks. The seed
  only takes valid steps with a permitted user, so a seed failure here is a real bug, not something to bypass.

### 8 — card insertion blocks

- The theme overrides `crud_views/tags/card.html` (`src/crud_views_tabler/templates/crud_views/tags/card.html`)
  and lacks upstream's new blocks. Add `card_root` (first child of the root `div`) and `card_header` (first child
  of `.card-body`) in the same positions as upstream, both empty. Update the template's comment block and the
  theme docs. Add a theme test that extends the card and fills both blocks.
- Rewrite `example/catalog/templates/catalog/product_card.html` as `{% extends "crud_views/tags/card.html" %}`.
  The status stripe goes in `card_root`, the type badge row in `card_header`, the title link in `card_title`,
  and subtitle and flavor/inactive badges in `card_content`. The price/stock footer goes in `card_actions`
  before `{{ block.super }}`, so it sits above the actions footer. The `data-product-card` attribute is on the
  root today, and tests may use it. If the root can't carry it any more, move it to an element inside the card
  and update the selectors. Remove the copied action plumbing. The rendered card must look the same as today.

### 9 — cards-first list

Upstream documented our existing configuration and added no API. No code change. Point the comments in
`example/catalog/views.py` (`ProductCardListView`, `ProductTableListView`) at the upstream recipe.

### 15 — accordion opens its first group (showcase)

Switch `roastery.views.LotDetailView` from `card-rows` to `cv_object_detail_layout = "accordion"`. Keep the group
order, so "Origin and producer" opens first. Update the class docstring and the demo text and docs that list
which page uses which pack (customers `split-card`, products `tabs-vertical`, lots now `accordion`;
`card-rows` is then unused in the demo, which is fine).

### 17 — tabs through the adapters

No theme code. `tabler-adapters.js` assigns `cv.bootstrapAdapters(() => globalThis.tabler)`, which now includes
the `tab` adapter. Add a theme test that the adapter set includes `tab`, at the same level as the existing
adapter tests. Check that keyboard navigation works on the product detail's vertical tabs.

### 23 — ancestor authorization replaces `CustomerGrantMixin`

`CustomerGrantMixin` (`example/sales/views/addresses.py`) is used on every nested view under customers:
addresses, orders, order actions (workflow, packing slip, duplicate) and subscriptions. Remove it and rely on
upstream's ancestor guard.

What the mixin does today, and the guard must reproduce:
- `can_on_customer(user, action, customer)` accepts object grants *and* model-level permissions, the latter for
  alex (Owner) and kim (Roasters). Upstream counts a model grant on a Guardian ancestor only with that
  ancestor's `AncestorPolicy(accept_global_perms=True)` (`docs/reference/guardian.md`, "Ancestor fallback").
  Configure that on the customer viewset.
- It treats views with `cv_permission == "view"` as reads (customer `view`) and everything else as writes
  (customer `change`). The order workflow view is `cv_permission = "view"`, but a POST runs a transition. Today
  a user with only `view` on a customer can POST a transition if fsm permits the step (kim roasting). Upstream
  may classify by HTTP method. Find out what it does and keep kim able to roast.

**Current state (verified 2026-11-09):** with upstream at `fe9d5d2e`+ the example's `manage.py check` already fails
with three `viewset.E268` errors: `address/make_default`, `order/duplicate` and `order/workflow` need
`ancestor_policy.actions[...] = AncestorPermissions(nearest=..., higher=...)`. Until those exist no example test
runs, so this work comes **first**, in two steps (decided with the user):

1. **First commit: policy + tests, mixin kept.** Configure the customer ancestor policy: the three missing
   actions (workflow view/view so kim can still roast; the builder picks the pairs for `make_default` and
   `duplicate` to match what the mixin enforces today, i.e. customer `change` since their `cv_permission` is not
   `"view"`), and `accept_global_perms=True` so alex and kim keep their model-level access. Add the access matrix
   tests below. Both gates are now active, the tests pin today's access, and `check` is green again.
2. **Later commit: remove `CustomerGrantMixin`.** The same tests, unchanged, must still pass. That shows the
   guard alone covers it.

Upstream applies one ancestor permission pair per endpoint whatever the HTTP method, so `actions["workflow"]`
view/view keeps POSTed transitions available to view-only users; django-fsm `permission=` still decides the step.
A customer outside sam's grants stays 403 (the customer queryset is not filtered, so it is not a 404).

Access matrix (sam, kim, alex; list/detail/create/update/delete/custom endpoints under addresses, orders, order
actions and subscriptions):
- sam: reads and writes nested pages of his granted customers; 403 on another manager's customer.
- kim: reads orders and can run the roast step on any customer's order; no address/subscription writes she
  can't do today.
- alex: everything.

If the guard can't reproduce a row of this matrix through upstream configuration, keep a minimal mixin for that
case only, and record the gap as a new note under finding 23.

The breaking changes in `docs/migrating-1.0.md` (`cv_guardian_parent_*`, `cv_guardian_accept_global_perms` on
`GuardianViewSet`) also apply. Check `example/sales/views/customers.py` and fix whatever the upgrade's system
checks report (`manage.py check --fail-level WARNING` must stay clean).

## Constraints

- CLAUDE.md theme rules hold: upstream hooks first, then theme CSS, then override templates. Every theme change
  gets its findings-doc entry in the same commit.
- Example apps never import `django_tabler` or `crud_views_tabler`.
- `task test` passes at the end (all three suites plus the check). It is red at the start (E268 above); the first
  commit makes it green.

## Left to the builder

- Commit granularity and order after the Guardian first commit (above, fixed). Suggested: one commit per finding
  group (workflow, cards, object detail), the `CustomerGrantMixin` removal as its own commit.
- Exact Tabler classes for `workflow:history-table`.
- Whether the seed's backdating stays a small helper in `sales/seed.py`.
