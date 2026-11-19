# Object Navbar Adoption Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every customer page and every page nested under a customer shows upstream's object navbar, placed by the Tabler theme, and finding 23 is closed.

**Architecture:** The theme's `crud_views_tabler/page.html` renders `{% cv_navbar %}` in a new empty block of `django_tabler/layouts/app.html` above the page header, using upstream's stock navbar templates. The example declares one `NavBar` for `customer` and attaches a mixin to the customer object views and all nested order, address and subscription views; the three child context buttons go away.

**Tech Stack:** Django 6.1, Python 3.14, django-crud-views from the sibling checkout `../django-crud-views` (branch `gsd/phase-06.40-object-navbar-opt-in-section-navigation-381`), Tabler 1.6.1.

**Spec:** `docs/superpowers/specs/2026-11-19-object-navbar-adoption-design.md`. Upstream reference: `../django-crud-views/docs/reference/navbar.md`.

## Global Constraints

- `../django-crud-views` and `../django-crud-views-extensions` are read-only.
- No override of `crud_views/tags/navbar.html`, `navbar_identity.html` or `navbar_items.html` in the theme or the example.
- App code under `example/` never imports `django_tabler` or `crud_views_tabler`.
- A page without a navbar keeps its markup byte for byte: the wrapper is emitted only when `cv_navbar` is truthy.
- Every theme CSS rule and every upstream awkwardness gets an entry in `docs/crud_views_upstream_findings_roastery.md` in the same commit.
- Upstream issue #381 is open with no pull request: docs cite the branch above, never a merge or "DONE upstream".
- Work on a new branch `adopt/object-navbar-381` cut from `main`. Commit messages follow the repo's style (a sentence, e.g. "Adopt upstream findings 20 and 35: ...") and end with the `Co-Authored-By` line of the session.
- The branch `experiment/customer-section-navigation-06-33` is not merged and its code is not copied.

## Review Focus

Each line has its test in the task named.

1. A customer whose name contains markup (`<b>A & B</b>`) shows it escaped in the identity and in the `aria-label`. (Task 2)
2. A customer with no subscriptions still shows the Subscriptions item. (Task 2)
3. An invalid POST that re-renders a nested form (order create) still shows the bar with Orders active. (Task 2)
4. A visible item never leads to a 403 for the same user, and an openable section is never hidden. (Task 2, the role matrix)
5. A delete page requested as a modal contains no bar. (Task 2)

---

### Task 1: The theme places the bar above the page header

**Files:**
- Modify: `src/django_tabler/templates/django_tabler/layouts/app.html` (inside `.page-wrapper`, before `.page-header`)
- Modify: `src/crud_views_tabler/templates/crud_views_tabler/page.html`
- Modify: `tests/crud_views_tabler/testapp/views.py`
- Test: `tests/crud_views_tabler/test_theme.py` (class `ThemeRenderingTests`)
- Modify: `docs/crud_views_tabler.md` (table in "The page: CRUD_VIEWS_EXTENDS"), `CLAUDE.md` ("Template chain" paragraph)
- Add to the first commit: the spec and this plan.

**Interfaces:**
- Produces: block `page_header_before` in `django_tabler/layouts/app.html` (empty by default); block `cv_navbar` in `crud_views_tabler/page.html`; wrapper element `<div class="cv-tabler-navbar container-xl d-print-none ...">` present only when a bar renders.

- [ ] **Step 1: Give the theme test app a bar**

In `tests/crud_views_tabler/testapp/views.py`:

```python
customer_navbar = NavBar(viewset="customer", items=[NavItem(key="detail"), NavItem(key="update")])


class CustomerNavbarMixin(CrudViewNavBarMixin):
    cv_navbar = customer_navbar
```

Put `CustomerNavbarMixin` first in the bases of `CustomerDetailView` and `CustomerUpdateView`. Imports come from `crud_views.lib.navbar`.

- [ ] **Step 2: Write the failing tests**

```python
def test_navbar_sits_above_the_page_header(self):
    html = self.client.get(reverse("customer-detail", kwargs={"pk": self.customer.pk})).content.decode()
    wrapper = html.index('class="cv-tabler-navbar container-xl d-print-none')
    self.assertLess(wrapper, html.index('class="cv-navbar'))
    self.assertLess(html.index('class="cv-navbar'), html.index('class="page-header'))
    self.assertEqual(html.count('class="cv-navbar '), 1)
    self.assertIn('aria-label="Sections for Customer 03"', html)
    self.assertRegex(html, r'class="nav-link[^"]* active" href="[^"]+" aria-current="true"')

def test_navbar_icons_are_tabler_svgs(self):
    html = self.client.get(reverse("customer-detail", kwargs={"pk": self.customer.pk})).content.decode()
    bar = html[html.index('class="cv-navbar'):html.index('class="page-header')]
    self.assertIn("<svg", bar)
    self.assertNotIn("fa-", bar)

def test_page_without_navbar_has_no_wrapper(self):
    html = self.client.get(reverse("customer-list")).content.decode()
    self.assertNotIn("cv-tabler-navbar", html)
    self.assertNotIn("cv-navbar", html)
```

- [ ] **Step 3: Run them and see the first two fail**

Run: `uv run --group test pytest tests/crud_views_tabler --ds tests.crud_views_tabler.settings -k navbar`
Expected: `test_navbar_sits_above_the_page_header` and `test_navbar_icons_are_tabler_svgs` FAIL with `ValueError: substring not found`; the third passes.

- [ ] **Step 4: Add the block and fill it**

`app.html`: `{% block page_header_before %}{% endblock %}` as the first child of `<div class="page-wrapper">`.

`page.html`:

```django
{% block page_header_before %}{% if cv_navbar %}<div class="cv-tabler-navbar container-xl d-print-none pt-3">{% block cv_navbar %}{% cv_navbar %}{% endblock %}</div>{% endif %}{% endblock %}
```

The spacing classes after `d-print-none` are yours to adjust in Task 3.

- [ ] **Step 5: Run the theme suite and the example check**

Run: `uv run --group test pytest tests/crud_views_tabler --ds tests.crud_views_tabler.settings` and `uv run python example/manage.py test django_tabler`
Expected: all pass. If an existing test fails because the test app's detail or update page now has a bar, the test is asserting on markup the bar legitimately changed: update that assertion, and say so in the commit message.

- [ ] **Step 6: Document the block**

- `docs/crud_views_tabler.md`: add the row `| {% cv_navbar %} (block cv_navbar) | above .page-header, in the layout's page_header_before block; stock templates, no override |` to the mapping table, and one sentence below it that the wrapper appears only when a bar renders and is hidden in print.
- `CLAUDE.md`, "Template chain": add `page_header_before` to the list of `app.html` blocks and `cv_navbar` to the tags `page.html` maps.

- [ ] **Step 7: Commit**

```bash
git switch -c adopt/object-navbar-381
git add docs/superpowers/specs/2026-11-19-object-navbar-adoption-design.md docs/superpowers/plans/2026-11-19-object-navbar-adoption.md \
  src/django_tabler src/crud_views_tabler tests/crud_views_tabler docs/crud_views_tabler.md CLAUDE.md
git commit -m "Theme: place the upstream object navbar above the page header (block page_header_before)"
```

---

### Task 2: The customer bar in the Acme demo

**Files:**
- Modify: `example/sales/views/customers.py`, `orders.py`, `order_actions.py`, `addresses.py`, `subscriptions.py`
- Create: `example/sales/tests/test_navbar.py`
- Modify: `docs/crud_views_upstream_findings_roastery.md`

**Interfaces:**
- Consumes: the theme placement of Task 1 (the bar renders on any page whose view has the mixin).
- Produces: `customer_navbar` and `CustomerNavbarMixin` in `example/sales/views/customers.py`.

- [ ] **Step 1: Write the failing tests**

`example/sales/tests/test_navbar.py`, class `CustomerNavbarTests(OrderTestCase)` (from `.test_orders`). One helper:

```python
SECTIONS = ("customer-detail", "order-list", "subscription-list", "address-list")
LABELS = ["Details", "Orders", "Subscriptions", "Addresses"]


def section_urls(customer):
    return [reverse("customer-detail", kwargs={"pk": customer.pk})] + [
        reverse(name, kwargs={"customer_pk": customer.pk}) for name in SECTIONS[1:]
    ]


def navbar(response):
    """None without a bar, else {"label", "items": [(text, href, active)]}."""
    html = response.content.decode()
    nav = re.search(r'<nav aria-label="Sections for ([^"]*)">(.*?)</nav>', html, re.S)
    if nav is None:
        return None
    items = [
        (strip_tags(body).strip(), href, "aria-current" in rest)
        for href, rest, body in re.findall(r'<a class="nav-link[^"]*" href="([^"]+)"([^>]*)>(.*?)</a>', nav.group(2), re.S)
    ]
    return {"label": unescape(nav.group(1)), "items": items}
```

Tests, as `alex` unless stated:

| Test | Assertion |
|---|---|
| `test_customer_detail_shows_four_sections` | on `customer-detail` of `self.mine`: `label == str(self.mine)`, texts `== LABELS`, hrefs `== section_urls(self.mine)`, only "Details" active |
| `test_update_page_has_the_bar_without_an_active_item` | on `customer-update`: four items, none active |
| `test_nested_pages_mark_their_section` | for `order-list`, `order-detail`, `order-update`, `order-workflow`, `order-duplicate`, `order-packing_slip`, `order-create` → only "Orders" active; `address-list`, `address-detail`, `address-update`, `address-create` → "Addresses"; `subscription-list`, `subscription-create`, `subscription-update` → "Subscriptions". Build the kwargs like `AccessMatrixTests.build` in `test_access.py`; every label is `str(customer)` |
| `test_pages_without_a_customer_have_no_bar` | `navbar(...) is None` on `customer-list`, `customer-create`, `orders-list`, `orders-create`, `subscriptions-list` |
| `test_child_buttons_are_gone` | `customer-detail` html has no `cv-key="orders"`, `cv-key="subscriptions"`, `cv-key="addresses"`; it still has `cv-key="update"` |
| `test_bar_is_hidden_in_print` | `order-packing_slip` html contains `class="cv-tabler-navbar container-xl d-print-none` |
| `test_visible_items_match_what_the_user_may_open` | for each of `alex`, `sam`, `kim` and each of `self.mine`, `self.other`: `openable = [u for u in section_urls(c) if get(u).status_code == 200]`; every page in `openable` has a bar whose hrefs `== openable`. Use `subTest(user=..., customer=...)` |
| `test_name_with_markup_is_escaped` | a customer created with name `<b>A & B</b>`: detail html contains `&lt;b&gt;A &amp; B&lt;/b&gt;` inside the bar, and no `<b>A` |
| `test_empty_section_stays_visible` | a customer with no subscriptions: "Subscriptions" is among the item texts |
| `test_invalid_nested_form_keeps_the_bar` | POST to `order-create` of `self.mine` with `{}`: status 200, bar present, only "Orders" active |
| `test_modal_delete_has_no_bar` | GET `customer-delete` as a modal request: `navbar(...) is None`. Take the way to issue a modal request from `../django-crud-views/tests/test1/test_navbar_templates.py` |

- [ ] **Step 2: Run them and see them fail**

Run: `uv run python example/manage.py test sales.tests.test_navbar`
Expected: FAIL, the positive tests with `TypeError: 'NoneType' object is not subscriptable` (no bar yet); `test_child_buttons_are_gone` on the `cv-key="orders"` assertion.

- [ ] **Step 3: Declare the bar**

In `example/sales/views/customers.py`, after `cv_customer`:

```python
customer_navbar = NavBar(
    viewset="customer",
    items=[
        NavItem(key="detail", label=_("Details")),
        NavItem(child="order"),
        NavItem(child="subscription"),
        NavItem(child="address"),
    ],
)


class CustomerNavbarMixin(CrudViewNavBarMixin):
    cv_navbar = customer_navbar
```

- [ ] **Step 4: Attach it and remove the buttons**

`CustomerNavbarMixin` goes first in the bases of:

- `customers.py`: `CustomerDetailView`, `CustomerUpdateView`, `CustomerDeleteView`
- `orders.py`: `OrderListView`, `OrderDetailView`, `OrderCreateView`, `OrderUpdateView`, `OrderDeleteView`
- `order_actions.py`: `OrderWorkflowView`, `OrderPackingSlipView`, `OrderDuplicateView`
- `addresses.py`: `AddressListView`, `AddressDetailView`, `AddressCreateView`, `AddressUpdateView`, `AddressDeleteView`
- `subscriptions.py`: `SubscriptionListView`, `SubscriptionCreateView`, `SubscriptionUpdateView`, `SubscriptionDeleteView`

Not on `AddressMakeDefaultView`, `AllOrdersListView`, `AllOrdersCreateView`, `AllSubscriptionsListView`, `RunSubscriptionsView`, `CustomerListView`, `CustomerCreateView`.

In `customers.py`: delete the three `ChildContextButton` entries and the now unused import, and set on `CustomerDetailView`:

```python
cv_context_actions = ["home", "update", "delete"]
cv_context_actions_inline = ["update"]
```

- [ ] **Step 5: Run the example suite and the check**

Run: `uv run python example/manage.py test django_tabler dashboard sales catalog roastery shipping showcase` and `uv run python example/manage.py check --fail-level WARNING`
Expected: all pass, the check prints no `viewset.E28x`.

If `test_visible_items_match_what_the_user_may_open` fails, do not weaken it and do not change permissions: it means upstream's item admission and the request's authorization disagree for that role. Record the role, customer and URL, and stop for a decision; it is a candidate upstream finding.

An existing test that asserted on the removed buttons is updated to the bar's link instead.

- [ ] **Step 6: Update the findings document**

In `docs/crud_views_upstream_findings_roastery.md`:

- Summary row 23, last cell: `parent gate implemented upstream (#336) and adopted; child sections: upstream object navbar (#381, phase 06.40 branch, issue still open) adopted for the customer, the three child buttons removed`.
- Finding 23, first bullet: replace the "**Not addressed:** ..." sentence with one saying the section navigation is implemented on the branch `gsd/phase-06.40-object-navbar-opt-in-section-navigation-381` for issue #381, which is open and has no pull request yet.
- Finding 23: a new bullet "**Child sections adopted here (2026-11-19):**" naming `customer_navbar` / `CustomerNavbarMixin` in `example/sales/views/customers.py`, the pages that carry it, the removed buttons, the theme block (`page_header_before`, stock templates, no override), the test file, and that the customer's name shows twice on its own pages by decision. Add that this supersedes the "keep downstream" outcome of #363 and that the experiment branch stays unmerged.
- "Not shown in the demo": rewrite the "Tabs for a customer's orders, addresses and subscriptions" bullet: shown since 2026-11-19 as the object navbar (#23); green lots keep context buttons on purpose.
- New finding `### 36. The object navbar has no class keys`, after finding 35, in the document's bullet format (What happened / Where / What we do / Suggested upstream change / Severity: cosmetic): `nav nav-pills`, `cv-navbar mb-3` and the leaf classes are fixed in `crud_views/tags/navbar*.html`, and the reference says "No new button-class keys are introduced", so a theme restyles the bar only with CSS or an override; suggested: keys such as `navbar:wrapper`, `navbar:identity`, `navbar:nav`, `navbar:link`. Add its summary row.

- [ ] **Step 7: Commit**

```bash
git add example/sales docs/crud_views_upstream_findings_roastery.md
git commit -m "Adopt upstream object navbar (#381) for the customer: finding 23 child sections, finding 36 logged"
```

---

### Task 3: Browser check and full verification

**Files:**
- Possibly modify: `src/crud_views_tabler/static/crud_views_tabler/crud_views_tabler.css`, `src/crud_views_tabler/templates/crud_views_tabler/page.html` (spacing classes only), `docs/crud_views_upstream_findings_roastery.md`

- [ ] **Step 1: Look at it**

Run `task setup`, start the server on a free port, sign in as `alex` / `demo`. Check customer detail, a customer's order list, an order update form and the packing slip's print preview, each in the sidebar layout and the top-bar layout, light and dark, and at 375 px width.

Pass means: the bar sits above the breadcrumb with even spacing; the active pill is the sienna primary with readable text in both themes; items wrap without horizontal scroll at 375 px; icons align with their labels; the print preview has no bar.

- [ ] **Step 2: Fix what fails, in this order**

Spacing: the utility classes on the theme's wrapper. Anything else: a rule in `crud_views_tabler.css` scoped under `.cv-tabler-navbar`, with a sentence added to finding 36 naming the rule and the defect. No template override. If nothing fails, change nothing.

- [ ] **Step 3: Run everything**

Run: `task test`
Expected: every suite passes and the check is clean.

- [ ] **Step 4: Commit (only if Step 2 changed something)**

```bash
git add src/crud_views_tabler docs/crud_views_upstream_findings_roastery.md
git commit -m "Theme: object navbar spacing and colours on the Tabler page (finding 36)"
```

Report what was checked in the browser and what, if anything, could not be checked.
