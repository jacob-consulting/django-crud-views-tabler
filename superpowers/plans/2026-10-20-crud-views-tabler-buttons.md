# crud_views_tabler on django-crud-views buttons (#201, #204): Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete the theme's button-only template overrides and `TablerDeleteForm`. Express the Tabler button look
as entries in django-crud-views' button class table, and restore below-toolbar tooltips through the tooltip
adapter.

**Architecture:** `CrudViewsTablerConfig.ready()` registers a `TABLER_BUTTON_CLASSES` dict
(`crud_views_tabler/buttons.py`) with upstream's `register_button_classes()`. The action buttons, containers, menu
toggle, filter toggle and card-order bar render through upstream's stock logic templates and leaves. Only
`tags/card.html` stays among the button-related overrides, because it carries the card layout and blocks; its
footer includes upstream's container leaf. `tabler-adapters.js` replaces `cv.adapters.tooltip.init` with a
location-aware Tabler tooltip.

**Tech Stack:** Python 3.14, Django 6.1, uv, django-crud-views main @ 4b62ed6 (editable path dependency
`../django-crud-views`), Tabler 1.6.1 (CDN), crispy-bootstrap5. Tests: Django `TestCase` via
`uv run python manage.py test`.

**Spec:** `docs/superpowers/specs/2026-10-20-crud-views-tabler-buttons-design.md`

## Global Constraints

- Python 3.14, Django 6.1, uv. Tests: `uv run python manage.py test`. `uv run python manage.py check --fail-level WARNING` passes (an existing test asserts it).
- Tabler 1.6.1 from the CDN; `tabler.min.js` loads `defer` at the end of `templates/base.html`. Do not change the script order. The tooltip adapter resolves `globalThis.tabler` at call time.
- No inline scripts (CSP).
- Stock markup wins: no theme override of any `crud_views/tags/button/*.html` leaf, and no theme template that copies upstream branching (`cv_disabled` / POST / modal decisions, loops over `group.inline`).
- The theme writes no `data-cv-tooltip` and no `data-bs-toggle="tooltip"`; upstream owns the marker.
- No button class literal (`btn`) left in theme templates (grep gate in Task 5).
- Every key the theme registers is in upstream's `DEFAULT_BUTTON_CLASSES`, so `crud_views.W362` never fires.
- Upstream checkout: `../django-crud-views`, `main` @ 4b62ed6. References: `src/crud_views/lib/button_classes.py`, `src/crud_views/lib/crispy/form.py` (`CrispyDeleteForm`), `src/crud_views/templates/crud_views/tags/button/*.html`, `src/crud_views/templates/crud_views/tags/card.html`, `docs/reference/buttons.md`, `docs/reference/javascript.md#tooltips`.

## Review Focus

1. **Disabled actions:** a user without delete permission, with `cv_inaccessible_actions = "disable"`, still gets a
   disabled `<button data-cv-disabled="permission">`, now from the stock leaf, styled by `list:danger` (Task 2,
   `test_disabled_action_renders_a_tabler_icon`, extended).
2. **Project settings win over the theme:** `CRUD_VIEWS_BUTTON_CLASSES = {"list:danger": "x-danger"}` renders
   `x-danger` on the row delete (Task 1, `test_project_setting_wins_over_the_theme_classes`).
3. **Overflow menus:** a list with `cv_list_actions_inline = ["detail"]` renders the `⋯` toggle with the theme's
   `list:menu-toggle` classes inside a `dropdown` wrapper, and the menu items keep the fixed-width icon slot (Task 2,
   `test_overflow_menu_uses_theme_classes`).
4. **Tooltips without Tabler:** if `globalThis.tabler?.Tooltip` is missing when the adapter runs, it does nothing
   instead of throwing (Task 3, guard asserted by `test_tooltip_adapter_places_toolbar_tooltips_below`).
5. **Upstream renames or drops a key:** a registered theme key missing from `DEFAULT_BUTTON_CLASSES` fails a theme
   test, not only a warning (Task 1, `test_every_theme_key_is_an_upstream_key`).

---

## File structure

| File | Responsibility |
|---|---|
| `crud_views_tabler/buttons.py` (new) | `TABLER_BUTTON_CLASSES: dict[str, str]`, the theme's class table |
| `crud_views_tabler/apps.py` | registers `TABLER_BUTTON_CLASSES` in `ready()` |
| `crud_views_tabler/forms.py` | deleted |
| `customers/views.py` | `CustomerDeleteView.form_class = CrispyDeleteForm` |
| `crud_views_tabler/templates/crud_views/tags/card.html` | footer includes upstream's container leaf |
| 9 templates under `crud_views_tabler/templates/crud_views/` | deleted (Task 2) |
| `crud_views_tabler/static/crud_views_tabler/tabler-adapters.js` | location-aware tooltip `init` |
| `crud_views_tabler/tests.py` | tests per task |
| `docs/crud_views_tabler.md`, `docs/crud_views_upstream_questions.md`, `docs/crud_views_tooltips.md` | docs (Task 4) |

---

### Task 1: Theme class table and the stock delete form

**Files:**
- Create: `crud_views_tabler/buttons.py`
- Modify: `crud_views_tabler/apps.py` (`ready()`, docstring)
- Modify: `customers/views.py` (import and `CustomerDeleteView.form_class`)
- Delete: `crud_views_tabler/forms.py`
- Test: `crud_views_tabler/tests.py` (new class `ButtonClassTests(SimpleTestCase)`, plus the existing delete tests)

**Interfaces:**
- Consumes: `crud_views.lib.button_classes.register_button_classes(dict)`, `get_button_classes() -> dict`,
  `DEFAULT_BUTTON_CLASSES`; `crud_views.lib.crispy.CrispyDeleteForm`.
- Produces: `crud_views_tabler.buttons.TABLER_BUTTON_CLASSES: dict[str, str]`, registered at startup. Task 2's
  markup assertions rely on these exact strings.

- [ ] **Step 1: Write the failing tests**

```python
from crud_views.lib.button_classes import DEFAULT_BUTTON_CLASSES, get_button_classes
from crud_views_tabler.buttons import TABLER_BUTTON_CLASSES


class ButtonClassTests(SimpleTestCase):
    def test_theme_classes_are_registered(self):
        resolved = get_button_classes()
        for key, classes in TABLER_BUTTON_CLASSES.items():
            self.assertEqual(resolved[key], classes, key)

    def test_every_theme_key_is_an_upstream_key(self):
        self.assertLessEqual(set(TABLER_BUTTON_CLASSES), set(DEFAULT_BUTTON_CLASSES))

    def test_table_values(self):  # the spec's table, verbatim
        expected = {
            "context:primary": "btn btn-primary btn-icon",
            "context:secondary": "btn btn-icon",
            "context:tertiary": "btn btn-icon",
            "context:danger": "btn btn-icon btn-outline-danger",
            "list:primary": "btn btn-sm btn-icon btn-ghost-primary",
            "list:secondary": "btn btn-sm btn-icon btn-ghost-secondary",
            "list:tertiary": "btn btn-sm btn-icon btn-ghost-secondary",
            "list:danger": "btn btn-sm btn-icon btn-ghost-danger",
            "card:primary": "btn btn-sm btn-primary",
            "card:secondary": "btn btn-sm",
            "card:tertiary": "btn btn-sm btn-icon btn-ghost-secondary",
            "card:danger": "btn btn-sm btn-ghost-danger",
            "context:container": "btn-list",
            "list:container": "btn-list flex-nowrap justify-content-end gap-1",
            "card:container": "btn-list",
            "context:menu-toggle": "btn btn-icon",
            "list:menu-toggle": "btn btn-sm btn-icon btn-ghost-secondary",
            "card:menu-toggle": "btn btn-sm btn-icon",
            "context:menu-wrapper": "dropdown",
            "list:menu-wrapper": "dropdown",
            "form:delete": "btn btn-danger",
            "card-order:toggle": "btn btn-icon",
            "card-order:container": "btn-group",
            "formset:control": "btn btn-icon",
            "formset:control-danger": "btn btn-icon btn-danger",
        }
        self.assertEqual(TABLER_BUTTON_CLASSES, expected)

    @override_settings(CRUD_VIEWS_BUTTON_CLASSES={"list:danger": "x-danger"})
    def test_project_setting_wins_over_the_theme_classes(self):
        self.assertEqual(get_button_classes()["list:danger"], "x-danger")
```

In `ThemeRenderingTests`, add a full-page delete test next to the existing modal one, and keep
`test_delete_modal_partial_has_no_card_and_a_danger_button` unchanged (it asserts `btn btn-danger`):

```python
    def test_delete_form_is_the_stock_crispy_delete_form(self):
        from crud_views.lib.crispy import CrispyDeleteForm
        self.assertIs(CustomerDeleteView.form_class, CrispyDeleteForm)
        html = self.client.get(reverse("customer-delete", args=[self.customer.pk])).content.decode()
        self.assertRegex(html, r'<input type="submit"[^>]*class="btn btn-danger"')
        self.assertNotIn("btn-primary btn-danger", html)
```

`test_project_setting_wins_over_the_theme_classes` relies on upstream's `setting_changed` receiver to reset the cache;
add no manual reset.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run python manage.py test crud_views_tabler.tests.ButtonClassTests crud_views_tabler.tests.ThemeRenderingTests.test_delete_form_is_the_stock_crispy_delete_form`
Expected: ImportError on `crud_views_tabler.buttons` (the whole module fails to import; that is the failure).

- [ ] **Step 3: Implement**

- `crud_views_tabler/buttons.py`: a module docstring (one line, like `icons.py`'s style) and `TABLER_BUTTON_CLASSES`
  with exactly the dict above.
- `apps.py` `ready()`: import `register_button_classes` and `TABLER_BUTTON_CLASSES` next to the existing local
  imports and call `register_button_classes(TABLER_BUTTON_CLASSES)`. Extend the class docstring: it also registers
  the Tabler button classes, so projects need no button settings.
- `customers/views.py`: import `CrispyDeleteForm` from `crud_views.lib.crispy` (extend the existing import line),
  drop the `crud_views_tabler.forms` import, set `form_class = CrispyDeleteForm`.
- Delete `crud_views_tabler/forms.py`.

- [ ] **Step 4: Run the full suite**

Run: `uv run python manage.py test`
Expected: all pass, including `test_system_checks_pass` (no `W362`). The old templates are still in place, so
markup tests are unaffected.

- [ ] **Step 5: Commit**

```bash
git add crud_views_tabler/buttons.py crud_views_tabler/apps.py customers/views.py crud_views_tabler/tests.py
git rm crud_views_tabler/forms.py
git commit -m "Theme: register Tabler button classes; stock CrispyDeleteForm replaces TablerDeleteForm"
```

---

### Task 2: Drop the button overrides; card footer through the container leaf

**Files:**
- Delete (all under `crud_views_tabler/templates/crud_views/`): `tags/context_action.html`, `tags/list_action.html`,
  `tags/list_action.inner.html`, `tags/card_action.html`, `tags/context_actions.html`, `columns/actions.html`,
  `tags/actions_menu_toggle.html`, `tags/context_action_filter.html`, `snippets/card_order.html`
- Modify: `crud_views_tabler/templates/crud_views/tags/card.html` (the `card_footer` block and the header comment)
- Modify: `crud_views_tabler/static/crud_views_tabler/crud_views_tabler.css` only if Step 6 shows a layout
  difference
- Test: `crud_views_tabler/tests.py`

**Interfaces:**
- Consumes: Task 1's registered classes. Upstream's `crud_views/tags/button/container.html`, called with
  `cv_buttons`, `cv_group`, `cv_location`, `cv_container_tag`. `{% cv_render_list_action_form ctx %}`.
  `{% cv_card_action_group object as group %}`, which always returns an `ActionGroup` on main.
- Produces: the stock DOM described below; Task 5 checks it in the browser.

- [ ] **Step 1: Write the failing tests**

Extend `test_near_copies_of_upstream_templates_are_not_overridden` (rename it
`test_upstream_templates_are_not_overridden`) to cover the nine deleted names too:

```python
        for name in ("crud_views/modal/content.html", "crud_views/tags/actions_menu_item_label.html",
                     "crud_views/tags/breadcrumb.html", "crud_views/tags/context_action.html",
                     "crud_views/tags/list_action.html", "crud_views/tags/card_action.html",
                     "crud_views/tags/context_actions.html", "crud_views/columns/actions.html",
                     "crud_views/tags/actions_menu_toggle.html", "crud_views/tags/context_action_filter.html",
                     "crud_views/snippets/card_order.html"):
            self.assertNotIn("crud_views_tabler", get_template(name).origin.name, name)
        with self.assertRaises(TemplateDoesNotExist):
            get_template("crud_views/tags/list_action.inner.html")
        for name in ("crud_views/tags/button/action.html", "crud_views/tags/button/container.html",
                     "crud_views/tags/button/menu_item.html", "crud_views/tags/button/menu_item_label.html"):
            self.assertNotIn("crud_views_tabler", get_template(name).origin.name, name)
```

(`TemplateDoesNotExist` from `django.template`.) Add, in `ThemeRenderingTests`, a helper `tag(html, key)` that
returns the first opening `<a …>` / `<button …>` tag with `cv-key="<key>"`, and use it in these tests:

```python
    def test_toolbar_uses_theme_classes(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        create = self.tag(html, "create")
        self.assertIn('class="btn btn-primary btn-icon"', create)
        self.assertIn('data-cv-tooltip="context"', create)
        self.assertIn('class="btn btn-icon active"', self.tag(html, "list"))
        self.assertIn('aria-current="page"', self.tag(html, "list"))
        self.assertRegex(html, r'<fieldset class="btn-list" aria-label="Actions" cv-context-container="true">')

    def test_row_actions_use_theme_classes(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        delete = self.tag(html, "delete")
        self.assertIn('class="btn btn-sm btn-icon btn-ghost-danger"', delete)
        self.assertIn('data-cv-tooltip="list"', delete)
        self.assertIn('class="btn btn-sm btn-icon btn-ghost-secondary"', self.tag(html, "update"))
        self.assertIn('<fieldset class="btn-list flex-nowrap justify-content-end gap-1"', html)

    def test_overflow_menu_uses_theme_classes(self):
        with mock.patch.object(CustomerListView, "cv_list_actions_inline", ["detail"]):
            html = self.client.get(reverse("customer-list")).content.decode()
        self.assertIn('<div class="dropdown">', html)
        self.assertRegex(html, r'class="btn btn-sm btn-icon btn-ghost-secondary dropdown-toggle cv-menu-toggle"')
```

Change these existing tests:
- `test_list_uses_tabler_table_and_icons`: keep as is (`btn-ghost-danger` now comes from the table).
- `test_disabled_action_renders_a_tabler_icon`: also assert that the disabled button's `class` is
  `btn btn-sm btn-icon btn-ghost-danger`.
- `test_filter_toggle_contract`: `data-cv-tooltip` becomes `data-cv-tooltip="context"`; add
  `class="btn btn-icon"`.
- `test_action_tooltips_are_initialised_by_crud_views`: additionally assert every context button tag (`cv-key` of
  `list`, `card`, `create`, plus the filter toggle) has `data-cv-tooltip="context"`.
- `CardThemeTests.test_card_action_variants`: `btn btn-sm btn-primary flex-grow-1` (unchanged), tertiary becomes
  `btn btn-sm btn-icon btn-ghost-secondary`, and the labelled detail button renders `<span>Open</span>`.
- `CardThemeTests.test_cards_render_in_tabler_grid`: also assert
  `html.count('class="btn-list" cv-card-container="true"') == 12`.
- `CardThemeTests.test_order_bar`: replace the literal with
  `assertRegex(html, r'value="desc"\s+class="btn btn-icon active"')` and assert `<fieldset class="btn-group"`.
- `CardThemeTests.test_icon_only_card_action_has_a_crud_views_tooltip`: `btn-icon` stays;
  `data-cv-tooltip="card"`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run python manage.py test crud_views_tabler`
Expected: FAIL in the new and changed tests (theme origins, `fieldset`, `data-cv-tooltip="…"` values).

- [ ] **Step 3: Delete the nine templates and rewire `tags/card.html`**

Replace the `card_footer` block body with the version in the spec (§3): a `card-footer` div containing the
`group.menu` forms loop and the `include` of `crud_views/tags/button/container.html` with `cv_buttons=group.inline
cv_group=group cv_location="card" cv_container_tag="div"`. Drop the `group is None` branch. In the header comment,
replace "the actions row" with "the actions row (crud_views' container leaf)"; keep the block list.

- [ ] **Step 4: Run the full suite**

Run: `uv run python manage.py test`
Expected: all pass.

- [ ] **Step 5: Grep gate**

Run: `grep -rnE "\bbtn\b|btn-|data-cv-tooltip|data-bs-toggle" crud_views_tabler/templates`
Expected: no output.

- [ ] **Step 6: Layout check in the browser**

`uv run python manage.py runserver`, log in, open `/customers/` (list) and the card view. Check:
- toolbar and row buttons sit in a row with Tabler's gap
- row buttons do not wrap and stay right-aligned in the last cell (the `td:has(> [cv-list-container])` rule)

If `fieldset.btn-list` differs from the former `div.btn-list`, add the smallest rule to `crud_views_tabler.css`
with a one-line comment in the file's style. Otherwise change nothing.

- [ ] **Step 7: Commit**

```bash
git add -A crud_views_tabler
git commit -m "Theme: drop the action, container, menu toggle, filter toggle and card order overrides; card footer uses the container leaf"
```

---

### Task 3: Toolbar tooltips below the button

**Files:**
- Modify: `crud_views_tabler/static/crud_views_tabler/tabler-adapters.js`
- Test: `crud_views_tabler/tests.py` (`ThemeRenderingTests`)

**Interfaces:**
- Consumes: `cv.adapters`, `cv.bootstrapAdapters(ns)` and the `init(el, {location})` contract from upstream's
  `docs/reference/javascript.md#tooltips`.
- Produces: `cv.adapters.tooltip.init(el, {location} = {})`, which places tooltips `bottom` for `location ===
  "context"` and `top` otherwise, and does nothing when `globalThis.tabler?.Tooltip` is missing.

- [ ] **Step 1: Write the failing test**

```python
    def test_tooltip_adapter_places_toolbar_tooltips_below(self):
        from django.contrib.staticfiles import finders
        source = open(finders.find("crud_views_tabler/tabler-adapters.js"), encoding="utf-8").read()
        self.assertIn("cv.bootstrapAdapters(() => globalThis.tabler)", source)
        self.assertIn("cv.adapters.tooltip.init", source)
        self.assertIn('location === "context"', source)
        self.assertIn('"bottom"', source)
        self.assertIn("globalThis.tabler?.Tooltip", source)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run python manage.py test crud_views_tabler.tests.ThemeRenderingTests.test_tooltip_adapter_places_toolbar_tooltips_below`
Expected: FAIL on `cv.adapters.tooltip.init`.

- [ ] **Step 3: Implement**

After the existing `Object.assign(...)` line, assign `cv.adapters.tooltip.init` as in upstream's recipe. Read
`globalThis.tabler?.Tooltip` once per call, return early if it is missing, then call
`getOrCreateInstance(el, {placement: location === "context" ? "bottom" : "top"})`. Add one comment line explaining
the placement: below the toolbar, so tooltips do not cover the page header.

- [ ] **Step 4: Run the full suite**

Run: `uv run python manage.py test`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add crud_views_tabler/static/crud_views_tabler/tabler-adapters.js crud_views_tabler/tests.py
git commit -m "Theme: toolbar tooltips below the button through cv.adapters.tooltip (location-aware init)"
```

---

### Task 4: Docs

**Files:**
- Modify: `docs/crud_views_tabler.md`
- Modify: `docs/crud_views_upstream_questions.md` (points 2, 4, 5, and the "How this was checked" update line)
- Modify: `docs/crud_views_tooltips.md` ("What the theme does meanwhile")

**Interfaces:**
- Consumes: the final state from Tasks 1–3.

- [ ] **Step 1: `docs/crud_views_tabler.md`**

Update the sections "Header and actions", "Card views", "Forms (crispy)", "JavaScript" and "Overridden templates":
- The class table: point to `crud_views_tabler/buttons.py`. Explain the variant mapping: create is primary, delete
  is danger, `CardAction.variant` overrides. State that projects override keys with `CRUD_VIEWS_BUTTON_CLASSES`.
- The accepted visual differences, from the spec's table "Visible changes accepted by the maintainer".
- The `btn-icon` limitation on `card:tertiary`.
- The tooltip adapter and its placement.
- The 10 remaining overrides, each with one line on why it stays.
- `TablerDeleteForm` removed.

Remove every statement that describes the deleted templates as current.

- [ ] **Step 2: `docs/crud_views_upstream_questions.md`**

Below each existing "Status (upstream main @ 440ac55, 2026-10-20)" block of points 2, 4 and 5, add a "Status
(upstream main @ 4b62ed6, 2026-10-20)" block in the same style:
- **Point 2:** resolved by #201 (option A plus B; `register_button_classes()`, `CrispyDeleteForm.get_delete_button()`,
  slot `form:delete`). The theme registers classes and dropped `TablerDeleteForm`.
- **Point 4:** resolved by #201 variants. The theme no longer keys on `create` / `create_select`.
- **Point 5:** resolved for buttons by #201 and #204. 19 → 10 overrides, and no leaf override at all, fewer than the
  draft's "two leaf overrides" estimate, because the maintainer chose stock markup over the old look and #204 added
  the tooltip marker. List the 10 that stay, and why.

Add one line to "How this was checked" for the 4b62ed6 update.

- [ ] **Step 3: `docs/crud_views_tooltips.md`**

Retitle "What the theme does meanwhile" to "Resolved by #204". Describe what landed:
- the markers with location values
- `init(el, {location})`
- the object-detail trigger moving from `data-bs-title` to `title`
- the formset `title` translation
- the theme using the placement recipe

Change the "Draft" line at the top to say the issue is closed.

- [ ] **Step 4: Commit**

```bash
git add docs/crud_views_tabler.md docs/crud_views_upstream_questions.md docs/crud_views_tooltips.md
git commit -m "Docs: theme on the button class table and leaves; upstream points 2, 4, 5 resolved by #201/#204"
```

---

### Task 5: Verification

**Files:** none changed unless a check fails (then fix in the owning task's files and commit separately).

- [ ] **Step 1: Suite and checks**

Run: `uv run python manage.py test && uv run python manage.py check --fail-level WARNING`
Expected: all tests pass; "System check identified no issues".

- [ ] **Step 2: Anti-goal greps**

Run: `grep -rnE "\bbtn\b|btn-|data-cv-tooltip|data-bs-toggle" crud_views_tabler/templates; ls crud_views_tabler/templates/crud_views/tags/button 2>/dev/null; grep -rn "TablerDeleteForm\|DangerSubmit" --include=*.py --include=*.md . | grep -v "^./.venv" | grep -v "docs/superpowers"`
Expected: no template hits. No `tags/button` directory in the theme. `TablerDeleteForm` appears only in the docs'
history passages (the upstream questions doc, with "removed").

- [ ] **Step 3: Browser check**

Run `uv run python manage.py runserver` and log in with the demo user. Check each of the following, and note
anything that fails:
- **List:**
  - The toolbar shows icon buttons with a blue icon-only Create; "list" is active.
  - Hovering or focusing a toolbar button shows a Tabler tooltip below it.
  - The filter toggle opens and closes the panel and swaps its icon.
  - Row buttons are ghost icons with a red delete, right-aligned and unwrapped; their tooltips show above.
- **Card view:**
  - The footer shows a blue flex "Open", "Edit" and the square icon-only delete with a tooltip.
  - The order select and the asc/desc toggles reorder.
- **Detail page:** if the toolbar has a delete action (upstream's default `detail_context_actions`), it is outlined
  red.
- **Update form:** submit and cancel render and work.
- **Delete modal:** opened from a row, it shows a red Delete; cancel and the close button close it; Delete deletes.
- **Console:** no errors.

- [ ] **Step 4: Report**

Report the results. State plainly what was not checked:
- tooltips inside a modal (the demo's delete modal has no trigger; upstream's vitest covers `cv:modal:loaded`)
- formset controls (no formsets in the demo)
- disabled actions in the browser (covered by a test only)
