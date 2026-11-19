# Acme Roasters: a real-looking demo app for the Tabler theme

Date: 2026-11-04. Status: draft for review.

## Intent

A developer lands on django-crud-views (GitHub or docs), clicks through its example app and thinks "this saves me a
lot of time — but what about theming?". Upstream's example has a *Theme* page
(`examples/bootstrap5/theming/`, `TABLER_DEMO_URL`) that will link here. This app has to answer that question in
two ways at once:

1. **It looks like a real product.** A believable back-office for a specialty coffee roastery, not a test form.
2. **Getting there took very little.** The app code knows nothing about Tabler; the theme is a small app listed
   before `crud_views`. The demo makes that *visible*, in the app itself.

The demo will be hosted (render.com), so nobody has to install it to try it. Deployment itself is out of scope here
(it waits for django-crud-views 1.0.0rc1).

The current demo (`customers`, `catalog` with one kitchen-sink `Product` form) was a good test bench but looks
awful as an application. It is replaced.

## Goals

- A coherent roastery back-office: customers, orders, products, green coffee lots, cupping, shipments.
- Use as many django-crud-views features as fit the domain naturally, each with a real job (feature map below).
- Every crud_views page shows its own code next to it (“Show code” panel), and one page shows the whole theme.
- Seed data that makes every page look lived-in on first load.
- Record every place where theming needed a template override or a workaround instead of an upstream hook, as
  upstream issue candidates (see “Upstream findings”).

## Non-goals

- render.com deployment, `render.yaml`, production settings.
- A docs site (mkdocs/readthedocs) for the theme. General theming docs belong upstream; `docs/crud_views_tabler.md`
  stays the long-form write-up. Revisit when it is decided whether `django_tabler`/`crud_views_tabler` get their
  own repos.
- i18n of the demo (English only). *My call.*
- A storefront / customer-facing shop. This is the staff back-office.

## Anti-goals (would make it a failure even if it works)

- App code (`example/*/views.py`, forms, models) that imports from or mentions `django_tabler` /
  `crud_views_tabler` beyond settings and the project templates. The point is that the theme is invisible to app
  code. Plain Django views (dashboard) may use Tabler markup in their templates — that is the project's own look.
- Feature-demo pages with no business meaning ("Formset example #2"). Each feature serves the roastery.
- New theme template overrides added just to make one page pretty when an upstream hook would do. If an override is
  unavoidable, it goes in the theme (not the example) and gets an upstream finding.
- Losing the crispy pack coverage that `catalog` currently pins.

## Constraints

- Django 6.1, Python 3.14, Tabler 1.6.1 from jsDelivr, as today.
- django-crud-views from the sibling checkout `../django-crud-views`; build against branch
  `feature/examples-pre-1.0-restructure` (it is what 1.0.0rc1 will contain). Version string there is still 0.30.0.
- django-crud-views extras needed: `workflow` (django-fsm-2), `polymorphic`, `guardian`, `ordered`. Object detail
  is built in (`crud_views_object_detail`).
- django-crud-views-extensions from the sibling checkout `../django-crud-views-extensions` (typeahead,
  datetimepicker), as an editable path dependency like crud_views.
- `src/django_tabler` must not depend on django-crud-views; `src/crud_views_tabler` must not require
  django-crud-views-extensions (anything for the extensions is optional, see below).
- Tabler icon SVG paths come from `<tabler archives>/tabler-icons-3.49.0/svg/` into `django_tabler.icons.ICONS`;
  licensed archives are reference only, never committed wholesale.
- All pages require login (`LoginRequiredMiddleware`), as today.

## Decided

- **Domain:** specialty coffee roastery “Acme Roasters”, wholesale to cafés plus direct consumers with
  subscriptions. (User's choice from three options.)
- **Look:** as in the approved mockups (`.superpowers/brainstorm/*/content/roastery-screens.html`): Tabler vertical
  dark sidebar, sections Sales / Catalog / Roastery / Developer, dashboard with stat cards, customer detail with
  property grid + tabs, order page with workflow steps and line-item formset, product cards per type, lot → cupping
  → scores with a code panel. A warm primary colour (sienna `#a0522d` in the mockup). (User: “looks awesome”.)
- **Code panel in the app, not a docs site.** Each crud_views page gets a “Show code” panel with that page's
  `models.py` / `views.py` / forms / templates; a “How this is themed” page shows the theme itself. (User agreed.)
- **The theme tests get their own app**, independent of the demo, so the demo can change freely. (User.)
- **The kitchen-sink product form survives** as a “Form showcase” page under Developer, keeping
  `docs/crispy_tabler_coverage.md` and its tests valid.

## The application

### Apps (replacing `customers` and `catalog`)

| App | Models | Purpose |
|---|---|---|
| `dashboard` | – | start page (plain Django view), demo users seed; keeps the user list |
| `sales` | `Customer`, `Address`, `Order`, `OrderLine`, `CustomerSubscription` | customers, their orders and subscriptions |
| `catalog` | `Category` (ordered), `Product` (polymorphic) → `Beans`, `Equipment`, `Subscription`, `Origin`, `FlavorNote` | what is sold |
| `roastery` | `GreenLot`, `CuppingSession`, `CuppingScore`, `RoastBatch` | buying, tasting and roasting green coffee |
| `shipping` | `Shipment` (a `Resource`, not ORM) | courier tracking from a fake API |
| `showcase` | `ShowcaseItem` (today's `catalog.Product` with its `Category`/`Tag`/`Channel`, renamed) | crispy pack coverage form |
| theme test app | see “Theme tests” | not in the demo |

Names of models and fields are the builder's call within this outline.

### Domain sketch

- **Customer**: name, kind (`wholesale` / `consumer`), contact, email, phone, country/city, owner (staff user, the
  account manager), notes, created. Wholesale-only fields: company, VAT id, price tier (A/B/C with a discount),
  payment terms. → *conditional group* on `kind`.
- **Address** (child of Customer): label, street, zip, city, country, is_default.
- **Order** (child of Customer): number, state (FSM: draft → confirmed → roasted → shipped → delivered; cancel from
  draft/confirmed), ship-to address (from the customer's addresses), requested roast date, notes, totals computed
  from lines and the customer's tier.
- **OrderLine** (formset of Order): product, quantity, grind (whole bean / filter / espresso) and bag size
  (250 g / 1 kg) — the last two only meaningful for Beans.
- **Orders have two ViewSets** (*my call*): the nested one under Customer owns detail, edit, delete and workflow
  (breadcrumb “Customers › Bean & Bloom Café › Order #1045”); a top-level “Orders” list (sidebar Sales → Orders)
  lists all orders the user may see and has its own create with the typeahead customer picker, redirecting into the
  nested order after save. Rows link to the nested detail. For Guardian, the top-level queryset is filtered to the
  customers the user has object permission on (Orders get no grants of their own).
- **CustomerSubscription** (child of Customer, *my call*): subscription product, start date, next delivery,
  active/paused. Feeds the dashboard stat, the product card's subscriber count, the customer's Subscriptions tab and
  a top-level Sales → Subscriptions list. The no-object custom form view **“Run subscriptions”** creates draft
  orders for all active subscriptions due on or before a chosen date and moves their next delivery on.
- **Product** (polymorphic): name, slug, SKU, price, stock, active, category, description.
  - **Beans**: origin (FK `Origin`: country/region), process (washed/natural/honey/anaerobic), altitude, roast level,
    flavor notes (M2M), linked green lot (optional).
  - **Equipment**: brand, warranty months, weight.
  - **Subscription**: interval (weekly / 2 weeks / monthly), bags per delivery, bag size.
- **Category**: ordered (up/down), drives the sidebar/filters.
- **GreenLot**: code (e.g. `CO-24-017`), origin, farm/producer, variety, process, harvest year, kg purchased, kg on
  hand, price/kg, arrival date.
- **CuppingSession** (child of GreenLot): date, notes, invited tasters (users).
- **CuppingScore** (formset of CuppingSession): taster, aroma, flavor, acidity, body, aftertaste, balance, overall
  → total (SCA-style, 0–100). Session/lot average shown.
- **RoastBatch**: green lot, roast date, profile name, green kg in, roasted kg out (→ weight loss %), roaster user,
  orders it fulfils (optional M2M).
- **Shipment** (Resource): tracking number, carrier, status, ETA, events — served from a fixed in-code dataset that
  pretends to be a courier API, keyed to seeded orders.

### Feature map (each feature, where it does its job)

| crud_views feature | Where |
|---|---|
| ViewSet list/detail/create/update/delete, tables, filters | every model |
| **Nested** (`ParentViewSet`) | Customer → Address, Customer → Order; GreenLot → CuppingSession (two levels with scores below) |
| **Formsets** (`FormSetMixin`, `InlineFormSet`) | Order lines; Cupping scores |
| **Formsets + Conditional** | Order lines: grind/bag size only for beans products, if expressible; otherwise a conditional formset elsewhere (e.g. subscription delivery schedule). Builder's call. |
| **Conditional** (`ConditionalGroupModelForm`) | Customer form: wholesale group on `kind` |
| **Workflow** (`crud_views_workflow`) | Order state, transition buttons, history; badges in lists |
| **Polymorphic** | Product (create-select → type form) |
| **Object detail** (`cv_property_display`) | Customer (split-card), Product (per type), GreenLot; use at least two layout packs |
| **Card view** | Products list as cards (as in the mockup); a table view may exist too |
| **Ordered** (up/down) | Category |
| **Guardian** | Customer per-object permissions: account managers see/edit only their customers |
| **Resources** | Shipments (list + detail from the fake API) |
| **Custom form view** | e.g. “Duplicate order” / “Reorder” on an order; a no-object one such as “Run subscriptions” |
| **Action view (POST)** | e.g. “Mark default address”, “Restock” |
| **Context buttons** | e.g. “Packing slip” on order detail |
| **Action menus** (⋯) | lists with many actions (orders, customers) |
| **Disabled actions** (`cv_action_enabled`, `cv_inaccessible_actions="disable"`) | Edit/delete order disabled once shipped; actions the current demo user may not use show disabled |
| **Delete protection / related objects** | Customer with orders: PROTECT; green lot delete previews cascaded sessions |
| **Messages** | after transitions and custom actions |
| **Breadcrumbs** | everywhere, through the nests |
| **Label modes & icons** | Tabler icons on all actions; form buttons “both” (theme default) |
| Extensions: **typeahead** | customer picker on order create (from the order list), product picker in order lines if practical |
| Extensions: **datetimepicker** | requested roast date, roast date, cupping date |

If a feature does not fit cleanly in the builder's judgement, it may be dropped, but the drop is listed in the
handover with the reason. Nested, formsets, workflow, polymorphic, object detail, guardian and resources are
must-haves.

### Demo users and permissions

The login page lists the demo accounts with a one-click fill (passwords shown; it is a demo):

- **Alex, owner**: everything.
- **Sam, account manager** (sales): sees only the customers Guardian assigns to Sam, plus their orders; no roastery
  edits. Shows Guardian and disabled actions.
- **Kim, head roaster**: roastery full access, orders read-only (confirm → roasted transition allowed), no
  customers edit.

Exact permission sets are the builder's call within that intent. *My call; user asked for creativity.* The existing
`admin/admin` superuser from the Taskfile stays.

### Dashboard

Plain Django view (no crud_views), Tabler markup in its template: stat cards (revenue 30 days, open orders,
active subscriptions, green stock), “orders to roast this week” table, recent cupping scores, and one small chart
(revenue per week) via ApexCharts from jsDelivr, as Tabler's own demo uses. *Chart is my call.*

### Developer section

- **Form showcase**: today's kitchen-sink form, renamed app `showcase`. `docs/crispy_tabler_coverage.md` and the
  coverage tests are updated for the new names; the coverage itself must not shrink.
- **Show code panel**: on every crud_views page (via `crud_views_tabler/page.html` or rather a project template
  block — see below), a collapsible card listing that view's app files (`models.py`, `views.py`, `forms.py`,
  templates) with Pygments highlighting. Pattern borrowed from upstream's example-only `snippet_panels` tag; we
  write our own in the example project (Pygments becomes an example dependency). It must live in the example
  project, not in the theme packages.
- **How this is themed**: one page showing the theme's file list with line counts and the source of
  `crud_views_tabler/apps.py`, `buttons.py`, the template overrides, `tabler-adapters.js`, and the relevant
  `settings.py` lines (`INSTALLED_APPS` order, `CRUD_VIEWS_EXTENDS`, `CRISPY_TEMPLATE_PACK`). Headline: “the whole
  theme is N files / M lines; your app code is unchanged”. Numbers computed at render time, not hard-coded.

Where the panel hooks in: `crud_views_tabler/page.html` should not grow demo-only code. Preferred: the example
sets `CRUD_VIEWS_EXTENDS` to its own `example/templates/project/crud_views.html` that extends
`crud_views_tabler/page.html` and adds the panel in a block. Builder confirms a suitable block exists or notes the
gap as an upstream/theme finding.

### Seed data

One command (or the existing three replaced) that builds a coherent world: ~25 customers (mixed kinds, two with
Sam as owner), addresses, ~80 orders across all states over the last 3 months, ~30 products across types, ~8 green
lots with cupping sessions and scores, roast batches, shipments matching shipped orders. Deterministic (fixed
random seed), with a `--reset` flag that deletes the demo data and rebuilds the same world, so a hosted instance
can be reset by a scheduled command later (*my call*). Realistic names: real coffee origins, plausible café names,
invented people. The Taskfile's `seed:*` tasks are updated. Hardening a public instance against shared write
access (scheduled resets, guarding destructive actions) belongs to the deployment work, not here.

### Theme tests

`crud_views_tabler`'s tests stop importing from the demo. They get a minimal test app with a small model + ViewSet
covering what the tests exercise today (list with filter/sort/pagination, detail, create/update, delete with
related objects and protection, disabled actions, action menus). Placement: a test-only app under `tests/`
(e.g. `tests/crud_views_tabler/` with its own settings, run by pytest like the crispy pack) — *my call*;
CLAUDE.md's commands are updated accordingly. The existing assertions are carried over, not rewritten from
scratch.

## Theme work this will trigger

The demo will hit crud_views templates the theme has never rendered: object detail layouts, workflow badge/history,
polymorphic create-select, guardian manage, formset control rows, conditional toggle groups, card view, custom form
views, and the extensions' typeahead (Bootstrap `input-group`/`dropdown-menu`, swappable via
`CRUD_VIEWS_TYPEAHEAD["TEMPLATE"]`). Tabler is Bootstrap 5 underneath, so much will just work.

`../django-crud-views` and `../django-crud-views-extensions` are **read-only** for this work (user). Gaps there
are worked around here and recorded as findings; if the extensions package breaks against the pre-1.0 branch, that
is a finding too, and the affected feature may be dropped from the demo with a note.

Rule: fix in this order — (1) an existing upstream hook (class keys, settings, blocks), (2) Tabler CSS in the theme's existing
stylesheet, (3) a new template override in `crud_views_tabler` as last resort. Every (2)/(3) gets an upstream
finding. A Tabler typeahead template, if needed, ships in `crud_views_tabler` as an optional template selected by
setting, without importing the extensions package.

New Tabler icons go into `django_tabler.icons.ICONS` from the licensed SVG source; `crud_views_tabler.W001` must
stay clean.

## Upstream findings

A new file `docs/crud_views_upstream_findings_roastery.md` collects candidates as they come up, each with: what
happened, where (file/line in upstream), what the theme did instead, suggested upstream change, severity
(blocker / annoyance / cosmetic). Not filed as issues; the user triages later. Already known:

- The “show code” `snippet_panels` tag is example-only upstream; every theme/demo has to copy it (the extensions
  repo already did). Candidate: ship it (or a documented recipe) in the library.
- Upstream's tooltip recipe (`docs/reference/javascript.md#tooltips`) still says to replace `init` (from the
  2026-11-04 tidy-up; also in `docs/crud_views_upstream_status.md`).
- `crud_views.lib.crispy.Column1..12` hard-code `col-md-N` (fine for Tabler, a note for non-Bootstrap themes).
- Workflow `BadgeEnum` values are Bootstrap colour names; Tabler has its own `bg-*-lt` palette (check while
  building).

## Left to the builder

- Exact model fields, names, URL paths, table columns, filters.
- Which object-detail layout pack per model.
- How totals/discounts are computed (property vs stored).
- Breaking the work into phases (suggested: theme tests split → apps and seed → features → developer section →
  polish and findings).
- Whether the mockup HTML is kept in the repo for reference (`.superpowers/` is currently not git-ignored; it should
  be).

## Acceptance

- `task reset` then `task up` gives a populated app; every sidebar entry works for Alex; Sam and Kim see the reduced
  views described above.
- Every must-have feature is reachable in at most three clicks from the dashboard.
- Django tests, pytest (crispy pack + theme tests), and `manage.py check --fail-level WARNING` pass.
- No JS console errors on any page (checked in a real browser).
- The “How this is themed” page renders with computed file/line counts.
- `docs/crud_views_upstream_findings_roastery.md` exists and lists every override/workaround added.
- README and CLAUDE.md describe the new apps, commands and test layout.
