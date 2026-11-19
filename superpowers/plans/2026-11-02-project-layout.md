# Project Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move reusable code to `src/` (`django_tabler`, `crud_views_tabler`, `crispy_tabler`) and the demo to `example/`, with no change to what the app renders.

**Architecture:** Moves first, proven by a rendered-HTML comparison against a snapshot taken before anything changes. Then `django_tabler` is carved out with Acme content behind template overrides, `crispy_tabler` is copied in, and the docs follow.

**Tech Stack:** Python 3.14, Django 6.1, uv, setuptools, Django test runner, pytest for the crispy suite.

**Spec:** `docs/superpowers/specs/2026-11-02-project-layout-design.md`

## Global Constraints

- Python `>=3.14` and Django 6.1 stay as they are; the project name stays `tabler-test`.
- Non-test code in `src/` never imports from `example/`; `django_tabler` never references `crud_views` or `crud_views_tabler`.
- `INSTALLED_APPS` order: `django_tabler`, then `crud_views_tabler`, then `crud_views`.
- `../crispy-tabler` is never modified. `../django-crud-views` stays an editable path dependency.
- `db.sqlite3` is moved, never recreated.
- Use `git mv` for tracked moves.
- Do not fix the 4 baseline failures. Do not rewrite documents under `docs/superpowers/` other than this plan.

Commands used throughout, all run from the repository root:

```bash
SNAP=/tmp/claude-1000/-home-alex-projects-alex-tabler-test/d3fb9c9b-e87a-4132-a01d-f54f66492a54/scratchpad/layout
```

- **Test command before Task 3:** `uv run python example/manage.py test crud_views_tabler dashboard catalog customers`
- **Test command from Task 3:** the same, with `django_tabler` added as a label.
- **Expected failures, always exactly these 4, for the same reasons:**
  - `catalog.tests.ProductFormCoverageTests.test_form_actions_and_group_labels`
  - `crud_views_tabler.tests.ThemeRenderingTests.test_delete_form_is_the_stock_crispy_delete_form`
  - `crud_views_tabler.tests.ThemeRenderingTests.test_related_objects_alerts_get_the_tabler_layout`
  - `crud_views_tabler.tests.TablerIconTests.test_every_upstream_icon_name_is_mapped`

## Review Focus

- A flash message containing HTML, such as a username with `<b>`, is escaped on non-crud pages; a safe string passes through. Pinned in Task 3.
- A message with a custom level or with `extra_tags` renders like `cv_messages` does: as info, with the tags on the alert. Pinned in Task 3.
- A non-editable install still ships templates and static files. A wheel with only `.py` files would pass every editable test and break for anyone installing it. Pinned in Task 5.
- The example's override wins over the package default whatever the app order, so the site still says "Acme Admin". Pinned in Task 3.
- After the copy, `crispy_tabler` imports from `src/`, not a stale install of the sibling. Pinned in Task 4.

---

### Task 1: Branch and baseline snapshot

**Files:**
- Create: `$SNAP/snapshot.py` (throwaway, outside the repository)
- Commit: the spec and this plan

**Interfaces:**
- Produces: `$SNAP/snapshot.py <project_dir> <out_dir>`, which writes one normalized `.html` per page; `$SNAP/db.sqlite3`, a frozen database copy; `$SNAP/before/`, the baseline. Tasks 2 to 5 run the script again and compare with `diff -r`.

- [ ] **Step 1: Create the branch and commit the documents**

```bash
git checkout -b layout/src-example
git add docs/superpowers/specs/2026-11-02-project-layout-design.md docs/superpowers/plans/2026-11-02-project-layout.md
git commit -m "Docs: design and plan for the src/ and example/ layout"
```

- [ ] **Step 2: Freeze a database copy**

```bash
mkdir -p "$SNAP" && cp db.sqlite3 "$SNAP/db.sqlite3"
```

- [ ] **Step 3: Write `$SNAP/snapshot.py`**

Requirements:
- Put `project_dir` first on `sys.path`, set `DJANGO_SETTINGS_MODULE=config.settings`, call `django.setup()`, then `django.test.utils.setup_test_environment()`.
- Point `connections["default"].settings_dict["NAME"]` at `$SNAP/db.sqlite3` before any query, so the real database is untouched.
- Disconnect `django.contrib.auth.models.update_last_login` from `user_logged_in`, so runs do not change the dashboard.
- Fetch `login` with an anonymous client. With `Client.force_login` as `admin`, fetch `dashboard:index`, `dashboard:users`, `customer-list`, `customer-create`, `customer-detail`, `customer-delete`, `product-list` and `product-create`, using the first row's pk where needed. Fail loudly on `NoReverseMatch` or any status other than 200.
- Also fetch `dashboard:index` as `messages.html`, with `client.session["_messages"]` set from `SessionStorage.serialize_messages` (`django.contrib.messages.storage.session`) to five `Message` objects: `DEBUG`, `INFO`, `SUCCESS`, `WARNING` and `ERROR`, the `SUCCESS` one with `extra_tags="probe"`.
- Normalize before writing: replace `csrfmiddlewaretoken` values with `X`, replace `>\s+<` with `>\n<`, and collapse other whitespace runs to one space.

- [ ] **Step 4: Capture and check the baseline**

Run: `uv run python "$SNAP/snapshot.py" . "$SNAP/before" && uv run python "$SNAP/snapshot.py" . "$SNAP/before2" && diff -r "$SNAP/before" "$SNAP/before2"`
Expected: 10 files and no diff. `messages.html` contains `alert-danger`, `alert-secondary` and `probe`. Relative times such as "2 days ago" can shift overnight, so if only those differ later, re-create the baseline from `a287d94` in a worktree.

---

### Task 2: Move the demo to `example/` and the theme to `src/`

**Files:**
- Move: `catalog/`, `customers/`, `dashboard/`, `config/`, `manage.py`, `templates/` to `example/`
- Move: `crud_views_tabler/` to `src/crud_views_tabler/`
- Move (untracked): `db.sqlite3` to `example/db.sqlite3`
- Modify: `pyproject.toml`

**Interfaces:**
- Consumes: the Task 1 snapshot script.
- Produces: the layout later tasks work in. `BASE_DIR` in `example/config/settings.py` needs no edit: it now resolves to `example/`.

- [ ] **Step 1: Move the files**

Use `git mv` for the tracked directories and plain `mv` for the database.

- [ ] **Step 2: Add the build to `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
"*" = ["templates/**/*.html", "static/**/*"]
```

- [ ] **Step 3: Sync**

Run: `uv sync`
Expected: `tabler-test` is installed editable, and `uv run python -c "import crud_views_tabler; print(crud_views_tabler.__file__)"` prints a path under `src/`.

- [ ] **Step 4: Run the tests**

Run the test command from before Task 3.
Expected: 84 tests with exactly the 4 expected failures. In the verbose output, the theme tests are still named `crud_views_tabler.tests...`.

- [ ] **Step 5: Compare the pages and the data**

Run: `uv run python "$SNAP/snapshot.py" example "$SNAP/after2" && diff -r "$SNAP/before" "$SNAP/after2"`
Expected: no diff.

Run: `uv run python example/manage.py shell -c "from django.contrib.auth import get_user_model as g; from customers.models import Customer as C; from catalog.models import Product as P; print(g().objects.count(), C.objects.count(), P.objects.count())"`
Expected: `41 60 40`.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "Layout: demo moves to example/, crud_views_tabler to src/"
```

---

### Task 3: Create `django_tabler`

**Files:**
- Create: `src/django_tabler/__init__.py`, `apps.py` (`DjangoTablerConfig`, `name = "django_tabler"`), `tests.py`, `templatetags/__init__.py`
- Create: `src/django_tabler/icons.py`, holding `ICONS` and `svg()` from `crud_views_tabler/icons.py`, with a docstring that does not mention crud-views
- Move: `example/dashboard/templatetags/tabler.py` to `src/django_tabler/templatetags/tabler.py`, and delete the now empty `dashboard/templatetags/`
- Move into `src/django_tabler/templates/django_tabler/`: `base.html`, `layouts/app.html`, `includes/navbar.html`, `includes/brand.html`, `includes/field.html`
- Move: `example/templates/registration/login.html` to `src/django_tabler/templates/registration/login.html`
- Move: `example/templates/crud_views_page.html` to `src/crud_views_tabler/templates/crud_views_tabler/page.html`
- Create in `src/django_tabler/templates/django_tabler/includes/`: `site_name.html`, `nav_menu.html`, `messages.html`
- Create in `example/templates/django_tabler/includes/`: `site_name.html`, `nav_menu.html`, `brand.html`
- Modify: `src/crud_views_tabler/icons.py`, `checks.py`, `tests.py`; `example/config/settings.py`; `example/dashboard/templates/dashboard/index.html`, `user_list.html`; `example/dashboard/tests.py`

**Interfaces:**
- Produces:
  - `django_tabler.icons.ICONS: dict[str, list[str]]`
  - `django_tabler.icons.svg(name: str | None, css: str = "") -> SafeString`
  - Filter `message_alert(message) -> dict[str, str]` in the `tabler` library, with keys `css` and `icon`
  - `CRUD_VIEWS_EXTENDS = "crud_views_tabler/page.html"`
  - `{% block messages %}` in `django_tabler/layouts/app.html`
  - Unchanged: `crud_views_tabler.icons.render`, `TABLER_ICONS` and the `{% load tabler %}` name

- [ ] **Step 1: Write the failing tests**

In `src/django_tabler/tests.py`, render `django_tabler/includes/messages.html` with `{"messages": [Message(level, text, extra_tags)]}`:

```python
class MessagesIncludeTests(SimpleTestCase):
    def test_levels_map_to_alert_classes(self):
        # subTest: ERROR "alert alert-danger", WARNING "alert alert-warning", SUCCESS "alert alert-success",
        # INFO "alert alert-info", DEBUG "alert alert-secondary"; each output also contains "<svg"
    def test_custom_level_renders_as_info(self):
        # Message(35, "x") -> contains "alert alert-info"
    def test_body_is_escaped_and_safe_strings_pass(self):
        # "<b>x</b>" -> "&lt;b&gt;x&lt;/b&gt;"; mark_safe("<b>x</b>") -> "<b>x</b>"
    def test_extra_tags_reach_the_alert(self):
        # extra_tags="probe" -> class attribute contains "probe"

class PackageTests(SimpleTestCase):
    def test_package_does_not_reference_crud_views(self):
        # walk Path(django_tabler.__file__).parent, skipping tests.py and __pycache__;
        # no file matches r"crud_views|cv_"
    def test_default_site_name(self):
        # the file in the package reads exactly "Django Tabler", with no trailing newline
    def test_default_nav_menu_is_empty(self):
        # the package's nav_menu.html renders to an empty string after strip()
```

Add to `crud_views_tabler/tests.py`:

```python
class MessagesParityTests(SimpleTestCase):
    def test_plain_include_matches_cv_messages(self):
        # for all five levels plus Message(35, "x") and extra_tags="probe", render
        # django_tabler/includes/messages.html and Template("{% load crud_views %}{% cv_messages %}")
        # with the same {"messages": [...]}; equal after re.sub(r"\s+", " ", html).strip() and
        # re.sub(r">\s+<", "><", html)
```

Add to `example/dashboard/tests.py`:

```python
class LayoutBoundaryTests(SimpleTestCase):
    def test_example_overrides_the_site_name(self):
        # render_to_string("django_tabler/includes/site_name.html") == "Acme Admin"
    def test_src_does_not_import_the_example(self):
        # under Path(django_tabler.__file__).parents[1], every .py except crud_views_tabler/tests.py
        # has no line matching r"^\s*(from|import)\s+(catalog|customers|dashboard|config)\b"
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `uv run python example/manage.py test django_tabler dashboard.tests.LayoutBoundaryTests crud_views_tabler.tests.MessagesParityTests`
Expected: import or `ModuleNotFoundError` failures, because `django_tabler` does not exist yet.

- [ ] **Step 3: Split the icons and move the tag library**

- `crud_views_tabler/icons.py` keeps `TABLER_ICONS` and `render()`, and imports `svg` from `django_tabler.icons`.
- `checks.py` imports `ICONS` from `django_tabler.icons` and `render` from `crud_views_tabler.icons`, and names `django_tabler.icons.ICONS` in its docstring and hint.
- `crud_views_tabler/tests.py` imports each name from its new home. No `mock.patch` target names a moved symbol.
- `tabler.py` imports `svg` from `django_tabler.icons`. Add the `message_alert` filter:
  - It looks up `message.level` (default `INFO`) and returns `css` and `icon`.
  - `DEBUG`: `alert alert-secondary`, `bug`
  - `INFO`: `alert alert-info`, `info-circle`
  - `SUCCESS`: `alert alert-success`, `check`
  - `WARNING`: `alert alert-warning`, `alert-triangle`
  - `ERROR`: `alert alert-danger`, `alert-circle`
  - Any other level renders as `INFO`.

- [ ] **Step 4: Move and namespace the templates**

- Every `extends` and `include` of `base.html`, `layouts/app.html` and `includes/*` gains the `django_tabler/` prefix, including those in `dashboard/index.html`, `dashboard/user_list.html`, `login.html` and `page.html`.
- `settings.py`: add `'django_tabler'` before `'crud_views_tabler'`, and set `CRUD_VIEWS_EXTENDS = 'crud_views_tabler/page.html'`.

- [ ] **Step 5: Split out the Acme content**

- `site_name.html` has no trailing newline in either copy, or `<span>Acme Admin</span>` gains a space. Package: `Django Tabler`. Example: `Acme Admin`.
- `base.html` (title), `layouts/app.html` (footer) and `brand.html` include `site_name.html` in place of the literal.
- The `<li>` items of `navbar.html` move verbatim to the example's `nav_menu.html`, which starts with `{% load tabler %}`. `navbar.html` includes `nav_menu.html` inside its `<ul>`. The package's `nav_menu.html` is empty.
- The package's `brand.html` keeps the same markup but links to `/`. The example's `brand.html` keeps `{% url 'dashboard:index' %}` and today's icon.

- [ ] **Step 6: Replace `cv_messages` in the layout**

- `layouts/app.html`: drop `{% load crud_views %}` and use `{% block messages %}{% include "django_tabler/includes/messages.html" %}{% endblock %}`.
- `crud_views_tabler/page.html`: add `{% block messages %}{% cv_messages %}{% endblock %}`.
- `messages.html` loops over `messages` and reproduces the frame in `crud_views_tabler/templates/crud_views/tags/alert.html` for a dismissible alert with no heading, using `message|message_alert` and `{% icon alert.icon "alert-icon" %}`. Read `../django-crud-views/src/crud_views/templates/crud_views/snippets/alert/text.html` for the body markup. The parity test decides the exact output.

- [ ] **Step 7: Run the new tests to verify they pass**

Run the command from Step 2.
Expected: all pass.

- [ ] **Step 8: Run all tests and compare the pages**

Run the test command from Task 3 on.
Expected: the 84 baseline tests plus the new ones, with exactly the 4 expected failures.

Run: `uv run python "$SNAP/snapshot.py" example "$SNAP/after3" && diff -r "$SNAP/before" "$SNAP/after3"`
Expected: no diff.

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "django_tabler: shared templates, tags and icons, with Acme content in the example"
```

---

### Task 4: Copy `crispy_tabler` into the repository

**Files:**
- Create: `src/crispy_tabler/`, `scripts/vendor_templates.py`, `tests/__init__.py`, `tests/crispy_tabler/` (all from sibling commit `2f86558`)
- Modify: `pyproject.toml`, `uv.lock`, `docs/crispy_tabler_coverage.md`

**Interfaces:**
- Consumes: the Task 2 build configuration, whose `"*"` package data already covers the pack's templates.
- Produces: the import name `crispy_tabler`, unchanged; the command `uv run --group test pytest`.

- [ ] **Step 1: Copy from the commit, not the working tree**

```bash
git -C ../crispy-tabler archive 2f86558 src/crispy_tabler scripts | tar -x -C .
mkdir -p tests/crispy_tabler && touch tests/__init__.py
git -C ../crispy-tabler archive 2f86558 tests | tar -x --strip-components=1 -C tests/crispy_tabler
```

- [ ] **Step 2: Adjust the copied tests and the script**

- Under `tests/crispy_tabler/`, replace `tests.forms`, `tests.helpers` and `"tests.urls"` with `tests.crispy_tabler.forms`, `tests.crispy_tabler.helpers` and `"tests.crispy_tabler.urls"`.
- `scripts/vendor_templates.py`: `DEST` still resolves correctly, because `scripts/` and `src/` keep their relative positions, so it needs no change. This corrects the spec's "DEST adjusted". Change the docstring's usage line to `uv run --group test python scripts/vendor_templates.py [--force]`.

- [ ] **Step 3: Update `pyproject.toml`**

- Remove `crispy-tabler` from `dependencies` and from `[tool.uv.sources]`.
- Add `"django-crispy-forms>=2.4"` and `"crispy-bootstrap5>=2026.9"` to `dependencies`.
- Add:

```toml
[dependency-groups]
test = ["pytest", "pytest-django", "crispy-bootstrap5==2026.9"]

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "tests.crispy_tabler.settings"
pythonpath = ["."]
testpaths = ["tests"]
addopts = "--strict-markers"
```

- [ ] **Step 4: Sync and check where the package comes from**

Run: `uv sync && uv run python -c "import crispy_tabler; print(crispy_tabler.__file__)"`
Expected: a path under this repository's `src/`, not `../crispy-tabler`.

- [ ] **Step 5: Run the crispy suite**

Run: `uv run --group test pytest`
Expected: 34 passed, the same as in the sibling.

Run: `uv run --group test python scripts/vendor_templates.py`
Expected: it refuses to run because of the hand-edited templates, and `git status src/crispy_tabler` shows no new changes compared with the copy.

- [ ] **Step 6: Run the Django tests and compare the pages**

Run the test command from Task 3 on.
Expected: exactly the 4 expected failures.

Run: `uv run python "$SNAP/snapshot.py" example "$SNAP/after4" && diff -r "$SNAP/before" "$SNAP/after4"`
Expected: no diff.

Run: `git -C ../crispy-tabler status --short`
Expected: no output.

- [ ] **Step 7: Record the source and commit**

Add one line to `docs/crispy_tabler_coverage.md`: `crispy_tabler` was copied from `jacob-consulting/crispy-tabler` at `2f86558`; this repository now holds the working copy, and nothing syncs back automatically.

```bash
git add -A
git commit -m "crispy_tabler: copy into src/ from sibling 2f86558, tests under tests/crispy_tabler"
```

---

### Task 5: Documentation and final verification

**Files:**
- Modify: `README.md`, `docs/crud_views_tabler.md`

- [ ] **Step 1: Update `README.md`**

- Run commands use `uv run python example/manage.py ...`, and include `seed_demo_catalog`.
- Say that only django-crud-views is still a sibling dependency, and add the `/product/` row to the pages table, which lacks it.
- Rewrite the Layout section to the spec's target layout.
- Tests section: the Task 3 test command and `uv run --group test pytest`.

- [ ] **Step 2: Update `docs/crud_views_tabler.md`**

- Lines 31, 37 and 38: `crud_views_tabler/page.html` is now part of the theme, not a project template. It extends `django_tabler/layouts/app.html`.
- Lines 279 and 280: `{% cv_messages %}` is now in `crud_views_tabler/page.html`, and the layout's default is `django_tabler/includes/messages.html`.

- [ ] **Step 3: Check that a built wheel carries its data**

Run: `uv build --wheel -o "$SNAP/dist" && uv run python -m zipfile -l "$SNAP"/dist/*.whl | grep -cE "(django_tabler/templates/django_tabler/base\.html|crud_views_tabler/templates/crud_views_tabler/page\.html|crud_views_tabler/static/crud_views_tabler/crud_views_tabler\.css|crispy_tabler/templates/crispy_tabler/)"`
Expected: more than 40 matches. Separately, `uv run python -m zipfile -l "$SNAP"/dist/*.whl | grep -E "^(catalog|customers|dashboard|config)/"` prints nothing.

- [ ] **Step 4: Run everything once more**

Run:

```bash
uv sync
uv run python example/manage.py check
uv run python example/manage.py test django_tabler crud_views_tabler dashboard catalog customers
uv run --group test pytest
uv run python "$SNAP/snapshot.py" example "$SNAP/final" && diff -r "$SNAP/before" "$SNAP/final"
git -C ../crispy-tabler status --short
git status --short
```

Expected: `check` reports no issues; the Django run has exactly the 4 expected failures; pytest reports 34 passed; no page diff; both status commands show nothing except this task's documents before the commit.

Run the Task 2 data count again. Expected: `41 60 40`.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/crud_views_tabler.md
git commit -m "Docs: README and theme notes follow the new layout"
```
