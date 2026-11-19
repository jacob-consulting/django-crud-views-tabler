# crud_views_tabler on django-crud-views main: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the Tabler theme app `crud_views_tabler` onto django-crud-views main's icon registry and JavaScript adapters, delete the Font Awesome mapping, jQuery and the Bootstrap shim it no longer needs, and update the two documents that describe the theme.

**Architecture:** The theme stays a template-override app listed before `crud_views` in `INSTALLED_APPS`. Icons: `AppConfig.ready()` registers a `tabler` icon library (inline-SVG renderer in `crud_views_tabler/icons.py`) and a Tabler value for every semantic icon name upstream defines; templates render icons with upstream's `{% cv_icon %}`. JavaScript: one registered asset points `cv.adapters` at `window.tabler`; the theme follows upstream's modal shell, modal dismiss and filter toggle contracts and marks its buttons `data-cv-tooltip`.

**Tech Stack:** Python 3.14, Django 6.1, uv, django-crud-views main (installed as an editable path dependency from `../django-crud-views`), Tabler 1.6.1 (CDN), crispy-bootstrap5. Tests: Django `TestCase` via `uv run python manage.py test`.

**Spec:** `docs/superpowers/specs/2026-10-20-crud-views-tabler-upstream-main-design.md`

## Global Constraints

- Python 3.14, Django 6.1, uv. Tests run with `uv run python manage.py test`. `uv run python manage.py check --fail-level WARNING` must pass (an existing test asserts it).
- Tabler 1.6.1 from the CDN; `tabler.min.js` is loaded `defer` at the end of `templates/base.html`. Do not change the script order in `templates/base.html`.
- No inline scripts (strict-CSP friendly).
- These ids and hooks stay unchanged: `cv-modal`, `cv-modal-dialog`, `cv-modal-content`, `cv-filter-toggle`, `filter-collapse`, every `cv-key`, `cv-list-container`, `cv-context-container`, every `data-cv-*` attribute.
- The SVG markup is exactly: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false" class="icon {css}">` + one `<path d="…" />` per entry + `</svg>`; `class` is `"icon"` plus the extra classes, trimmed.
- Anti-goals (grep-verified in Task 8): no Font Awesome class string, no `jquery`, no `cvt_icon`, no `<i class="{{ … }}">` left under `crud_views_tabler/`.
- The `dashboard` app's `{% icon %}` tag keeps working through a plain `name -> SVG` function; it does not use the registry.
- Upstream checkout: `../django-crud-views`, branch `main` at commit 440ac55 (version 0.30.0 plus the unreleased #200). Upstream references used below live there: `src/crud_views/lib/icons.py`, `src/crud_views/lib/assets.py`, `src/crud_views/static/crud_views/js/adapters.js`, `src/crud_views/templates/crud_views/**`, `docs/reference/icons.md`, `docs/reference/javascript.md`, `tests/test1/test_filter.py`.

## Review Focus

1. A `css` argument containing quotes must be escaped in the SVG `class` attribute, never injected (Task 2, `test_css_is_escaped`).
2. A disabled action (`cv_inaccessible_actions = "disable"` on the target view, user without permission) must still render a Tabler SVG inside the disabled `<button data-cv-disabled="permission">` (Task 2, `test_disabled_action_renders_a_tabler_icon`).
3. The dashboard pages, which use the theme's SVG function through their own `{% icon %}` tag, must keep rendering SVG after the module API change (Task 2, `test_dashboard_icons_still_render`).
4. A pinned filter (`cv_filter_pinned = True`) renders the filter card with the Tabler filter icon and no toggle button (Task 6, `test_pinned_filter_has_no_toggle`).
5. A project override of a theme-mapped name with another library (`CRUD_VIEWS_ICONS = {"detail": "far:eye"}`) renders that library's markup and does not trigger `crud_views_tabler.W001` (Task 2, `test_project_setting_wins_over_the_theme`; Task 3, `test_other_library_values_are_not_reported`).

---

## File structure

| File | Responsibility |
|---|---|
| `pyproject.toml`, `uv.lock` | editable path dependency on the upstream checkout |
| `crud_views_tabler/icons.py` | Tabler SVG paths (`ICONS`), the plain SVG function `svg()`, the registry renderer `render()`, the semantic table `TABLER_ICONS` |
| `crud_views_tabler/checks.py` | system check `crud_views_tabler.W001` (new) |
| `crud_views_tabler/apps.py` | `ready()`: icon library + icon table + asset registration, imports the checks |
| `crud_views_tabler/static/crud_views_tabler/tabler-adapters.js` | the one-statement adapter asset (new) |
| `crud_views_tabler/templates/crud_views/**` | overrides; see the per-task edit tables |
| `crud_views_tabler/tests.py` | all theme tests (one file, as today) |
| `dashboard/templatetags/tabler.py` | imports the renamed SVG function |
| `customers/views.py` | `icon_header="tabler:building-store"` |
| `docs/crud_views_tabler.md`, `docs/crud_views_upstream_questions.md`, `README.md` | documentation |

Deleted: `crud_views_tabler/templatetags/` (whole package), `crud_views_tabler/templates/crud_views/tags/icon.html`, `crud_views_tabler/templates/crud_views/shared/js.html`, `crud_views_tabler/static/crud_views_tabler/bootstrap-shim.js`.

The test suite is red between Task 1 and the end of Task 2 (the dependency switch breaks the filter template until the icon templates are migrated). Tasks 1 and 2 are therefore executed back to back.

---

### Task 1: Editable path dependency on the upstream checkout

**Files:**
- Modify: `pyproject.toml`
- Regenerate: `uv.lock`

**Interfaces:**
- Produces: `crud_views` importable from `../django-crud-views/src/crud_views`, version `0.30.0`, with `static/crud_views/js/adapters.js` and `lib/icons.py` present. Every later task relies on this.

- [ ] **Step 1: Point the dependency at the sibling checkout**

In `pyproject.toml` replace the `dependencies` entry `"django-crud-views>=0.29.4"` with `"django-crud-views>=0.30.0"` and add, after the `[project]` table:

```toml
[tool.uv.sources]
django-crud-views = { path = "../django-crud-views", editable = true }
```

- [ ] **Step 2: Lock and sync**

Run: `cd <repo> && uv lock && uv sync`
Expected: `uv.lock` changes (the `django-crud-views` entry gets `source = { editable = "../django-crud-views" }` and `version = "0.30.0"`); `uv sync` reports the editable package installed and `django-crud-views==0.29.4` removed.

- [ ] **Step 3: Verify what is installed**

Run:

```bash
uv run python -c "import crud_views, pathlib; p = pathlib.Path(crud_views.__file__).resolve(); print(crud_views.__version__, p); assert 'django-crud-views/src' in str(p); assert (p.parent / 'static/crud_views/js/adapters.js').exists(); assert (p.parent / 'lib/icons.py').exists()"
```

Expected: prints `0.30.0 ../django-crud-views/src/crud_views/__init__.py`, no assertion error.

- [ ] **Step 4: System checks still pass**

Run: `uv run python manage.py check --fail-level WARNING`
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 5: Record the baseline**

Run: `uv run python manage.py test crud_views_tabler 2>&1 | tail -5`
Expected: `FAILED (errors=9)`; every error is `TemplateSyntaxError: Invalid block tag … 'cv_filter_icon'` from `crud_views/tags/list_filter.inner.html`. This is the expected red state that Task 2 fixes. Any other failure is unexpected: stop and investigate.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "Install django-crud-views from the sibling checkout (editable path, main @ 440ac55)"
```

---

### Task 2: Icon registry integration

**Files:**
- Modify: `crud_views_tabler/icons.py`
- Modify: `crud_views_tabler/apps.py`
- Modify: `dashboard/templatetags/tabler.py:3,12`
- Modify: `customers/views.py:26`
- Modify: 12 templates under `crud_views_tabler/templates/crud_views/` (table in Step 7)
- Delete: `crud_views_tabler/templatetags/crud_views_tabler.py`, `crud_views_tabler/templatetags/__init__.py`, `crud_views_tabler/templates/crud_views/tags/icon.html`
- Test: `crud_views_tabler/tests.py`

**Interfaces:**
- Consumes (upstream `crud_views.lib.icons`): `register_icon_library(prefix: str, renderer: str | Callable = "font", **config) -> None`, `register_icons(icons: dict[str, str]) -> None`, `render_icon(value: str | None, css: str = "") -> SafeString`, `DEFAULT_ICONS: dict[str, str]` (27 keys), template tag `{% cv_icon value css="" %}` in the `crud_views` library. Renderer contract: `renderer(name: str, *, css: str, config: dict) -> SafeString`.
- Produces (`crud_views_tabler.icons`): `ICONS: dict[str, list[str]]` (Tabler name -> `<path d>` strings); `svg(name: str | None, css: str = "") -> SafeString` (inline SVG, `""` for unknown or empty name); `render(name: str, *, css: str, config: dict) -> SafeString` (the registry renderer, delegates to `svg`, ignores `config`); `TABLER_ICONS: dict[str, str]` (every `DEFAULT_ICONS` key -> `"tabler:<name>"`). Task 3 reads `ICONS`; Task 4 extends the `register_assets` call in `apps.py`.

- [ ] **Step 1: Replace `IconTests` and extend the rendering tests**

In `crud_views_tabler/tests.py` replace the whole `IconTests` class, the import line `from crud_views_tabler.icons import render_icon`, and add the new rendering tests. New imports at the top:

```python
import re
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from crud_views.lib.icons import DEFAULT_ICONS
from crud_views.lib.icons import render_icon as cv_render_icon
from crud_views_tabler.icons import ICONS, TABLER_ICONS, render, svg
from customers.models import Customer
from customers.views import CustomerDeleteView
```

The new icon test class:

```python
class TablerIconTests(SimpleTestCase):
    def test_svg_for_a_tabler_name(self):
        html = svg("eye", "icon-sm")
        self.assertIn('class="icon icon-sm"', html)
        self.assertIn("<path", html)
        self.assertIn('aria-hidden="true"', html)

    def test_svg_without_extra_classes_has_no_trailing_space(self):
        self.assertIn('class="icon"', svg("eye"))

    def test_unknown_or_empty_name_renders_nothing(self):
        self.assertEqual(svg("not-an-icon"), "")
        self.assertEqual(svg(None), "")
        self.assertEqual(render("not-an-icon", css="", config={}), "")

    def test_css_is_escaped(self):
        self.assertIn('class="icon a&quot; onload=&quot;x"', svg("eye", 'a" onload="x'))

    def test_renderer_matches_svg(self):
        self.assertEqual(render("trash", css="icon-sm", config={"renderer": "x"}), svg("trash", "icon-sm"))

    def test_every_upstream_icon_name_is_mapped(self):
        self.assertEqual(set(TABLER_ICONS), set(DEFAULT_ICONS))
        for name, value in TABLER_ICONS.items():
            prefix, tabler_name = value.split(":", 1)
            self.assertEqual(prefix, "tabler", name)
            self.assertIn(tabler_name, ICONS, f"{name} -> {value} has no path in ICONS")

    def test_registry_renders_tabler_svg(self):
        self.assertEqual(cv_render_icon("detail"), svg("eye"))
        self.assertEqual(cv_render_icon("tabler:building-store", css="icon-sm"), svg("building-store", "icon-sm"))

    @override_settings(CRUD_VIEWS_ICONS={"detail": "far:eye"})
    def test_project_setting_wins_over_the_theme(self):
        self.assertEqual(cv_render_icon("detail"), '<i class="fa-regular fa-eye" aria-hidden="true"></i>')
```

In `ThemeRenderingTests` change `test_list_uses_tabler_table_and_icons` to end with:

```python
        self.assertNotIn("fa-regular", html)
        self.assertNotIn("fa-solid", html)
        self.assertNotIn("<i class=", html)  # every icon on the page is a Tabler SVG
        self.assertIn(svg("building-store"), html)  # the ViewSet header icon, tabler:building-store
```

and add to `ThemeRenderingTests`:

```python
    def test_disabled_action_renders_a_tabler_icon(self):
        viewer = get_user_model().objects.create_user("viewer", password="viewer-pass")
        viewer.user_permissions.add(Permission.objects.get(codename="view_customer", content_type__app_label="customers"))
        self.client.force_login(viewer)
        with mock.patch.object(CustomerDeleteView, "cv_inaccessible_actions", "disable"):
            html = self.client.get(reverse("customer-list")).content.decode()
        button = re.search(r'<button[^>]*data-cv-disabled="permission"[^>]*>.*?</button>', html, re.S)
        self.assertIsNotNone(button)
        self.assertIn("<svg", button.group(0))
        self.assertNotIn("<i class=", button.group(0))

    def test_dashboard_icons_still_render(self):
        html = self.client.get("/").content.decode()
        self.assertIn("<svg", html)
        self.assertNotIn("<i class=", html)
```

In `CardThemeTests` add to `test_cards_render_in_tabler_grid`: `self.assertNotIn("<i class=", html)`, and add to `test_order_bar`:

```python
        self.assertRegex(html, r'<button[^>]*value="asc"[^>]*>\s*<svg')
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run python manage.py test crud_views_tabler 2>&1 | tail -3`
Expected: `ImportError: cannot import name 'TABLER_ICONS' from 'crud_views_tabler.icons'` (the suite does not even start).

- [ ] **Step 3: Rewrite `crud_views_tabler/icons.py`**

Keep every existing `ICONS` entry. Delete `FONT_AWESOME`, `FONT_AWESOME_EXACT`, `resolve()` and `render_icon()`. Add these twelve `ICONS` entries (Tabler outline set 3.41.0, background path already dropped):

```python
    "caret-down": ["M6 10l6 6l6 -6h-12"],
    "caret-up": ["M18 14l-6 -6l-6 6h12"],
    "chevrons-down": ["M7 7l5 5l5 -5", "M7 13l5 5l5 -5"],
    "chevrons-right": ["M7 7l5 5l-5 5", "M13 7l5 5l-5 5"],
    "chevrons-up": ["M7 11l5 -5l5 5", "M7 17l5 -5l5 5"],
    "circle-check": ["M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0", "M9 12l2 2l4 -4"],
    "circle-x": ["M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0", "M10 10l4 4m0 -4l-4 4"],
    "file-text": [
        "M14 3v4a1 1 0 0 0 1 1h4",
        "M17 21h-10a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2h7l5 5v11a2 2 0 0 1 -2 2",
        "M9 9l1 0",
        "M9 13l6 0",
        "M9 17l6 0",
    ],
    "filter-x": [
        "M13.758 19.414l-4.758 1.586v-8.5l-4.48 -4.928a2 2 0 0 1 -.52 -1.345v-2.227h16v2.172a2 2 0 0 1 -.586 1.414l-4.414 4.414v1.5",
        "M22 22l-5 -5",
        "M17 22l5 -5",
    ],
    "hierarchy": [
        "M10 5a2 2 0 1 0 4 0a2 2 0 1 0 -4 0",
        "M3 19a2 2 0 1 0 4 0a2 2 0 1 0 -4 0",
        "M17 19a2 2 0 1 0 4 0a2 2 0 1 0 -4 0",
        "M6.5 17.5l5.5 -4.5l5.5 4.5",
        "M12 7l0 6",
    ],
    "language": [
        "M9 6.371c0 4.418 -2.239 6.629 -5 6.629",
        "M4 6.371h7",
        "M5 9c0 2.144 2.252 3.908 6 4",
        "M12 20l4 -9l4 9",
        "M19.1 18h-6.2",
        "M6.694 3l.793 .582",
    ],
    "square-x": [
        "M3 5a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14",
        "M9 9l6 6m0 -6l-6 6",
    ],
```

Add the semantic table, exactly these 27 entries:

```python
# django-crud-views semantic icon name -> Tabler icon (registered from apps.py; CRUD_VIEWS_ICONS overrides per key).
TABLER_ICONS: dict[str, str] = {
    "list": "tabler:list",
    "card": "tabler:layout-grid",
    "detail": "tabler:eye",
    "create": "tabler:square-plus",
    "update": "tabler:pencil",
    "delete": "tabler:trash",
    "order-up": "tabler:arrow-up",
    "order-down": "tabler:arrow-down",
    "manage": "tabler:settings",
    "workflow": "tabler:hierarchy",
    "actions-menu": "tabler:dots",
    "filter": "tabler:filter",
    "filter-close": "tabler:filter-x",
    "language": "tabler:language",
    "sort-asc": "tabler:sort-ascending",
    "sort-desc": "tabler:sort-descending",
    "table-sort-asc": "tabler:chevrons-up",
    "table-sort-desc": "tabler:chevrons-down",
    "formset-up": "tabler:caret-up",
    "formset-down": "tabler:caret-down",
    "formset-add": "tabler:plus",
    "formset-delete": "tabler:square-x",
    "field-marker": "tabler:chevrons-right",
    "boolean-true": "tabler:circle-check",
    "boolean-false": "tabler:circle-x",
    "property-detail": "tabler:info-circle",
    "text-icon": "tabler:file-text",
}
```

Add the two functions with these signatures; `svg` keeps today's `format_html` / `format_html_join` markup (Global Constraints) and returns `SafeString("")` for a falsy name or a name not in `ICONS`; `render(name, *, css, config)` returns `svg(name, css)`:

```python
def svg(name: str | None, css: str = "") -> SafeString: ...
def render(name: str, *, css: str, config: dict) -> SafeString: ...
```

Update the module docstring: Tabler outline icons as inline SVG, plugged into django-crud-views' icon registry as the `tabler` library; `TABLER_ICONS` maps the package's semantic names; a project overrides per key with `CRUD_VIEWS_ICONS`.

- [ ] **Step 4: Register the library and the table in `crud_views_tabler/apps.py`**

`ready()` becomes:

```python
    def ready(self):
        from crud_views.lib.assets import register_assets
        from crud_views.lib.icons import register_icon_library, register_icons

        from crud_views_tabler.icons import TABLER_ICONS

        register_icon_library("tabler", renderer="crud_views_tabler.icons.render")
        register_icons(TABLER_ICONS)
        register_assets("crud_views_tabler", css=["crud_views_tabler/crud_views_tabler.css"])
```

Extend the class docstring with one sentence: registers the `tabler` icon library and a Tabler icon for every semantic name, so projects need no icon settings.

- [ ] **Step 5: Update the dashboard tag**

In `dashboard/templatetags/tabler.py` change the import to `from crud_views_tabler.icons import svg` and the tag body to `return svg(name, css_class)`.

- [ ] **Step 6: Point the demo ViewSet at the Tabler library**

`customers/views.py:26`: `icon_header="building-store"` becomes `icon_header="tabler:building-store"`.

- [ ] **Step 7: Switch the templates from `cvt_icon` to `cv_icon`**

Apply exactly these edits under `crud_views_tabler/templates/crud_views/`:

| File | `{% load %}` line becomes | Icon tag edits |
|---|---|---|
| `tags/context_action.html` | `{% load crud_views %}` | 3× `{% cvt_icon cv_icon_action %}` → `{% cv_icon cv_icon_action %}` |
| `tags/list_action.html` | delete the `{% load crud_views_tabler %}` line (no tag used) | none |
| `tags/list_action.inner.html` | `{% load crud_views %}` | 3× `{% cvt_icon cv_icon_action %}` → `{% cv_icon cv_icon_action %}` |
| `tags/card_action.html` | `{% load crud_views %}` | 2× `{% cvt_icon cv_icon_action %}` → `{% cv_icon cv_icon_action %}`; 2× `{% cvt_icon cv_icon_action "icon-sm" %}` → `{% cv_icon cv_icon_action css="icon-sm" %}` |
| `tags/actions_menu_toggle.html` | `{% load i18n crud_views %}` | `{% cvt_icon cv_menu_icon %}` → `{% cv_icon cv_menu_icon %}` |
| `tags/actions_menu_item_label.html` | `{% load crud_views %}` | `{% cvt_icon cv_icon_action "dropdown-item-icon" %}` → `{% cv_icon cv_icon_action css="dropdown-item-icon" %}` |
| `tags/context_action_filter.html` | `{% load crud_views %}` | `{% cvt_icon cv_icon_action %}` → `{% cv_icon "filter" %}` (Task 6 rewrites this file) |
| `tags/list_filter.inner.html` | unchanged (`crispy_forms_tags crud_views`) | `{% cv_filter_icon %}` → `{% cv_icon "filter" %}` |
| `snippets/card_order.html` | `{% load i18n crud_views %}` | `{% cvt_icon "sort-ascending" %}` → `{% cv_icon "sort-asc" %}`; `{% cvt_icon "sort-descending" %}` → `{% cv_icon "sort-desc" %}` |
| `snippets/pagination.html` | `{% load crud_views i18n %}` | `{% cvt_icon "chevron-left" "icon-sm" %}` → `{% cv_icon "tabler:chevron-left" css="icon-sm" %}`; same for `chevron-right` |
| `table/bootstrap5.html` | `{% load django_tables2 crud_views i18n %}` | same two chevron edits as `pagination.html` |
| `view_card.content.html` | `{% load crud_views i18n %}` | `{% cvt_icon "mood-empty" %}` → `{% cv_icon "tabler:mood-empty" %}` |
| `view_delete.content.html` | `{% load crud_views i18n %}` | `{% cvt_icon "alert-circle" "alert-icon" %}` → `{% cv_icon "tabler:alert-circle" css="alert-icon" %}` |

- [ ] **Step 8: Delete the dead files**

```bash
git rm -r crud_views_tabler/templatetags crud_views_tabler/templates/crud_views/tags/icon.html
```

- [ ] **Step 9: Verify nothing references the removed library**

Run: `grep -rn "{% load[^%]*crud_views_tabler" crud_views_tabler/templates; grep -rn "cvt_icon\|cv_filter_icon" crud_views_tabler dashboard customers templates --include=*.html --include=*.py; grep -rn "render_icon" dashboard`
Expected: no output from any of the three greps (`shared/js.html` still references `crud_views_tabler/bootstrap-shim.js` at this point; Task 4 removes it).

- [ ] **Step 10: Run the full suite**

Run: `uv run python manage.py test`
Expected: `OK`, every test passes (the dashboard tests included).

- [ ] **Step 11: Commit**

```bash
git add -A crud_views_tabler dashboard/templatetags/tabler.py customers/views.py
git commit -m "Theme: register a tabler icon library with django-crud-views' icon registry; drop the Font Awesome mapping"
```

---

### Task 3: System check `crud_views_tabler.W001`

**Files:**
- Create: `crud_views_tabler/checks.py`
- Modify: `crud_views_tabler/apps.py` (import the checks in `ready()`)
- Test: `crud_views_tabler/tests.py`

**Interfaces:**
- Consumes: `crud_views.lib.icons.get_icons() -> dict[str, str]` (resolved table, cached, reset on `setting_changed`); `crud_views_tabler.icons.ICONS`.
- Produces: `check_tabler_icons(app_configs=None, **kwargs) -> list[CheckMessage]`, registered with `django.core.checks.register(Tags.templates)`; warning id `crud_views_tabler.W001`.

- [ ] **Step 1: Write the failing tests**

Add to `crud_views_tabler/tests.py` (import `from django.core.checks import run_checks`):

```python
class IconCheckTests(SimpleTestCase):
    @override_settings(CRUD_VIEWS_ICONS={"detail": "tabler:does-not-exist"})
    def test_unknown_tabler_icon_is_reported(self):
        messages = [m for m in run_checks() if m.id == "crud_views_tabler.W001"]
        self.assertEqual(len(messages), 1)
        self.assertIn("'detail'", messages[0].msg)
        self.assertIn("'tabler:does-not-exist'", messages[0].msg)

    @override_settings(CRUD_VIEWS_ICONS={"detail": "far:eye", "person": "tabler:user"})
    def test_other_library_values_are_not_reported(self):
        self.assertEqual([m.id for m in run_checks() if m.id.startswith("crud_views_tabler.")], [])
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run python manage.py test crud_views_tabler.tests.IconCheckTests -v 2`
Expected: `test_unknown_tabler_icon_is_reported` fails with `0 != 1`; the other passes.

- [ ] **Step 3: Implement `crud_views_tabler/checks.py`**

```python
from django.core.checks import CheckMessage, Tags, Warning, register
```

`check_tabler_icons(app_configs=None, **kwargs) -> list[CheckMessage]`, decorated `@register(Tags.templates)`: for every `(key, value)` in `get_icons().items()` where `value` is a `str` starting with `"tabler:"` and the part after the colon is not in `ICONS`, append `Warning(f"Icon {key!r} = {value!r}: crud_views_tabler has no SVG for Tabler icon {name!r}.", hint="Add its <path d> values to crud_views_tabler.icons.ICONS or use another library prefix.", id="crud_views_tabler.W001")`.

- [ ] **Step 4: Import the checks from `ready()`**

In `apps.py` `ready()` add, next to the other imports: `import crud_views_tabler.checks  # noqa: F401`.

- [ ] **Step 5: Run the tests**

Run: `uv run python manage.py test crud_views_tabler`
Expected: `OK` (including the existing `test_system_checks_pass`, which proves the default table triggers no W001).

- [ ] **Step 6: Commit**

```bash
git add crud_views_tabler/checks.py crud_views_tabler/apps.py crud_views_tabler/tests.py
git commit -m "Theme: warn (crud_views_tabler.W001) when a tabler: icon has no SVG path"
```

---

### Task 4: JavaScript: no jQuery, no shim, one adapter asset

**Files:**
- Create: `crud_views_tabler/static/crud_views_tabler/tabler-adapters.js`
- Delete: `crud_views_tabler/templates/crud_views/shared/js.html`, `crud_views_tabler/static/crud_views_tabler/bootstrap-shim.js`
- Modify: `crud_views_tabler/apps.py` (`register_assets` gains `js=`)
- Test: `crud_views_tabler/tests.py`

**Interfaces:**
- Consumes: upstream `register_assets(key, js=(), css=(), emit=True)`; bundles render after the core scripts, in `INSTALLED_APPS` order. Upstream `adapters.js` defines `cv.adapters` and `cv.bootstrapAdapters(ns)`, `ns` an object or a function resolved per call.
- Produces: `cv.adapters` bound to `window.tabler` on every crud_views page.

- [ ] **Step 1: Replace the script test**

In `ThemeRenderingTests` replace `test_scripts_load_jquery_and_shim_deferred` with:

```python
    def test_scripts_use_the_tabler_adapter_without_jquery(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        self.assertNotIn("jquery", html.lower())
        self.assertNotIn("bootstrap-shim", html)
        core = html.index("crud_views/js/adapters.js")
        theme = html.index("crud_views_tabler/tabler-adapters.js")
        self.assertLess(core, theme)
        self.assertIn("crud_views/js/modal.js", html)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run python manage.py test crud_views_tabler.tests.ThemeRenderingTests.test_scripts_use_the_tabler_adapter_without_jquery`
Expected: FAIL, `'jquery' unexpectedly found in …`.

- [ ] **Step 3: Delete the override and the shim**

```bash
git rm crud_views_tabler/templates/crud_views/shared/js.html crud_views_tabler/static/crud_views_tabler/bootstrap-shim.js
```

- [ ] **Step 4: Create `crud_views_tabler/static/crud_views_tabler/tabler-adapters.js`**

```javascript
// Tabler's bundle exposes Bootstrap's components on window.tabler, not window.bootstrap.
// crud_views calls Bootstrap only through cv.adapters (adapters.js); point them at Tabler.
// The namespace is resolved on every adapter call, so tabler.min.js may load deferred.
Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler));
```

- [ ] **Step 5: Register the asset**

In `apps.py` the `register_assets` call becomes `register_assets("crud_views_tabler", js=["crud_views_tabler/tabler-adapters.js"], css=["crud_views_tabler/crud_views_tabler.css"])`.

- [ ] **Step 6: Run the suite**

Run: `uv run python manage.py test crud_views_tabler`
Expected: `OK`.

- [ ] **Step 7: Commit**

```bash
git add -A crud_views_tabler
git commit -m "Theme: drop jQuery and the bootstrap shim; bind cv.adapters to window.tabler"
```

---

### Task 5: Modal contract and Tabler shell

**Files:**
- Modify: `crud_views_tabler/templates/crud_views/modal/content.html:4`
- Create: `crud_views_tabler/templates/crud_views/modal/shell.html`
- Test: `crud_views_tabler/tests.py`

**Interfaces:**
- Consumes: upstream `{% cv_config %}` includes `crud_views/modal/shell.html`; `modal.js` finds the shell through the ids `cv-modal`, `cv-modal-dialog`, `cv-modal-content` and calls `cv.adapters.modal.hide` for a click on `[data-cv-modal-dismiss]` inside the shell; the Bootstrap adapter's `setSize` swaps only `modal-sm/lg/xl` and keeps other classes on the dialog.

- [ ] **Step 1: Write the failing tests**

Extend `test_delete_modal_partial_has_no_card_and_a_danger_button` with:

```python
        self.assertIn("data-cv-modal-dismiss", html)
        self.assertNotIn("data-bs-dismiss", html)
```

Add to `ThemeRenderingTests`:

```python
    def test_modal_shell_is_tabler(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        self.assertIn('class="modal modal-blur fade" id="cv-modal"', html)
        self.assertIn('class="modal-dialog modal-dialog-centered" id="cv-modal-dialog"', html)
        self.assertIn('id="cv-modal-content"', html)
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run python manage.py test crud_views_tabler.tests.ThemeRenderingTests -v 2 2>&1 | grep -E "FAIL|ok$" | head`
Expected: the two tests FAIL (`data-cv-modal-dismiss` not found; `modal-blur` not found).

- [ ] **Step 3: Switch the close button**

`modal/content.html` line 4: `data-bs-dismiss="modal"` becomes `data-cv-modal-dismiss`. Nothing else changes.

- [ ] **Step 4: Create `modal/shell.html`**

```html
{# Tabler theme: blurred backdrop, centered dialog. The three ids are crud_views' contract (modal.js, cv.adapters.modal). #}
<div class="modal modal-blur fade" id="cv-modal" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog modal-dialog-centered" id="cv-modal-dialog">
    <div class="modal-content" id="cv-modal-content"></div>
  </div>
</div>
```

- [ ] **Step 5: Run the suite**

Run: `uv run python manage.py test crud_views_tabler`
Expected: `OK`.

- [ ] **Step 6: Commit**

```bash
git add crud_views_tabler/templates/crud_views/modal crud_views_tabler/tests.py
git commit -m "Theme: Tabler modal shell; close through data-cv-modal-dismiss"
```

---

### Task 6: Filter toggle contract and `data-cv-tooltip`

**Files:**
- Rewrite: `crud_views_tabler/templates/crud_views/tags/context_action_filter.html`
- Modify: `crud_views_tabler/templates/crud_views/tags/context_action.html`, `tags/list_action.inner.html`, `tags/card_action.html`
- Test: `crud_views_tabler/tests.py`

**Interfaces:**
- Consumes: `list.filter.js` reads `aria-expanded` on `#cv-filter-toggle`, toggles `#filter-collapse` through `cv.adapters.collapse`, flips `d-none` on every `[data-cv-filter-icon]` inside the button and POSTs `{"filter_expanded": <bool>}` as JSON to the list URL; the view stores it in the session and exposes `cv_filter_expanded` to the template. `tooltip.js` initialises `[data-cv-tooltip]` through `cv.adapters.tooltip` at load, on `cv:modal:loaded` and on `cv:formset:row-added`.

- [ ] **Step 1: Write the failing tests**

Add to `ThemeRenderingTests` (import `from customers.views import CustomerListView`):

```python
    def test_filter_toggle_contract(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        button = re.search(r'<button[^>]*id="cv-filter-toggle"[^>]*>.*?</button>', html, re.S).group(0)
        self.assertIn('aria-controls="filter-collapse"', button)
        self.assertIn('aria-expanded="false"', button)
        self.assertIn("data-cv-tooltip", button)
        self.assertIn('<span data-cv-filter-icon="open">', button)
        self.assertIn('<span data-cv-filter-icon="close" class="d-none">', button)
        self.assertEqual(button.count("<svg"), 2)

    def test_filter_toggle_reflects_the_session_state(self):
        response = self.client.post(
            reverse("customer-list"), data='{"filter_expanded": true}', content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        html = self.client.get(reverse("customer-list")).content.decode()
        button = re.search(r'<button[^>]*id="cv-filter-toggle"[^>]*>.*?</button>', html, re.S).group(0)
        self.assertIn('aria-expanded="true"', button)
        self.assertIn('<span data-cv-filter-icon="open" class="d-none">', button)
        self.assertIn('<span data-cv-filter-icon="close">', button)
        self.assertIn('class="collapse show" id="filter-collapse"', html)

    def test_pinned_filter_has_no_toggle(self):
        with mock.patch.object(CustomerListView, "cv_filter_pinned", True):
            html = self.client.get(reverse("customer-list")).content.decode()
        self.assertIn('id="filter-pinned"', html)
        self.assertNotIn('id="cv-filter-toggle"', html)
        self.assertIn("<svg", html[html.index('id="filter-pinned"'):][:800])  # the card header's filter icon

    def test_action_tooltips_are_initialised_by_crud_views(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        buttons = re.findall(r"<(?:a|button)\b[^>]*\bcv-key=[^>]*>", html)
        self.assertGreater(len(buttons), 3)
        for tag in buttons:
            self.assertNotIn('data-bs-toggle="tooltip"', tag)
        self.assertTrue(any("data-cv-tooltip" in tag for tag in buttons))
```

Add to `CardThemeTests`:

```python
    def test_icon_only_card_action_has_a_crud_views_tooltip(self):
        html = self.get()
        delete = re.search(r'<a\b[^>]*/delete/\?cv_from=card[^>]*>', html).group(0)  # the no_label card action
        self.assertIn("btn-icon", delete)
        self.assertIn("data-cv-tooltip", delete)
        self.assertNotIn('data-bs-toggle="tooltip"', delete)
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run python manage.py test crud_views_tabler 2>&1 | tail -3`
Expected: `FAILED (failures=4)` or `(failures=4, errors=1)`: the four new assertions on tooltips and the contract fail; `test_pinned_filter_has_no_toggle` may already pass.

- [ ] **Step 3: Rewrite `tags/context_action_filter.html`**

```html
{% load crud_views %}
{# Tabler theme: icon button; aria-expanded, aria-controls and the two icon spans are list.filter.js' contract. #}
<button type="button" class="btn btn-icon" id="cv-filter-toggle"
        aria-expanded="{% if cv_filter_expanded %}true{% else %}false{% endif %}" aria-controls="filter-collapse"
        title="{{ cv_action_label }}" data-cv-tooltip data-bs-placement="bottom" cv-key="{{ cv_key }}">
  <span data-cv-filter-icon="open"{% if cv_filter_expanded %} class="d-none"{% endif %}>{% cv_icon "filter" %}</span>
  <span data-cv-filter-icon="close"{% if not cv_filter_expanded %} class="d-none"{% endif %}>{% cv_icon "filter-close" %}</span>
  <span class="visually-hidden">{{ cv_action_label }}</span>
</button>
```

- [ ] **Step 4: Switch the action buttons to `data-cv-tooltip`**

Replace every `data-bs-toggle="tooltip"` with `data-cv-tooltip` in `tags/context_action.html` (2 occurrences), `tags/list_action.inner.html` (2) and `tags/card_action.html` (1). `title` and `data-bs-placement` attributes stay as they are.

Run: `grep -rn 'data-bs-toggle="tooltip"' crud_views_tabler/templates`
Expected: no output.

- [ ] **Step 5: Run the suite**

Run: `uv run python manage.py test`
Expected: `OK`.

- [ ] **Step 6: Commit**

```bash
git add crud_views_tabler/templates crud_views_tabler/tests.py
git commit -m "Theme: filter toggle follows the list.filter.js contract; action tooltips via data-cv-tooltip"
```

---

### Task 7: Documentation

**Files:**
- Modify: `docs/crud_views_upstream_questions.md`
- Modify: `docs/crud_views_tabler.md`
- Modify: `README.md`

No automated tests; Step 5 verifies structure with grep.

- [ ] **Step 1: `docs/crud_views_upstream_questions.md`: checked-against note**

In the section "How this was checked, and what was not", change the second bullet's bold lead-in to **Not checked at the time of writing:** and add a bullet after it:

```markdown
- **Update 2026-10-20:** the "Status" block under each point was checked against the upstream checkout
  (`../django-crud-views`, branch `main` at 440ac55: 0.30.0 plus the unreleased #200) by diffing
  `v0.29.4..main` for `src/crud_views/templates` and `src/crud_views/static` and reading `docs/reference/icons.md`
  and `docs/reference/javascript.md`. The original analysis and its file/line references remain for 0.29.4.
```

- [ ] **Step 2: Status blocks, one per point**

Insert each block directly under the point's `## N. …` heading, before `### What the package does today`.

Point 1:

```markdown
### Status (upstream main @ 440ac55, 2026-10-20)

**What upstream did (0.30.0):** a semantic icon registry (`crud_views.lib.icons`, `docs/reference/icons.md`). The
package refers to icons by name (`detail`, `delete`, `filter`, …: 27 names); the table is layered (package defaults,
theme registrations from `AppConfig.ready()`, `CRUD_VIEWS_ICONS`); values are `prefix:name` with a renderer per
library (`far`, `fas`, `bi` built in; the `font` renderer or any callable); one tag, `{% cv_icon %}`, renders
everything; `cv_icon_action`, `cv_icon_header` and `cv_menu_icon` carry icon values, not classes; object detail uses
the same table. `tags/icon.html`, `{% cv_filter_icon %}`, `CRUD_VIEWS_FILTER_ICON`, `CRUD_VIEWS_ACTIONS_MENU_ICON` and
the object-detail icon settings are gone, guarded by the checks `crud_views.E350`–`E356`, `W352`, `W353` and
`viewset.W246`.

**How it maps to the options:** option C, with a library/renderer layer on top. The compatibility rule is the one C
predicted: a colon-less value that is not a known name is a raw CSS class.

**What the theme does now:** registers a `tabler` library (inline-SVG renderer) and a Tabler icon for every semantic
name from `ready()`. The Font Awesome table, `{% cvt_icon %}` and `tags/icon.html` are gone; formset, boolean,
object-detail and language-selector icons are Tabler without any template override. Resolved.
```

Point 2:

```markdown
### Status (upstream main @ 440ac55, 2026-10-20)

Not changed on main. A draft design in the upstream repository,
`superpowers/specs/2026-10-19-button-variants-and-leaves-design.md`, gives `CrispyDeleteForm` the missing
`get_delete_button()` / `get_delete_button_kwargs()` hooks and moves every button class into a layered table
(`CRUD_VIEWS_BUTTON_CLASSES`, `register_button_classes()` for themes): option A plus option B, without the
contradictory-classes problem because the package would ship its own `Submit` subclass reading the table. Not
implemented; the theme keeps `TablerDeleteForm`.
```

Point 3:

```markdown
### Status (upstream main @ 440ac55, 2026-10-20)

**What upstream did (#200, unreleased):** `viewset.js`, `modal.js`, `list.filter.js` and `tooltip.js` use the DOM API
and `fetch`; `formset.js` stays on jQuery, logs one `console.error` without it and retries once on `window` `load`.
Every call into Bootstrap goes through `cv.adapters` (`modal.show` / `hide` / `setSize`, `tooltip.init`,
`collapse.toggle`), defined in a new first core script, `adapters.js`, pre-filled for `globalThis.bootstrap`;
`cv.bootstrapAdapters(ns)` builds all three for any Bootstrap-compatible namespace, `ns` being an object or a function
resolved on every call. New contracts: `crud_views/modal/shell.html` (ids `cv-modal`, `cv-modal-dialog`,
`cv-modal-content`), `data-cv-modal-dismiss`, `cv_modal_size` tokens `""` / `sm` / `lg` / `xl` (`viewset.E250`), and
the filter toggle's `aria-expanded`, `aria-controls="filter-collapse"` and `data-cv-filter-icon` spans
(`docs/reference/javascript.md`).

**How it maps to the options:** B (the three small scripts, plus tooltip.js), with C deferred (formset.js). The
"configured global" idea became an adapter object with a lazily resolved namespace, which also removes the load-order
trap: Bootstrap may load anywhere, deferred included.

**What the theme does now:** no jQuery, no shim. One registered asset, `tabler-adapters.js`, holds one statement:
`Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler))`. `shared/js.html` is no longer
overridden. Resolved for every page without formsets; a project with formsets loads jQuery itself.
```

Point 4:

```markdown
### Status (upstream main @ 440ac55, 2026-10-20)

Not changed on main. The draft design named under point 2 adds `cv_action_variant` to every view (`CreateView` and
the polymorphic create-select view default to `primary`, `DeleteView` to `danger`, the rest to `secondary`), a
`ContextButton.variant` override, and `CardAction.variant = None` meaning "the target view's variant": options B and
C together. Not implemented; the theme still hard-codes `create` / `create_select` as the primary action.
```

Point 5 (the second paragraph goes after the first, still before `### What the package does today`):

```markdown
### Status (upstream main @ 440ac55, 2026-10-20)

Not changed on main. The draft design named under point 2 is option D: `cv_button_data()` normalises a button once in
Python, three leaves (`tags/button/action.html`, `menu_item.html`, `container.html`) only draw, and the current
template names become thin logic templates so whole-template overrides keep working. Its "Tabler check" section
counts what this theme would drop: the six logic-copying overrides become two leaf overrides plus a `ready()`
registration. Not implemented.

**Observed while following main (2026-10-20):** three of the theme's overrides had gone stale between 0.29.4 and
main. `tags/list_filter.inner.html` still called `{% cv_filter_icon %}`, removed in 0.30.0: a `TemplateSyntaxError`
on every list page with a filter (9 of the theme's 19 tests). `tags/icon.html` went silently dead: upstream deleted
the template and `{% cv_header_icon %}` renders through `render_icon()` now. `modal/content.html` kept
`data-bs-dismiss="modal"`, which still worked only because Tabler's data API handles it, not through the new
`cv.adapters.modal.hide`. One loud failure, two silent ones, found only by diffing upstream's templates against the
overrides: the failure mode this point describes.
```

- [ ] **Step 3: `docs/crud_views_tabler.md`**

Apply these edits:

1. Line 4 ("Built against …"): `Built against django-crud-views main @ 440ac55 (0.30.0 plus the unreleased JavaScript adapters, installed as an editable path dependency from the sibling checkout `../django-crud-views`), Tabler 1.6.1 and crispy-bootstrap5 2026.9.`
2. In "Card views", delete the paragraph starting `Font Awesome mapping note:`.
3. In "Filter", append: `The toggle button in the page header follows list.filter.js' contract (aria-expanded, aria-controls="filter-collapse", both icons rendered with one hidden), so the icon swaps between filter and filter-x and matches the session state after a reload.`
4. Replace the whole "Icons" section with:

```markdown
## Icons

django-crud-views 0.30.0 refers to icons by semantic name (`detail`, `delete`, `filter`, …), resolves names through a
layered table (package defaults, theme registrations, `CRUD_VIEWS_ICONS`) to `prefix:name` values, and renders every
icon through `{% cv_icon %}` with a renderer per library prefix. The theme plugs into that:

- `crud_views_tabler/icons.py` holds Tabler outline icons as SVG paths (`ICONS`), the registry renderer `render`
  (inline SVG with `class="icon …"` and `aria-hidden`), and `TABLER_ICONS`: a Tabler icon for every semantic name
  the package defines (27 names, from `detail` to the formset and object-detail icons),
- `CrudViewsTablerConfig.ready()` registers the library (`register_icon_library("tabler", renderer=…)`) and the table
  (`register_icons(TABLER_ICONS)`), so a project needs no icon settings; formset, boolean, object-detail and
  language-selector icons are Tabler too, without a template override,
- the theme's templates use `{% cv_icon "sort-asc" %}` for semantic names and `{% cv_icon "tabler:chevron-left" %}`
  for Tabler-only icons; a ViewSet or view uses `icon_header="tabler:building-store"`,
- a project overrides any name with `CRUD_VIEWS_ICONS = {"detail": "tabler:zoom"}` (or a value from another
  library); a `tabler:` value without a path in `ICONS` renders nothing and is reported by the system check
  `crud_views_tabler.W001`.

The `dashboard` app's `{% icon %}` tag renders the same SVGs through the plain `icons.svg()` function.
```

5. Replace the whole "JavaScript" section with:

```markdown
## JavaScript

Core scripts on django-crud-views main run without jQuery and call Bootstrap only through `cv.adapters` (`modal`,
`tooltip`, `collapse`). Tabler's bundle exposes Bootstrap's components on `window.tabler`, so the theme registers one
asset, `crud_views_tabler/tabler-adapters.js`, holding one statement:

    Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler));

The namespace is resolved on every call, so `tabler.min.js` stays `defer`red at the end of the body while the
crud_views scripts load synchronously from `{% cv_js %}`. The theme loads no jQuery; a project with formsets loads it
in its own base template (`formset.js` is the only core script that needs it).

The theme follows the modal and filter contracts of main: `modal/shell.html` is overridden with Tabler's `modal-blur`
and a centered dialog (the ids `cv-modal`, `cv-modal-dialog`, `cv-modal-content` are the contract),
`modal/content.html` closes through `data-cv-modal-dismiss`, `cv_modal_size` takes `""`, `"sm"`, `"lg"` or `"xl"`, and
the filter toggle carries `aria-expanded`, `aria-controls="filter-collapse"` and both filter icons. Theme buttons carry
`data-cv-tooltip`, so core's `tooltip.js` initialises their tooltips through the adapter, including inside modal
content, which Tabler's own page-load initialisation never sees.
```

6. Replace the "Overridden templates" code block with:

```
crud_views/
  columns/actions.html            row actions
  modal/content.html              modal header icon, data-cv-modal-dismiss
  modal/shell.html                Tabler modal shell (modal-blur, centered)
  snippets/card_order.html        card ordering bar
  snippets/pagination.html        card-view pagination
  table/bootstrap5.html           card table, sort headers, footer pagination
  tags/actions_menu_item_label.html, actions_menu_toggle.html
  tags/breadcrumb.html
  tags/card.html, card_action.html  cards (with blocks) and card buttons
  tags/context_action.html, context_action_filter.html, context_actions.html
  tags/list_action.html (+ list_action.inner.html)
  tags/list_filter.html, list_filter.inner.html
  view_card.content.html          card grid and empty state
  view_create.content.html, view_update.content.html, view_delete.content.html
static/crud_views_tabler/
  crud_views_tabler.css           required marker, row actions, filter card spacing
  tabler-adapters.js              cv.adapters -> window.tabler
```

7. In "Not covered yet", change `- Filter button state (active/open) and a Tabler-style cancel button.` to `- A Tabler-style cancel button.`
8. In "Questions for django-crud-views upstream", append a status to each item: 1 → ` **Resolved in 0.30.0 (icon registry).**`; 2 → ` **Draft design upstream, not implemented.**`; 3 → ` **Resolved on main (#200, jQuery-free core and cv.adapters).**`; 4 and 5 → ` **Draft design upstream, not implemented.**`
9. In "Approach", the sentence `So the theme is template overrides plus a little Python (icons, one form class) and two static files.` becomes `So the theme is template overrides plus a little Python (the icon library, a system check, one form class) and two static files (a stylesheet and the adapter script).`

- [ ] **Step 4: `README.md`**

1. The "Layout" bullet for `crud_views_tabler/` becomes: `` - `crud_views_tabler/`: prototype Tabler theme for django-crud-views (template overrides, Tabler icon library, JS adapter); ``
2. After the "Run it" code block and before "Open http://…", add:

```markdown
django-crud-views is installed from the sibling checkout `../django-crud-views` (branch `main`) as an editable path
dependency (`[tool.uv.sources]` in `pyproject.toml`), because the theme follows features that are not released yet.
Replace the source entry with a version pin once they are.
```

- [ ] **Step 5: Verify the structure**

Run: `grep -c "^### Status (upstream main @ 440ac55" docs/crud_views_upstream_questions.md; grep -n "tabler-adapters.js\|crud_views_tabler.W001\|modal/shell.html" docs/crud_views_tabler.md | wc -l; grep -n "editable path" README.md`
Expected: `5`; a count of at least `3`; one README line.

- [ ] **Step 6: Commit**

```bash
git add docs/crud_views_upstream_questions.md docs/crud_views_tabler.md README.md
git commit -m "Docs: record what upstream main resolved (icons, JS adapters) and how the theme uses it"
```

---

### Task 8: Final verification

**Files:** none changed unless a step finds a defect.

- [ ] **Step 1: Suite and checks**

Run: `uv run python manage.py check --fail-level WARNING && uv run python manage.py test`
Expected: no issues; `OK`.

- [ ] **Step 2: No leftovers**

Run:

```bash
grep -rn "cvt_icon\|bootstrap-shim\|FONT_AWESOME\|cv_filter_icon\|data-bs-dismiss\|fa-regular\|fa-solid\|crud_views_tabler/templatetags" crud_views_tabler templates customers dashboard README.md docs/crud_views_tabler.md
grep -rni "jquery" crud_views_tabler templates customers dashboard
```

Expected: the first grep prints nothing. The second prints at most prose lines (the design doc is not in its scope; `templates/base.html` loads no jQuery).

- [ ] **Step 3: Browser pass**

Start the server in the background: `uv run python manage.py runserver` (seed first if the database is empty: `uv run python manage.py migrate && uv run python manage.py seed_demo_customers`). Sign in as a superuser; if none exists in the local database, create one with `uv run python manage.py shell -c "from django.contrib.auth import get_user_model as g; U=g(); U.objects.filter(username='demo-admin').exists() or U.objects.create_superuser('demo-admin','demo@example.com','demo-admin-pass')"` and say so in the report.

Then, in Chrome (claude-in-chrome tools, new tab), at `http://127.0.0.1:8000/customer/`:

1. No console errors; the network log has no request to `code.jquery.com` and loads `crud_views_tabler/tabler-adapters.js` after `crud_views/js/adapters.js`.
2. Every icon in the header, toolbar, table rows and `⋯` menu is an SVG; hovering a row action shows a tooltip.
3. Click the filter toggle: the panel opens, the icon changes to `filter-x`, `aria-expanded` is `true`; reload: the panel is still open and the icon still `filter-x`; click again: closed, `filter` icon.
4. Sort a column and page; the sort survives paging.
5. `/customer/card/`: order-bar icons are SVG, pagination works.
6. In the table, click a row's delete: the modal opens with a blurred backdrop and a centered dialog; the close button dismisses it; open again, tick confirm, click Delete: redirect to the list with the "Deleted »…«" message.
7. Append `?theme=dark` to the list URL: icons follow the text colour.

Record what was seen for each item. Any failure is a defect: fix it in the owning task's files, add a test where a server-side assertion can catch it, re-run Step 1, and commit the fix.

- [ ] **Step 4: Final state**

Run: `git status --short && git log --oneline -8`
Expected: a clean tree (apart from the pre-existing untracked `.run/`) and the commits of Tasks 1–7 on `main`.
