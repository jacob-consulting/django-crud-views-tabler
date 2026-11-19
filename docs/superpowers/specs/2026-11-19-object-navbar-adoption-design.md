# Object navbar adoption (finding 23, upstream #381): design

Date: 2026-11-19. Status: approved and implemented on 2026-11-19.

## Intent

Finding 23 in `docs/crud_views_upstream_findings_roastery.md` has one open half: "no page tabs for children". Upstream
now ships an opt-in object navbar (`crud_views.lib.navbar`: `NavBar`, `NavItem`, `CrudViewNavBarMixin`, the
`{% cv_navbar %}` tag; reference in `../django-crud-views/docs/reference/navbar.md`). The Acme demo adopts it for the
customer, the Tabler theme places it, and the finding is closed.

## Goals

- Every customer page and every page nested under a customer shows one bar: the customer's identity and the links
  Details, Orders, Subscriptions, Addresses, with the current section marked.
- The theme places the bar for any project that uses `crud_views_tabler/page.html`; the example adds nothing to place it.
- Finding 23 records the adoption.

## Non-goals

- Green lots and cupping sessions keep their context buttons, so the demo shows both styles.
- No merge or reuse of `experiment/customer-section-navigation-06-33`; that branch stays as it is.
- No change to the application menu (`acme_nav.py`), breadcrumbs or permissions.
- No upstream change: both sibling checkouts are read-only.

## Anti-goals

- A copied or overridden navbar template in the theme. Overrides drift from upstream silently.
- A bar on pages that have no customer (customer list, customer create, the top-level "all orders" and "all
  subscriptions" lists). The last two are not children of `customer`; attaching the mixin there is an error upstream.

## Approaches

Decided in conversation on 2026-11-19; the user took all five recommendations.

| Decision | Chosen | Rejected, and why |
|---|---|---|
| Placement | Above the page header, upstream's default order | Top of the page body: the customer's name lands below the page title. Split (identity in `pretitle`, links below the header): the two halves are separated by title and buttons |
| Look | Upstream's stock markup (`nav nav-pills`), CSS only if a browser check shows a defect | Tabler underline tabs: needs an override of `navbar_items.html`, because upstream has no class key for the bar |
| Reach | Customer detail and update plus every nested order, address and subscription page | Detail page only: loses the point, which is orientation on nested pages |
| Name shown twice on the customer's own pages | Accepted | Retitling the detail page "Details": loses the avatar header |
| Child context buttons on customer detail | Removed; the bar replaces them | Keeping both: the same three links twice on one page |

## Design

**Declaration** (`example/sales/views/customers.py`, next to `cv_customer`):

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

Child labels and icons come from each ViewSet (plural name, header icon). The order matches today's buttons.

**Attachment.** `CustomerNavbarMixin` goes before the concrete base on:

- customer: detail, update, delete (the delete modal omits the bar by itself);
- order: list, detail, create, update, delete, workflow, packing slip, duplicate;
- address: list, detail, create, update, delete;
- subscription: list, create, update, delete.

Not on `AddressMakeDefaultView` (an action, it renders no page), nor on the views of `cv_all_orders` and
`cv_all_subscriptions`.

**Buttons.** The three `ChildContextButton`s leave `cv_customer.context_buttons`, and `orders`, `subscriptions`,
`addresses` leave `cv_context_actions` and `cv_context_actions_inline` on `CustomerDetailView`.

**Placement.**

- `django_tabler/layouts/app.html` gets one empty block, `page_header_before`, inside `.page-wrapper` before
  `.page-header`.
- `crud_views_tabler/page.html` fills it: a `container-xl d-print-none` wrapper with top spacing, containing
  `{% block cv_navbar %}{% cv_navbar %}{% endblock %}`. The wrapper is emitted only when `cv_navbar` is truthy, so
  pages without a bar keep their markup byte for byte. `d-print-none` covers the packing slip.

**Look.** Stock templates, no override. Check customer detail, a nested list and a nested form in the browser, in the
light and the dark layout and at phone width. A defect is fixed in `crud_views_tabler.css`; each rule gets a findings
entry in the same commit.

**Docs.**

- Finding 23: the "Not addressed" sentence is rewritten and a dated "Adopted here" entry added. Upstream issue #381
  is open with no pull request, so the entry cites the branch
  `gsd/phase-06.40-object-navbar-opt-in-section-navigation-381`, not a merge. The summary table at the top follows.
- A new finding: the navbar has no class key (`nav nav-pills` and the wrapper classes are fixed in the templates), so
  a theme can only restyle it with CSS or an override.
- `docs/crud_views_tabler.md` and the template chain paragraph in `CLAUDE.md` name the new block.

## Tests

- `example/sales/tests/`: the bar appears on customer detail, a nested order list and a nested order detail with
  the right active item; it is absent on customer list and the all-orders list; the three buttons are gone from
  customer detail; per role (alex, sam, kim) the visible items match what `test_access.py` says they may open.
- `tests/crud_views_tabler/`: a page without a navbar renders no wrapper.
- `task test` and `manage.py check --fail-level WARNING` pass.

## Left to the builder

- The wrapper's exact spacing classes.
- Whether the theme test needs a nested ViewSet in its test app or can assert on the template alone.
- The number of the new finding and its place in the document.
