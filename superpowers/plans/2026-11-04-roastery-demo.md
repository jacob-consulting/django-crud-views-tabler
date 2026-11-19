# Acme Roasters Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the `customers`/`catalog` test-bench demo with “Acme Roasters”, a coffee roastery back-office that
uses most django-crud-views features under the Tabler theme and shows its own code.

**Architecture:** The theme tests move to a pytest-run test app so the demo can change freely. The example project
gets new apps `sales`, `catalog` (rebuilt), `roastery`, `shipping`, `showcase` (the old kitchen-sink form) next to
`dashboard`; each app owns its models, ViewSets, tests and a `seed.py`. A project template between
`crud_views_tabler/page.html` and the views adds the “Show code” panel. Gaps in upstream are worked around in the
theme or example and logged in a findings document; the sibling repos are read-only.

**Tech Stack:** Django 6.1, Python 3.14, django-crud-views (sibling checkout, branch
`feature/examples-pre-1.0-restructure`) with extras `workflow`, `polymorphic`, `guardian`, `ordered`;
django-crud-views-extensions (sibling checkout, `main`); django-tables2, django-filter, crispy-forms with the
`crispy_tabler` pack; Tabler 1.6.1 (jsDelivr), ApexCharts (jsDelivr); Pygments; pytest + pytest-django.

**Spec:** `docs/superpowers/specs/2026-11-04-roastery-demo-design.md`

## Global Constraints

- `../django-crud-views` and `../django-crud-views-extensions` are read-only. Never edit, commit or switch branches there.
- App code (`example/<app>/models.py`, `views.py`, `forms.py`) never imports `django_tabler` or `crud_views_tabler`.
  Icon names in app code are strings (`"tabler:<name>"`).
- `src/django_tabler` must not import crud_views; `src/crud_views_tabler` must not import the extensions packages.
- Theme fix order: (1) existing upstream hook (class keys, settings, blocks), (2) CSS in
  `src/crud_views_tabler/static/crud_views_tabler/crud_views_tabler.css`, (3) new override template in
  `src/crud_views_tabler/templates/` as a last resort. Every (2)/(3), and every upstream bug or awkwardness, gets an
  entry in `docs/crud_views_upstream_findings_roastery.md` in the same commit.
- New icons: copy the SVG path data from `~/projects/tabler/tabler-icons-3.49.0/svg/outline/<name>.svg` into
  `django_tabler.icons.ICONS`; never commit the archive. `manage.py check --fail-level WARNING` (incl.
  `crud_views_tabler.W001`) stays clean.
- All pages require login; English only; demo brand “Acme Roasters”, primary colour sienna `#a0522d`.
- Demo accounts: `alex` (owner), `sam` (account manager), `kim` (head roaster), password `demo` for all; `admin/admin`
  superuser from the Taskfile stays.
- The look follows the approved mockup `.superpowers/brainstorm/127599-1793779096/content/roastery-screens.html`
  (not in git; open it in a browser).
- Test commands (after Task 1):
  - `uv run python example/manage.py test dashboard sales catalog roastery shipping showcase`
  - `uv run --group test pytest` (crispy pack) and
    `uv run --group test pytest tests/crud_views_tabler --ds tests.crud_views_tabler.settings` (theme); `task test`
    runs everything
  - `uv run python example/manage.py check --fail-level WARNING`

## Review Focus

1. Sam opens a URL of a customer, address or order Sam has no Guardian grant for, or a top-level orders/subscriptions
   list → 403/404 and never sees other reps' rows. Tests in Tasks 5, 6, 7.
2. Someone opens the edit/delete URL of a shipped, delivered or cancelled order directly → 403, not an edit form.
   Test in Task 6.
3. An order line for a non-beans product is posted with grind/bag size set, or an order is confirmed with no lines →
   grind/bag cleared on save; confirm refused with a message. Tests in Task 6.
4. “Run subscriptions” run twice for the same date → the second run creates no orders. Test in Task 7.
5. `seed_demo` run on a populated database without `--reset` → refuses with a clear message and changes nothing;
   `--reset` twice → identical row counts. Test in Task 10.

---

### Task 1: Theme tests get their own app

Move the theme's Django tests off the demo so later tasks can delete `customers`.

**Files:**
- Create: `tests/crud_views_tabler/__init__.py`, `settings.py`, `urls.py`, `testapp/` (`__init__.py`, `apps.py`,
  `models.py`, `views.py`, `urls.py`, `migrations/0001_initial.py`, `templates/testapp/customer_card.html`),
  `test_theme.py`
- Move: `src/crud_views_tabler/tests.py` → `tests/crud_views_tabler/test_theme.py`
- Modify: `example/dashboard/tests.py` (receives `test_dashboard_icons_still_render`), `pyproject.toml`
  (`testpaths = ["tests/crispy_tabler"]`), `Taskfile.yaml` (new `test` task), `CLAUDE.md` (commands)

**Interfaces:**
- Produces: test app label `testapp` with model `testapp.Customer` (same fields as today's `customers.Customer`) and
  views `CustomerListView`, `CustomerCardListView`, `CustomerDetailView`, `CustomerCreateView`,
  `CustomerUpdateView`, `CustomerDeleteView` with URL names `customer-list`, `customer-card`, … exactly as today.

- [ ] **Step 1:** Copy `example/customers/{models,views,urls}.py` and its card template into `testapp/` unchanged
  except the app label. Permission strings in the moved tests change from `customers` to `testapp`
  (e.g. `content_type__app_label="testapp"`). Generate the migration with a throwaway `makemigrations` against the
  test settings.
- [ ] **Step 2:** `tests/crud_views_tabler/settings.py`: copy the crud_views-relevant parts of
  `example/config/settings.py` (INSTALLED_APPS without `dashboard`/`customers`/`catalog`, plus
  `tests.crud_views_tabler.testapp`; middleware incl. sessions/messages/auth; `CRUD_VIEWS_EXTENDS`,
  `CRISPY_TEMPLATE_PACK`, `DJANGO_TABLES2_TEMPLATE`; in-memory SQLite; `LOGIN_URL`). `urls.py` includes the test app
  URLs, `accounts/login/` and a stub `dashboard:index` route if the page shell reverses it.
- [ ] **Step 3:** Two pytest runs, one per settings module (Django settings can't change mid-session):
  `pyproject.toml` keeps `DJANGO_SETTINGS_MODULE = "tests.crispy_tabler.settings"` and sets
  `testpaths = ["tests/crispy_tabler"]`; the theme suite runs with
  `uv run --group test pytest tests/crud_views_tabler --ds tests.crud_views_tabler.settings`. The Taskfile `test`
  task runs both pytest commands, the example's `manage.py test`, and the check.
- [ ] **Step 4:** Move `test_dashboard_icons_still_render` into `example/dashboard/tests.py`. In
  `LayoutBoundaryTests.test_src_does_not_import_the_example` drop the `allowed` exception (nothing under `src/`
  imports the example any more) and widen the pattern to
  `(catalog|customers|dashboard|config|sales|roastery|shipping|showcase)`.
- [ ] **Step 5: Run** both pytest commands → all moved theme tests pass, and the 34 crispy tests pass;
  `uv run python example/manage.py test dashboard` passes; `grep -rn "from customers" tests src` → nothing.
- [ ] **Step 6:** Delete `src/crud_views_tabler/tests.py`, update CLAUDE.md commands, add a `test` task to
  `Taskfile.yaml` that runs both suites and the check. Commit `Move crud_views_tabler tests to their own test app`.

### Task 2: Rename `catalog` to `showcase`

The kitchen-sink form becomes the Developer → Form showcase page; frees the name `catalog`.

**Files:**
- Move: `example/catalog/` → `example/showcase/` (app label `showcase`, model `ShowcaseItem` from `Product`, keep
  `Category`/`Tag`/`Channel` as `ShowcaseCategory`/`ShowcaseTag`/`ShowcaseChannel`), new `0001_initial` migration
  (delete the old one; the demo DB is recreated by `task reset`)
- Modify: `example/config/settings.py`, `example/config/urls.py`, nav menu, `docs/crispy_tabler_coverage.md`
  (names, URLs, commands), `Taskfile.yaml` (`seed:catalog` → `seed:showcase`)

**Interfaces:**
- Produces: URL prefix `showcase/`, ViewSet name `showcaseitem`, command `seed_demo_showcase`.

- [ ] **Step 1:** Rename and rewrite references; the coverage tests in `showcase/tests.py` keep every assertion, with
  only names/URLs changed.
- [ ] **Step 2: Run** `uv run python example/manage.py test showcase` → same test count as `catalog` had, all pass.
- [ ] **Step 3:** Commit `Rename the kitchen-sink catalog app to showcase`.

### Task 3: Dependencies, settings, project shell, demo users

**Files:**
- Modify: `pyproject.toml`, `example/config/settings.py`, `example/config/urls.py`,
  `example/templates/django_tabler/includes/{nav_menu,brand,site_name}.html`
- Create: `example/templates/project/crud_views.html`, `example/static/acme/acme.css`,
  `example/dashboard/seed.py`, `example/dashboard/management/commands/seed_demo.py`,
  `example/templates/registration/login.html` (extends django_tabler's login, adds the demo-account picker),
  `docs/crud_views_upstream_findings_roastery.md`
- Delete: `example/customers/` (its models move to `sales` in Task 5), `seed_demo_users` command and its Taskfile
  task (replaced by `seed_demo`), `example/db.sqlite3` reference data via `task reset`

**Interfaces:**
- Produces:
  - `example/dashboard/seed.py`: `def seed(rng: random.Random, world: dict) -> None` creates groups `Owner`,
    `Account managers`, `Roasters` and users `alex`, `sam`, `kim` (password `demo`, first names Alex/Sam/Kim),
    stores them in `world["users"] = {"alex": ..., "sam": ..., "kim": ...}`.
  - Every later app adds `example/<app>/seed.py` with the same signature; `seed_demo` calls
    `dashboard, catalog, sales, roastery` in that order (Task 10 adds `--reset`; until then it refuses when users
    `alex/sam/kim` exist).
  - `example/templates/project/crud_views.html` extends `crud_views_tabler/page.html`; it has an empty
    `{% block code_panel %}` that Task 12 fills. `CRUD_VIEWS_EXTENDS = "project/crud_views.html"`.
  - Findings doc format (one `##` per finding): *What happened*, *Where* (upstream path:line on
    `feature/examples-pre-1.0-restructure`), *What we did*, *Suggested upstream change*, *Severity*
    (blocker/annoyance/cosmetic). Seed it with the four known findings from the spec's “Upstream findings”.

- [ ] **Step 1:** Dependencies: `django-crud-views[workflow,polymorphic,guardian,ordered]` (path source unchanged),
  add `django-crud-views-extensions` as editable path source `../django-crud-views-extensions`, `pygments`. `uv sync`.
- [ ] **Step 2:** Settings: INSTALLED_APPS adds `ordered_model`, `django_fsm`, `crud_views_object_detail`,
  `polymorphic`, `guardian`, then (after `crud_views.apps.CrudViewsConfig`) `crud_views_workflow.apps.CrudViewsWorkflowConfig`,
  `crud_views_polymorphic.apps.CrudViewsPolymorphicConfig`, `crud_views_guardian.apps.CrudViewsGuardianConfig`,
  `crud_views_widget_datetimepicker.apps.CrudViewsWidgetDatetimepickerConfig`,
  `crud_views_widget_typeahead.apps.CrudViewsWidgetTypeaheadConfig`; `crud_views_tabler` stays before
  `crud_views`. Add `AUTHENTICATION_BACKENDS` with `guardian.backends.ObjectPermissionBackend`,
  `ANONYMOUS_USER_NAME = None`, `CRUD_VIEWS_BREADCRUMB_PREFIX = [{"title": "Home", "url_name": "dashboard:index"}]`,
  `CRUD_VIEWS_DATETIMEPICKER = {"DEFAULTS": {"dayOfWeekStart": 1}}`, `STATICFILES_DIRS = [BASE_DIR / "static"]`,
  URL `path("_typeahead/", include("crud_views_widget_typeahead.urls"))`.
- [ ] **Step 3:** Shell: sidebar sections Sales (Customers, Orders, Subscriptions), Catalog (Products, Categories),
  Roastery (Green lots, Roast batches, Shipments), Developer (Form showcase, How this is themed), Users (perm-gated
  as today). Entries for apps that don't exist yet are added by their tasks; this step creates the section headings
  pattern (Tabler `nav-link` subheaders as in the mockup). Brand: `ti-coffee`-equivalent icon `coffee` + “Acme
  Roasters”. `acme.css` sets `--tblr-primary: #a0522d; --tblr-primary-rgb: 160, 82, 45` on `:root` and is loaded
  from the project template, so the layout switch's primary picker still wins when the user sets one (verify in
  the browser; if Tabler's `data-bs-theme-primary` mechanism is the cleaner route, use it and say so in the commit).
- [ ] **Step 4:** Login page: below the form, a card “Demo accounts” listing Alex/Sam/Kim with role and a button
  per account that fills username and password (`demo`) — small inline script, no auto-submit.
- [ ] **Step 5: Test** in `example/dashboard/tests.py`:
  `test_seed_creates_demo_accounts` (after `call_command("seed_demo")`, users `alex`,`sam`,`kim` exist,
  `authenticate(username="sam", password="demo")` is not None, `sam` in group `Account managers`);
  `test_login_page_lists_demo_accounts` (GET `/accounts/login/` contains `Alex`, `Sam`, `Kim` and
  `data-demo-user="sam"`); `test_crud_views_extends_project_template` (`settings.CRUD_VIEWS_EXTENDS ==
  "project/crud_views.html"`). Update `test_example_overrides_the_site_name` to `"Acme Roasters"`.
- [ ] **Step 6: Run** the dashboard tests, pytest, and the check → pass. Commit `Roastery shell: deps, settings, sidebar, demo accounts`.

### Task 4: `catalog` — polymorphic products

**Files:**
- Create: `example/catalog/` (`models.py`, `forms.py`, `views.py`, `urls.py`, `seed.py`, `tests.py`, `admin.py`,
  `templates/catalog/product_card.html`, migrations)
- Modify: nav menu, `seed_demo` order, `django_tabler/icons.py` if icons are missing

**Interfaces:**
- Produces: `Origin(country, region)`, `FlavorNote(name, color)`, `Category` (`OrderedModel`, `name`),
  `Product(PolymorphicModel)`: `name, slug, sku, price: Decimal, stock: int, is_active, category, description`;
  `Beans(Product)`: `origin, process` (washed/natural/honey/anaerobic), `altitude_m, roast_level`
  (light/medium/dark), `flavor_notes` M2M, `green_lot` (nullable FK to `roastery.GreenLot`, string reference; add
  the field in Task 8's migration if the app doesn't exist yet); `Equipment(Product)`: `brand, warranty_months,
  weight_kg`; `Subscription(Product)`: `interval` (weekly/biweekly/monthly), `bags_per_delivery`, `bag_size`
  (250g/1kg). `Product.is_beans: bool` property. ViewSets `cv_product` (name `product`), `cv_category` (name
  `category`). `catalog.seed.seed` puts `world["products"]` (list) in.

- [ ] **Step 1: Tests** (`catalog/tests.py`, logged in as `alex` from `seed_demo`-like fixtures built with
  `dashboard.seed.seed` + `catalog.seed.seed`):
  - `test_card_list_shows_type_badges`: GET product card list contains one card per product and the strings
    `Beans`, `Equipment`, `Subscription`.
  - `test_create_select_then_typed_form`: POST the create-select view with the `Beans` content type → redirect to the
    create view; that form contains `process` and `flavor_notes`, the Equipment form contains `warranty_months`.
  - `test_detail_uses_object_detail_groups`: a Beans detail page contains group titles `Coffee` and `Commerce`
    (titles are this task's choice; assert the ones you define).
  - `test_category_up_down`: POST `category-down` on the first category → it is second.
  - `test_kim_cannot_edit_products`: `kim` gets 403 on product update.
- [ ] **Step 2: Run** `uv run python example/manage.py test catalog` → FAIL (app missing).
- [ ] **Step 3: Implement** with `crud_views_polymorphic.lib` (`PolymorphicContentTypeForm`,
  `PolymorphicCreateSelectViewPermissionRequired`, `PolymorphicCreateViewPermissionRequired`, …Update/Delete/Detail),
  `CardListViewPermissionRequired` as the default list (cards as in mockup tab 4: `card-status-top` colour per
  type, type badge, flavor-note badges, price footer) plus a table list, `ObjectDetailMixin` with
  `cv_property_display` per type (layout pack `tabs-vertical` or `split-card`, your choice), `OrderedUp/Down` views
  for `Category`, filters (type, category, active).
- [ ] **Step 4: Run** the tests → PASS. Open the pages in a browser as `alex`; anything the theme renders badly →
  apply the fix order, log findings.
- [ ] **Step 5:** Commit `Catalog: polymorphic products, ordered categories`.

### Task 5: `sales` — customers and addresses

**Files:**
- Create: `example/sales/` (`models.py`, `forms.py`, `views/customers.py`, `views/addresses.py`, `urls.py`,
  `seed.py`, `tests/test_customers.py`, `admin.py`, migrations)

**Interfaces:**
- Consumes: `world["users"]` (Task 3).
- Produces: `Customer`: `name, kind` (`wholesale`/`consumer`), `contact_name, email, phone, city, country, owner`
  (FK user, nullable), `company, vat_id, price_tier` (A/B/C, nullable), `payment_terms` (nullable), `notes,
  created_at`; `Customer.discount -> Decimal` (A 0.20, B 0.12, C 0.05, consumer 0). `Address`: `customer` FK
  CASCADE, `label, street, zip_code, city, country, is_default`. ViewSets: `cv_customer = GuardianViewSet(model=Customer, name="customer", icon_header="tabler:building-store")`,
  `cv_address = ViewSet(model=Address, name="address", parent=ParentViewSet(name="customer"))`.
  Guardian grant helper `sales.permissions.grant_customer(user, customer)` assigns `view`/`change` on the customer.
  `sales.seed.seed` puts `world["customers"]` in (≈25, mixed kinds, at least 3 owned by `sam` with grants).

- [ ] **Step 1: Tests:**
  - `test_wholesale_group_is_conditional`: the create form renders a conditional group containing `company`,
    `vat_id`, `price_tier`, `payment_terms`; POST with `kind=consumer` and those fields filled saves them empty;
    POST `kind=wholesale` without `company` → form error on `company`.
  - `test_detail_property_grid`: wholesale customer detail contains `Price tier` and the tabs/links for Orders,
    Addresses, Subscriptions (the latter two may be empty lists).
  - `test_sam_sees_only_granted_customers`: list as `sam` contains exactly the granted customers; detail of another
    customer → 403 or 404; nested address list of another customer → 403 or 404. *(Review Focus 1)*
  - `test_customer_with_orders_is_protected`: deleting a customer that has an order shows the protection alert and
    keeps the customer (write this test in Task 6, where orders exist; leave a skipped placeholder only if
    unavoidable).
  - `test_mark_default_address`: POST the `make_default` action on an address → it is default, the previous default
    isn't.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement:** `ConditionalGroupModelForm` with `ConditionalGroup(toggle=ModelFieldToggle(<kind is wholesale>)…)`
  — check upstream `crud_views/lib/conditional` for how a choice field (not a boolean) drives a toggle; if only
  booleans are supported, add a boolean `is_wholesale` model field derived from `kind` or make `kind` the boolean,
  and log a finding. Guardian views `Guardian{List,Detail,Create,Update,Delete}ViewPermissionRequired`; create
  grants the creator (pattern from upstream `guardian_demo`). Detail via `ObjectDetailMixin`, layout `split-card`,
  avatar initials + kind badge in the page header (mockup tab 2). Address views nested (`CreateViewParentMixin`),
  `make_default` as `ActionViewPermissionRequired` (`cv_key="make_default"`, `cv_permission="change"`,
  `cv_backend_only=True`). Delete with `cv_modal = True`, `cv_show_related_objects = True`. List with
  `cv_list_actions_inline = ["detail"]` (rest in ⋯ menu), filters (kind, country, owner), avatar column.
- [ ] **Step 4: Run** → PASS; browser check; findings.
- [ ] **Step 5:** Commit `Sales: customers with guardian and nested addresses`.

### Task 6: `sales` — orders (nested + top-level, workflow, line formset)

**Files:**
- Create: `example/sales/views/orders.py`, `example/sales/lookups.py`, `templates/sales/order_detail.html`
  (only if the context-button template needs it), `templates/sales/packing_slip.html`, `tests/test_orders.py`
- Modify: `sales/models.py`, `sales/forms.py`, `sales/urls.py`, `sales/seed.py`, migrations

**Interfaces:**
- Consumes: `Customer`, `Address`, `Customer.discount`, `catalog.Product.is_beans`.
- Produces: `Order(WorkflowModelMixin)`: `customer` FK **PROTECT**, `number` (int, unique, from 1001), `state`
  `FSMField` with `OrderState` = `draft, confirmed, roasted, shipped, delivered, cancelled`, `ship_to` FK Address
  (nullable), `requested_roast_date` (date, nullable), `notes, created_at, shipped_at` (nullable);
  `Order.subtotal`, `Order.discount_amount`, `Order.total` (Decimal properties computed from lines and
  `customer.discount`); `Order.is_editable` (`state in {draft, confirmed}`). Transitions: `wf_confirm`
  (draft→confirmed, refused with message if no lines), `wf_roast` (confirmed→roasted), `wf_ship`
  (roasted→shipped, sets `shipped_at`), `wf_deliver` (shipped→delivered), `wf_cancel` (draft/confirmed→cancelled,
  comment required). `STATE_BADGES` per state. `OrderLine`: `order` FK CASCADE, `product` FK PROTECT,
  `quantity` (positive int), `grind` (`whole`/`filter`/`espresso`, blank), `bag_size` (`250g`/`1kg`, blank),
  `unit_price` (copied from product on save), `line_total` property. ViewSets: `cv_order = ViewSet(model=Order,
  name="order", parent=ParentViewSet(name="customer"), icon_header="tabler:receipt")` and
  `cv_all_orders = ViewSet(model=Order, name="orders", icon_header="tabler:receipt")` (list + create only). Typeahead
  lookup `sales.customers` (name/company/city contains, restricted to customers the user can view).

- [ ] **Step 1: Tests:**
  - `test_line_formset_creates_lines_and_totals`: create a nested order with two bean lines and one equipment line →
    3 lines; `order.total == subtotal - discount` for a tier-B customer (assert exact Decimal for the seeded
    prices you choose in the test).
  - `test_non_beans_line_clears_grind_and_bag`: equipment line posted with `grind=espresso`, `bag_size=1kg` → saved
    blank. *(Review Focus 3)*
  - `test_confirm_without_lines_is_refused`: draft order with no lines, POST the confirm transition → state still
    `draft`, an error message is shown. *(Review Focus 3)*
  - `test_workflow_happy_path`: confirm → roast → ship → deliver; history (`WorkflowInfo`) has 4 entries.
  - `test_shipped_order_edit_is_disabled_and_forbidden`: list shows the update action disabled
    (`data-cv-disabled`) for a shipped order; GET and POST of its update and delete URLs → 403. *(Review Focus 2)*
  - `test_top_level_list_and_create`: `orders-list` lists orders of all customers for `alex`; for `sam` only the
    granted customers' orders *(Review Focus 1)*; POST `orders-create` with a customer → redirect to the nested order
    update page of that customer.
  - `test_customer_with_orders_is_protected` (from Task 5).
  - `test_packing_slip_context_button`: order detail contains a link to the packing slip; the slip page lists the
    lines.
  - `test_duplicate_order`: the custom form view `duplicate` on a delivered order creates a new draft with the same
    lines and redirects to it.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement:** models + `django_fsm.transition` with `custom={"label": …}`; workflow view
  (`WorkflowViewPermissionRequired`, `WorkflowForm`); line items via `crud_views.lib.formsets`
  (`InlineFormSet`, `FormSet`, `FormSets`, `FormSetMixin`) on nested create/update; the grind/bag rule as a
  `ConditionalFormSet`/conditional group if upstream supports a per-row toggle driven by the selected product,
  otherwise in `OrderLineForm.clean()` plus a small progressive-enhancement script that disables the two selects —
  log a finding either way about per-row conditional fields. Disabled actions via
  `cv_action_enabled(cls, user, obj=None)` returning `obj is None or obj.is_editable` on update/delete, and
  `cv_inaccessible_actions = "disable"`. Typeahead customer field on the top-level create form
  (`TypeaheadField(lookup="sales.customers", widget=TypeaheadSelect())`, `.bind(request)` in `__init__`);
  datetimepicker `DatePickerInput` on `requested_roast_date`. If the typeahead markup looks wrong under Tabler,
  add an optional Tabler template in `crud_views_tabler` selected via `CRUD_VIEWS_TYPEAHEAD["TEMPLATE"]` /
  `["SELECT_TEMPLATE"]` (no import of the extensions package) and log a finding. Packing slip: a `DetailViewPermissionRequired`
  subclass with `cv_key="packing_slip"`, `cv_path="packing-slip"` and its own print-friendly template, reached
  through a `ContextButton(key="packing_slip", key_target="packing_slip")` on the order ViewSet. Duplicate: `CustomFormViewPermissionRequired`
  (`cv_key="duplicate"`). Order detail page: workflow steps bar (Tabler `steps steps-counter`) — if this needs a
  template, put it in the example's `sales/templates`, not the theme. List badges via `STATE_BADGES`; check how
  `crud_views_workflow/badge.html` renders under Tabler (`text-bg-*` vs `bg-*-lt`) and log a finding.
- [ ] **Step 4: Run** → PASS; browser check incl. JS console; findings.
- [ ] **Step 5:** Commit `Sales: orders with workflow, line formset, typeahead`.

### Task 7: `sales` — subscriptions

**Files:**
- Modify: `sales/models.py`, `sales/views/subscriptions.py` (create), `sales/urls.py`, `sales/seed.py`,
  `sales/tests/test_subscriptions.py` (create), migrations

**Interfaces:**
- Consumes: `Order`, `OrderLine`, `catalog.Subscription`.
- Produces: `CustomerSubscription`: `customer` FK CASCADE, `product` FK `catalog.Subscription` PROTECT,
  `started_on`, `next_delivery` (date), `is_active`. `CustomerSubscription.advance()` moves `next_delivery` by the
  product's interval (7/14/30 days). `sales.services.run_subscriptions(due: date, user) -> list[Order]`.
  ViewSets: nested `cv_subscription` (parent `customer`), top-level `cv_all_subscriptions` (list only, plus the
  no-object custom form view `run` → “Run subscriptions”).

- [ ] **Step 1: Tests:**
  - `test_run_creates_draft_orders_for_due`: two active subscriptions due ≤ date, one future, one paused → 2 draft
    orders, each with one line (the subscription product, `quantity = bags_per_delivery`); due ones advanced.
  - `test_run_twice_creates_nothing_new`: second run for the same date → `[]`. *(Review Focus 4)*
  - `test_run_view_flashes_count`: POST the run view → success message “Created 2 draft orders”.
  - `test_sam_sees_only_own_subscriptions` on the top-level list. *(Review Focus 1)*
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement** (`CustomFormNoObjectViewPermissionRequired`, a date field with
  `DatePickerInput`, `messages.success`). **Step 4: Run** → PASS; browser check.
- [ ] **Step 5:** Commit `Sales: customer subscriptions and run subscriptions`.

### Task 8: `roastery` — green lots, cupping, roast batches

**Files:**
- Create: `example/roastery/` (`models.py`, `forms.py`, `views.py`, `urls.py`, `seed.py`, `tests.py`, `admin.py`,
  migrations)
- Modify: `catalog` migration for `Beans.green_lot` if deferred in Task 4

**Interfaces:**
- Produces: `GreenLot`: `code` (unique, e.g. `CO-24-017`), `origin` FK `catalog.Origin`, `producer, variety,
  process, harvest_year, kg_purchased, kg_on_hand, price_per_kg, arrived_on`; `GreenLot.average_score`.
  `CuppingSession`: `lot` FK CASCADE, `held_on`, `notes`; `CuppingSession.average`. `CuppingScore`: `session` FK
  CASCADE, `taster` FK user, `aroma, flavor, acidity, body, aftertaste, balance, overall` (Decimal 0–10, step 0.25),
  `total` property = sum of the seven attributes + 30 (SCA-style, max 100), documented in the model docstring. `RoastBatch`: `lot` FK PROTECT, `roasted_on`,
  `profile, green_kg, roasted_kg, roaster` FK user, `orders` M2M `sales.Order` (blank); `weight_loss_pct`.
  ViewSets: `cv_lot` (name `lot`), `cv_session` (name `cupping`, parent `lot`), `cv_batch` (name `batch`).

- [ ] **Step 1: Tests:**
  - `test_cupping_scores_formset`: nested create of a session with two score rows → 2 scores, `session.average`
    equals the expected value (all-8.00 row → total 86.00); unique taster per session enforced (duplicate taster → formset error).
  - `test_score_out_of_range_rejected`: 10.5 → field error.
  - `test_lot_delete_previews_sessions`: lot delete page lists its cupping sessions as related objects; lot with a
    roast batch → protection alert.
  - `test_breadcrumb_two_levels`: session detail breadcrumb contains `Green lots`, the lot code, the session date.
  - `test_kim_can_edit_roastery_sam_cannot`: `kim` 200 on lot update, `sam` 403.
  - `test_batch_weight_loss`: 12.0 → 10.2 kg = 15.0 %.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement** (lot detail with `ObjectDetailMixin`, layout `accordion` or
  `card-rows` — a different pack from Tasks 4/5; sessions as child list on the lot detail; scores formset rendered
  as a compact table-like row layout as in mockup tab 5; `DatePickerInput` on dates; batch create with typeahead or
  plain select for orders). **Step 4: Run** → PASS; browser check; findings.
- [ ] **Step 5:** Commit `Roastery: green lots, cupping sessions with score formsets, roast batches`.

### Task 9: `shipping` — courier tracking as a Resource

**Files:**
- Create: `example/shipping/` (`apps.py`, `resources.py`, `courier.py`, `views.py`, `urls.py`, `tests.py`)

**Interfaces:**
- Consumes: shipped/delivered `sales.Order`s.
- Produces: `shipping.courier.fetch_shipments() -> list[dict]`: deterministic fake API payload derived from
  shipped/delivered orders (tracking number `ACME` + order number zero-padded to 8 digits, carrier from a fixed
  list by order number, status `in_transit`/`delivered`, ETA, 3–5 events). `Shipment(Resource)` with
  `pk_field = "tracking_number"`, `cv_get_items` from `fetch_shipments()`. ViewSet `cv_shipment` (name `shipment`,
  `resource_permissions={"view": "sales.view_order"}`). Order detail links to its shipment detail when shipped.

- [ ] **Step 1: Tests:** `test_list_shows_one_row_per_shipped_order`; `test_detail_lists_events`;
  `test_unknown_tracking_number_404`.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement** (`ResourceViewMixin`, `ListViewTableMixin`, detail with event
  timeline using Tabler `list-group`/timeline markup in an example template). **Step 4: Run** → PASS.
- [ ] **Step 5:** Commit `Shipping: courier tracking from a fake API`.

### Task 10: Seed the world

**Files:**
- Modify: `dashboard/management/commands/seed_demo.py`, every `<app>/seed.py`, `Taskfile.yaml`, `README.md`

**Interfaces:**
- Consumes: all `seed(rng, world)` functions.
- Produces: `manage.py seed_demo [--reset] [--seed 42]`. Without `--reset` on a database where `alex` exists:
  prints “Demo data already present; use --reset to rebuild.” and exits 0 without changes. `--reset` deletes rows of
  all demo models (not `admin`, not other users) and rebuilds. Taskfile: `seed` runs `seed_demo` (no `status:`
  needed); `seed:showcase` stays as is.

- [ ] **Step 1: Tests** (`dashboard/tests.py`): `test_seed_refuses_on_populated_db` *(Review Focus 5)*;
  `test_seed_reset_is_deterministic` (two `--reset` runs → identical counts per model and identical first customer
  name) *(Review Focus 5)*; `test_seed_world_shape`: ≥ 20 customers, ≥ 60 orders in every state, ≥ 25 products of
  all three types, ≥ 6 lots with sessions and scores, ≥ 3 customers granted to `sam`, orders spread over the last
  90 days, ≥ 10 active subscriptions.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement**: real origins (Colombia/Huila, Ethiopia/Yirgacheffe,
  Brazil/Cerrado, Kenya/Nyeri, Guatemala/Huehuetenango, …), plausible café names, invented people; orders created
  through the model transitions so workflow history exists. **Step 4: Run** → PASS; `task reset` then `task up`;
  click every sidebar entry as alex, sam, kim.
- [ ] **Step 5:** Commit `Seed a coherent roastery world`.

### Task 11: Dashboard

**Files:**
- Modify: `example/dashboard/views.py`, `templates/dashboard/index.html`, `dashboard/tests.py`

**Interfaces:**
- Consumes: sales/catalog/roastery models.
- Produces: context keys `revenue_30d`, `revenue_trend_pct`, `open_orders`, `orders_to_roast` (qs, confirmed,
  ≤ 7 days), `active_subscriptions`, `next_subscription_run`, `green_stock_kg`, `recent_cuppings`,
  `revenue_by_week` (list of `(iso_week_label, Decimal)` for the last 12 weeks).

- [ ] **Step 1: Tests:** `test_stats_match_data` (known small fixture → exact values for the four stat cards);
  `test_revenue_by_week_has_12_points`; `test_sam_dashboard_counts_only_granted_customers` (revenue/open orders
  for sam are restricted) *(Review Focus 1)*.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement** the layout of mockup tab 1; ApexCharts from jsDelivr with a
  pinned version and SRI (as `django_tabler/base.html` does for Tabler), data via `json_script`, colours from
  Tabler CSS vars so dark mode works. **Step 4: Run** → PASS; browser check light + dark.
- [ ] **Step 5:** Commit `Dashboard: roastery stats and revenue chart`.

### Task 12: Show code panel and “How this is themed”

**Files:**
- Create: `example/config/showcode.py` (collector), `example/config/templatetags/showcode.py` (or a small `project`
  app if a templatetags module needs an app — your call), `example/templates/project/code_panel.html`,
  `example/templates/project/theming.html`, view + URL `theming`, tests in `dashboard/tests.py` or the new app
- Modify: `example/templates/project/crud_views.html` (fill `code_panel`), nav menu

**Interfaces:**
- Produces: `collect_app_sources(view) -> list[Source]` where `Source = (label: str, path: str, html: str,
  lines: int)`: the view's app `models.py`, `forms.py`, `views.py` / `views/*.py`, `seed.py` excluded,
  `templates/**/*.html`; highlighted with Pygments `HtmlFormatter(noclasses=True)` (dark-mode readable style, your
  choice). `collect_theme_sources() -> list[Source]`: every file under `src/crud_views_tabler/` (templates, static,
  `apps.py`, `buttons.py`, `icons.py`, `checks.py`…) except tests and `__pycache__`, plus the relevant lines of
  `example/config/settings.py` (INSTALLED_APPS block, `CRUD_VIEWS_EXTENDS`, `CRISPY_TEMPLATE_PACK`,
  `DJANGO_TABLES2_TEMPLATE`). Totals computed at render time.

- [ ] **Step 1: Tests:** `test_code_panel_on_crud_pages` (customer list page contains the panel and the string
  `cv_customer = GuardianViewSet`); `test_code_panel_never_shows_theme_imports` (for every app source collected
  from `sales`, `catalog`, `roastery`, `shipping`: no `django_tabler`/`crud_views_tabler` substring — enforces the
  anti-goal); `test_theming_page_counts` (page shows a file count equal to `len(collect_theme_sources())` and the
  summed line count); `test_panel_is_collapsed_by_default`.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement**: panel = Tabler card under the content, collapsed, with
  nav-pills per file (mockup tab 5); the page header gets a “Show code” toggle if a block allows it, otherwise the
  toggle sits on the panel card. Theming page: headline “The whole theme is N files, M lines. Your app code is
  unchanged.”, a file list with line counts, then the sources; links to upstream's theme guide
  (`docs/reference/theme.md` on Read the Docs) and to `docs/crud_views_tabler.md` on GitHub. If upstream offers no
  block to hang the panel on, log a finding (spec: upstream's `snippet_panels` is example-only).
- [ ] **Step 4: Run** → PASS; browser check. **Step 5:** Commit `Show code panel and How this is themed page`.

### Task 13: Sweep, findings, docs

**Files:**
- Modify: `docs/crud_views_upstream_findings_roastery.md`, `docs/crud_views_tabler.md` (new overrides/CSS, if any),
  `docs/crud_views_upstream_status.md` (link to the findings doc), `README.md`, `CLAUDE.md` (apps, commands, test
  layout, seed), `docs/crispy_tabler_coverage.md` (verify)

- [ ] **Step 1:** `task reset && task up`; in a real browser, as `alex`, `sam`, `kim`, visit every sidebar entry and
  every action reachable from them, light and dark mode, desktop and 390 px width. Record any JS console error,
  visual breakage or Bootstrap-only markup; fix per the fix order; each fix that is CSS/override/workaround → a
  finding. Confirm every must-have feature (nested, formsets, workflow, polymorphic, object detail, guardian,
  resources) is reachable within three clicks of the dashboard.
- [ ] **Step 2:** List features from the spec's feature map that were dropped or reduced, with the reason, at the end
  of the findings doc under “Not shown in the demo”.
- [ ] **Step 3: Run** all three test commands from Global Constraints → pass.
- [ ] **Step 4:** Update the docs listed above. Commit `Roastery demo: sweep, findings and docs`.
