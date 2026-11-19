# Object Header Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** On every page with a ViewSet Navigation bar, the Tabler page header shows the owner (avatar, name as h1, underline tabs) above the view's own title row, which reads as a section heading.

**Architecture:** One new empty block in the Tabler layout (`page_header_top`, above the title row). The theme's page template fills it when `cv_navbar` is truthy: breadcrumb, owner row from `cv_navbar.icon`/`cv_navbar.label`, and `{% cv_navbar_items %}` in a `.cv-tabler-navbar` wrapper. The title row (`page_heading`, `subtitle`, `actions`) stays where it is, so project overrides of `page_title`, `cv_context` and `actions` keep working. CSS scoped to the bar makes upstream's pills look like Tabler tabs and sizes the view title as a section heading.

**Tech Stack:** Django 6.1 templates, Tabler 1.6.1 CSS (CDN), django-crud-views (sibling checkout, PR #383 head `271928a6`), pytest (theme), Django test runner (example), Playwright for the browser check.

**Spec:** `docs/superpowers/specs/2026-11-19-object-header-layout-design.md`

## Global Constraints

- Work on branch `adopt/object-navbar-381` (unmerged; this builds on it), in place: the uv path deps are relative to this checkout.
- `../django-crud-views` and `../django-crud-views-extensions` are read-only.
- No copied or overridden upstream navbar template; read `cv_navbar.label`, `cv_navbar.icon` from context and place `{% cv_navbar_items %}`.
- App code under `example/` never imports `django_tabler` or `crud_views_tabler`; no change to `example/` views or templates.
- Every theme CSS rule and every upstream awkwardness gets an entry in `docs/crud_views_upstream_findings_roastery.md` in the same commit.
- Docs cite upstream as "PR #383 (open)"; never "merged". New text says "ViewSet Navigation"; existing finding headings stay (anchors).
- Pages without a bar render the same header as today.
- Test commands: theme `uv run --group test pytest tests/crud_views_tabler --ds tests.crud_views_tabler.settings`; example `uv run python example/manage.py test sales`; everything `task test`. Redirect long output to a file and read its tail.

## Review Focus

1. A project override of `page_title` (order detail appends `{{ object.state_badge }}`): the badge must stay in the view title, never in the owner h1. Pinned in Task 2.
2. A project override of `actions` with `{{ block.super }}` (demo's Show code): the button must sit in the view row below the tabs, not in the owner row. Pinned in Task 2.
3. A modal request (`X-CV-Modal: true`) to a view with the mixin: no owner row, no tabs, today's markup. Pinned in Task 2 (existing test kept).
4. An owner label with markup (`<b>A & B</b>`): escaped in the h1, the landmark label and `<title>`. Pinned in Task 2.
5. Breadcrumb appears exactly once on bar pages (block `breadcrumb` suppressed with a bar, rendered in `page_header_top`). Pinned in Task 1.

---

### Task 1: Theme renders the owner header

**Files:**
- Modify: `src/django_tabler/templates/django_tabler/layouts/app.html` (inside `.page-header > .container-xl`, before `.row`)
- Modify: `src/crud_views_tabler/templates/crud_views_tabler/page.html`
- Modify: `src/crud_views_tabler/static/crud_views_tabler/crud_views_tabler.css` (replace the two rules at lines 95–103)
- Modify: `tests/crud_views_tabler/test_theme.py` (navbar tests near lines 196–223, CSS test near 769)
- Modify: `docs/crud_views_upstream_findings_roastery.md` (finding 36 rewrite, new finding 38, summary rows), `docs/crud_views_tabler.md` (mapping table row and paragraph, lines ~46–61), `CLAUDE.md` (template chain paragraph)

**Interfaces:**
- Produces: layout block `page_header_top`; on bar pages the markup order inside `.page-header` is breadcrumb → `<span class="avatar ...">` + `<h1 class="page-title ...">label</h1>` → `<div class="cv-tabler-navbar ... d-print-none">` (upstream `<nav aria-label="Sections for …">`) → title row (`h2.page-title`, subtitle, `.btn-list` actions). Block `cv_navbar` wraps only the tabs wrapper. `<title>` is `"<cv_header> · <label> · <site name>"` on bar pages.

- [ ] **Step 1: Replace the navbar theme tests with these (test app customer is "Customer 03")**

```python
def test_bar_page_builds_the_owner_header(self):
    html = self.client.get(reverse("customer-detail", kwargs={"pk": self.customer.pk})).content.decode()
    header = html[html.index('class="page-header') : html.index('class="page-body')]
    order = [header.index('class="breadcrumb'), header.index("<h1"), header.index('class="cv-tabler-navbar'),
             header.index("<h2"), header.index('cv-key="update"')]
    self.assertEqual(order, sorted(order))
    self.assertRegex(header, r'<h1 class="page-title[^"]*">\s*Customer 03\s*</h1>')
    self.assertEqual(header.count('class="breadcrumb'), 1)
    self.assertNotIn('class="cv-navbar ', html)          # the full wrapper tag is not used
    self.assertIn('aria-label="Sections for Customer 03"', header)
    self.assertRegex(header, r'class="nav-link[^"]* active" href="[^"]+" aria-current="true"')

def test_bar_page_title_names_the_owner(self):
    html = self.client.get(reverse("customer-detail", kwargs={"pk": self.customer.pk})).content.decode()
    self.assertRegex(html, r"<title>[^<]*· Customer 03 · ")

def test_owner_icon_is_a_tabler_svg(self):
    html = self.client.get(reverse("customer-detail", kwargs={"pk": self.customer.pk})).content.decode()
    owner = html[html.index('class="avatar') : html.index("</h1>")]
    tabs = html[html.index('class="cv-tabler-navbar') : html.index("</nav>")]
    self.assertIn("<svg", owner); self.assertIn("<svg", tabs); self.assertNotIn("fa-", owner + tabs)

def test_emptying_the_navbar_block_drops_only_the_tabs(self):
    response = self.client.get(reverse("customer-detail", kwargs={"pk": self.customer.pk}))
    source = '{% extends "crud_views_tabler/page.html" %}{% block cv_navbar %}{% endblock %}'
    html = engines["django"].from_string(source).render(response.context_data, response.wsgi_request)
    self.assertNotIn("cv-tabler-navbar", html); self.assertNotIn("<nav aria-label=\"Sections", html)
    self.assertIn("<h1", html)

def test_page_without_navbar_keeps_todays_header(self):
    html = self.client.get(reverse("customer-list")).content.decode()
    self.assertNotIn("cv-tabler-navbar", html); self.assertNotIn("<h1", html)
    header = html[html.index('class="page-header') : html.index('class="page-body')]
    self.assertLess(header.index('class="breadcrumb'), header.index("<h2"))
```

CSS test (replaces `test_object_navbar_pills_fit_tabler`), named `test_object_navbar_pills_look_like_tabs`: asserts with `assertRegex` that the CSS contains the icon gap rule `.cv-tabler-navbar .nav-link { gap: .375rem; }` and at least one rule whose selector starts with `.cv-tabler-navbar .nav-pills` and sets a `border-bottom` (the tab underline), and that the old `--tblr-nav-pills-link-active-color` rule is gone.

- [ ] **Step 2: Run the theme tests.** Expected: 5 failed (the four bar tests and the CSS test: no `<h1`, no `page_header_top`, old CSS); `test_page_without_navbar_keeps_todays_header` passes already, as a regression guard; the rest pass.

- [ ] **Step 3: Add the block and fill it**

`app.html`: `{% block page_header_top %}{% endblock %}` as the first child of `.page-header > .container-xl`, with a one-line comment. `page.html`:
- `title`: `{% cv_header %}{% if cv_navbar %} · {{ cv_navbar.label }}{% endif %}`.
- Replace the `page_header_before` override with `page_header_top`: `{% if cv_navbar %}` breadcrumb, owner row (`avatar` with `{% cv_icon cv_navbar.icon %}` when set, `<h1 class="page-title">{{ cv_navbar.label }}</h1>`), `{% block cv_navbar %}<div class="cv-tabler-navbar d-print-none">{% cv_navbar_items %}</div>{% endblock %}` `{% endif %}`.
- `breadcrumb`: `{% if not cv_navbar %}{% cv_breadcrumb %}{% endif %}`.
- Leave `page_heading`, `subtitle`, `actions` unchanged. Update the template comment.

CSS (replacing lines 95–103, comment cites finding 36): keep the gap rule; style `.cv-tabler-navbar .nav-pills` / `.nav-link` like Tabler 1.6.1 `nav-tabs` (bottom border on the list, transparent background, active link with the bottom border in the link colour, readable in dark mode); size the view title after the tabs as a section heading with a sibling selector (`.cv-tabler-navbar ~ .row .page-title`). Exact values are set in Task 3's browser check; here the rules only need to exist and render.

- [ ] **Step 4: Run the theme tests.** Expected: all pass (90 + net new).

- [ ] **Step 5: Docs in the same commit**
- Finding 36: "What we do" describes the new rules (pills restyled as tabs, gap kept, view title sized); summary row 100 follows.
- New finding 38 "The ViewSet Navigation contract forbids the identity as page heading": quote theme.md ("The identity must not become another page heading or replace the existing view header/actions"); what we do (owner h1 from `cv_navbar.label`/`.icon`, `cv_navbar_items` placed, view header kept as the row below the tabs; `NavBar(template=...)` wrappers are not used by this layout because component tags ignore them); suggested upstream change (allow a theme-level owner header, or an `identity` placement that is a heading); severity cosmetic. Add the summary row.
- `docs/crud_views_tabler.md`: mapping row for the bar (block `page_header_top`, owner h1, `cv_navbar_items`, block `cv_navbar` = tabs only); paragraph replaced accordingly (breadcrumb moves to the top on bar pages; emptying `cv_navbar` drops only the tabs).
- `CLAUDE.md`: template chain lists `page_header_top` (empty, top of the page header) next to `page_header_before`, and `cv_navbar_items` instead of `cv_navbar`.

- [ ] **Step 6: Commit**

```bash
git add src/django_tabler/templates/django_tabler/layouts/app.html src/crud_views_tabler tests/crud_views_tabler docs/crud_views_upstream_findings_roastery.md docs/crud_views_tabler.md CLAUDE.md docs/superpowers/specs/2026-11-19-object-header-layout-design.md docs/superpowers/plans/2026-11-19-object-header-layout.md
git commit -m "Theme: owner header for ViewSet Navigation (avatar, name, tabs above the view's title row; findings 36, 38)"
```

### Task 2: Demo tests follow the owner header

**Files:**
- Modify: `example/sales/tests/test_navbar.py`
- Modify: `docs/crud_views_upstream_findings_roastery.md` (finding 23 "Child sections adopted here" bullet, summary row 87, "Not shown in the demo" tabs bullet)

**Interfaces:**
- Consumes: Task 1's markup order and `<title>` format.

- [ ] **Step 1: Adapt and add tests**
- `navbar()` helper unchanged (it parses the `<nav aria-label="Sections for …">` landmark).
- `test_name_with_markup_is_escaped`: slice `html[html.index("<h1") : html.index("</nav>")]`, expect `&lt;b&gt;A &amp; B&lt;/b&gt;` twice (h1, landmark); `<title>` contains it escaped; `"<b>A"` nowhere.
- `test_bar_is_hidden_in_print`: on the packing slip, the tabs wrapper and owner row are inside `class="page-header d-print-none`, and the wrapper itself has `d-print-none`.
- New `test_detail_buttons_sit_below_the_tabs`: on customer detail, `cv-key="update"` and `cv-key="delete"` come after `</nav>` and before `class="page-body`; none between `<h1` and `</nav>`.
- New `test_show_code_sits_below_the_tabs`: on a nested order list, the `href="#code-panel"` button and `cv-key="create"` come after `</nav>`.
- New `test_state_badge_stays_in_the_view_title`: on order detail, the h1 segment (`<h1` … `</h1>`) has no `badge`; the `<h2` … `</h2>` segment has one.
- Keep `test_modal_delete_has_no_bar` and add `self.assertNotIn("<h1", ...)`.
- `test_pages_without_a_customer_have_no_bar`: also `assertNotContains(response, "<h1")`.

- [ ] **Step 2: Run** `uv run python example/manage.py test sales.tests.test_navbar`. Expected: all pass (Task 1 already changed the markup; if a new test passes before its assertion was meaningful, check it fails against `git stash` of Task 1's `page.html`, record the result).

- [ ] **Step 3: Findings 23 and "Not shown in the demo"**: say the sections render as tabs under the customer's name at the top of the page header (Task 1's layout, PR #383 open), instead of "above the page header"; summary row 87 cites PR #383 (open).

- [ ] **Step 4: Run** `task test > $WS/task-test.log 2>&1; tail -20 $WS/task-test.log`. Expected: exit 0, check clean.

- [ ] **Step 5: Commit** `git add example/sales/tests/test_navbar.py docs/crud_views_upstream_findings_roastery.md && git commit -m "Demo: navbar tests follow the owner header; finding 23 cites PR #383"`

### Task 3: Browser check and CSS polish

**Files:**
- Modify (only if the check finds defects): `src/crud_views_tabler/static/crud_views_tabler/crud_views_tabler.css`, finding 36, the CSS test.

- [ ] **Step 1: Run the demo on a free port (not 8765; e.g. 8791)** with the existing database, log in as alex, and screenshot with Playwright (`PLAYWRIGHT_NODEJS_PATH=<path to node>`): customer detail, nested order list, order detail, nested order update; sidebar and top-bar layouts; light and dark; 1280 px and 375 px; print emulation of the packing slip. Compare with mockup option D/1 (`.superpowers/brainstorm/*/content/navbar-buttons.html`).
- [ ] **Step 2: Check:** tabs underline and active tab readable in light and dark (active text contrast ≥ 4.5:1 against the page); icon/label gap; tabs wrap at 375 px without horizontal scroll; owner row and view row aligned with the breadcrumb; view title visibly smaller than the owner name; no tabs or owner row in print.
- [ ] **Step 3: Fix defects in CSS only**, each with its rule text pinned in the CSS test (RED first) and described in finding 36.
- [ ] **Step 4: Run** `task test` (as in Task 2). Expected: exit 0.
- [ ] **Step 5: Commit** `git commit -am "Theme: owner header polish after browser check (finding 36)"` (skip if no change; ledger says so). Stop the demo server by its PID, never with `pkill -f`.
