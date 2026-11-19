# crispy_tabler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `crispy-tabler`, a self-contained django-crispy-forms template pack for Tabler, in a new sibling repository, and switch this demo onto it so the six findings in `docs/crispy_tabler_coverage.md` render correctly.

**Architecture:** One Django app, `crispy_tabler`, whose name is the crispy template pack. All 42 template names are vendored from crispy-bootstrap5 2026.9 with every internal include rewritten to the new pack, so no `bootstrap5/` path survives inside it. Six templates change; the rest stay byte-identical apart from the include prefix and a provenance header, which is what keeps the next re-diff cheap. `field.html` grows two branches fed by the pack's own template filters, and `layout.py` replaces the two crispy-bootstrap5 layout objects that hardcode their template path.

**Tech Stack:** Python ≥ 3.12, Django ≥ 5.2, django-crispy-forms ≥ 2.4 (2.7 installed), crispy-bootstrap5 ≥ 2026.9 (test dependency and vendoring source), uv, pytest + pytest-django in the package; the demo keeps `uv run python manage.py test`.

**Spec:** `docs/superpowers/specs/2026-10-21-crispy-tabler-design.md`

## Global Constraints

- New repository: `../crispy-tabler`. Distribution `crispy-tabler`, Django app and template pack `crispy_tabler`, `src/` layout, setuptools backend, MIT, English.
- Python ≥ 3.12; Django ≥ 5.2 only — **not** 4.2. crispy-bootstrap5 2026.9 and django-crispy-forms 2.7 both declare `Requires-Dist: django>=5.2`.
- Vendoring source is crispy-bootstrap5 **2026.9**, read from `<repo>/.venv/lib/python3.14/site-packages/crispy_bootstrap5/templates/bootstrap5/`.
- The pack must contain these 42 template names and no others in wave 1: `accordion-group.html accordion.html betterform.html display_form.html errors_formset.html errors.html field.html inputs.html multifield.html table_inline_formset.html uni_form.html uni_formset.html whole_uni_form.html whole_uni_formset.html` plus under `layout/`: `alert.html attrs.html baseinput.html button.html buttonholder.html checkboxselectmultiple_inline.html column.html div.html field_errors.html field_errors_block.html field_file.html field_with_buttons.html fieldset.html floating_field.html formactions.html help_text.html help_text_and_errors.html inline_field.html modal.html multifield.html prepended_appended_text.html radio_checkbox_select.html radioselect_inline.html row.html switch.html tab-link.html tab.html uneditable_input.html` (plus `widget/` for the package's own widgets).
- **No `bootstrap5` string anywhere under `src/crispy_tabler/templates/`.** A test enforces this.
- The package must not import `crud_views`, and must not ship CSS.
- Tabler class vocabulary is 1.6.1, verified against `<tabler archives>/tabler-1.6.1/dashboard/dist/css/tabler.css`.
- Never write the name of the maintainer's internal reference package in any file, commit message or comment.
- Acceptance surface: `/product/create/` in this demo, pinned by `catalog/tests.py`.

## Review Focus

Five things the spec requires implicitly and no obvious task test covers. Each has a test added to the task that owns the code.

1. **A range or colour field with a validation error** must get `is-invalid` next to `form-range` / `form-control-color`. Every other branch in `field.html` pairs its class with an error variant; new branches are the likely place to forget. (Task 3)
2. **A hidden field** must still short-circuit at the top of `field.html` and render as a bare widget, with no label, wrapper or help text. (Task 3)
3. **A horizontal form** (`helper.form_class = "form-horizontal"`, `label_class`, `field_class`) must keep its `col-form-label` / column wrappers through the edited templates. (Task 4)
4. **A file field with help text** must render its help text exactly once. `field.html` guards this with `{% if not field|is_file %}` because `field_file.html` emits it itself; editing around that guard duplicates or loses it. (Task 3)
5. **A field rendered inside a table formset** (`table_inline_formset.html` renders `field.html` with `tag="td"`) must not emit the checkbox wrapper `<div>`s, which `field.html` suppresses with `and tag != "td"`. (Task 3)

---

## File structure

| File | Responsibility |
|---|---|
| `crispy-tabler/pyproject.toml` | distribution metadata, deps, pytest config |
| `crispy-tabler/README.md`, `LICENSE`, `CHANGELOG.md`, `.gitignore` | packaging |
| `crispy-tabler/src/crispy_tabler/__init__.py`, `apps.py` | the Django app (no models, no urls, no `ready()`) |
| `crispy-tabler/src/crispy_tabler/vendored.py` | `CRISPY_BOOTSTRAP5_VERSION`, the provenance the parity test reads |
| `crispy-tabler/src/crispy_tabler/templatetags/crispy_tabler_field.py` | `is_range`, `is_color` |
| `crispy-tabler/src/crispy_tabler/layout.py` | `FloatingField`, `Switch` with `%s`-relative templates |
| `crispy-tabler/src/crispy_tabler/widgets.py` | `PlaintextInput`, `RangeInput`, `ColorInput` |
| `crispy-tabler/src/crispy_tabler/fields.py` | form fields binding those widgets |
| `crispy-tabler/src/crispy_tabler/templates/crispy_tabler/**` | the 42 vendored templates + `widget/` |
| `crispy-tabler/tests/settings.py`, `tests/forms.py`, `tests/test_*.py` | pytest-django suite |
| `tabler-test/pyproject.toml`, `config/settings.py` | editable dependency, app list, pack setting |
| `tabler-test/catalog/views.py`, `catalog/tests.py` | import swap, updated markers |
| `tabler-test/docs/crispy_tabler_coverage.md` | result recorded |

---

### Task 1: The package, installable and importable

**Files:**
- Create: `crispy-tabler/pyproject.toml`, `README.md`, `LICENSE`, `CHANGELOG.md`, `.gitignore`
- Create: `crispy-tabler/src/crispy_tabler/__init__.py`, `apps.py`, `vendored.py`
- Create: `crispy-tabler/tests/settings.py`, `tests/test_app.py`
- Modify: `tabler-test/pyproject.toml`

**Interfaces:**
- Produces: app label `crispy_tabler`; `crispy_tabler.vendored.CRISPY_BOOTSTRAP5_VERSION: str`

- [ ] **Step 1: `git init` the repository and write the packaging files**

`pyproject.toml`: setuptools backend, `name = "crispy-tabler"`, `version = "0.1.0"`, `requires-python = ">=3.12"`, `dependencies = ["django>=5.2", "django-crispy-forms>=2.4"]`, optional `test = ["pytest", "pytest-django", "crispy-bootstrap5>=2026.9"]`, `[tool.setuptools.packages.find] where = ["src"]`, `[tool.pytest.ini_options] DJANGO_SETTINGS_MODULE = "tests.settings"`. Classifiers for Django 5.2 / 6.0 / 6.1 and Python 3.12–3.14, MIT, author as in `django-crud-views/pyproject.toml`.

`tests/settings.py`: `INSTALLED_APPS` of `django.contrib.contenttypes`, `django.contrib.auth`, `crispy_forms`, `crispy_bootstrap5`, `crispy_tabler`; `CRISPY_TEMPLATE_PACK = "crispy_tabler"`; `CRISPY_ALLOWED_TEMPLATE_PACKS = ("crispy_tabler", "bootstrap5")`; `APP_DIRS = True`; in-memory sqlite; a `SECRET_KEY`.

`vendored.py`: `CRISPY_BOOTSTRAP5_VERSION = "2026.9"` with a docstring saying it is the release the templates were copied from and that the parity test compares it to the installed distribution.

- [ ] **Step 2: Write the failing test**

```python
# tests/test_app.py
def test_app_is_installed_and_pack_is_selected():
    from django.apps import apps
    from crispy_forms.utils import TEMPLATE_PACK
    assert apps.is_installed("crispy_tabler")
    assert str(TEMPLATE_PACK) == "crispy_tabler"

def test_vendored_version_matches_the_installed_crispy_bootstrap5():
    from importlib.metadata import version
    from crispy_tabler.vendored import CRISPY_BOOTSTRAP5_VERSION
    assert version("crispy-bootstrap5") == CRISPY_BOOTSTRAP5_VERSION
```

- [ ] **Step 3: Run it and watch it fail**

Run: `cd ../crispy-tabler && uv run --extra test pytest tests/test_app.py -v`
Expected: collection error — `crispy_tabler` not importable.

- [ ] **Step 4: Write `src/crispy_tabler/__init__.py` and `apps.py`**

`apps.py`: `CrispyTablerConfig(AppConfig)` with `name = "crispy_tabler"` and `default_auto_field` unset (no models). `__init__.py` stays empty.

- [ ] **Step 5: Run it and watch it pass**

Run: same command. Expected: 2 passed.

- [ ] **Step 6: Add the editable dependency to the demo**

In `tabler-test/pyproject.toml`, add `"crispy-tabler"` to `dependencies` and `crispy-tabler = { path = "../crispy-tabler", editable = true }` to `[tool.uv.sources]`, next to the existing `django-crud-views` entry. Do **not** touch `INSTALLED_APPS` or `CRISPY_TEMPLATE_PACK` yet — that is Task 7.

- [ ] **Step 7: Verify the demo still passes with the new dependency present but unused**

Run: `cd <repo> && uv run python -c "import crispy_tabler; print(crispy_tabler.__file__)"` then `uv run python manage.py test`
Expected: the path points at `../crispy-tabler/src/crispy_tabler/__init__.py`; 68 tests OK.

- [ ] **Step 8: Commit both repositories**

```bash
cd ../crispy-tabler && git add -A && git commit -m "feat: package skeleton, Django app and vendoring provenance"
cd <repo> && git add pyproject.toml uv.lock && git commit -m "Demo: install crispy-tabler as an editable path dependency"
```

---

### Task 2: Vendor the 42 templates, self-containment enforced by tests

**Files:**
- Create: `crispy-tabler/src/crispy_tabler/templates/crispy_tabler/**` (42 files)
- Create: `crispy-tabler/tests/test_pack_parity.py`

**Interfaces:**
- Consumes: `crispy_tabler.vendored.CRISPY_BOOTSTRAP5_VERSION` (Task 1)
- Produces: the template directory every later task edits

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_pack_parity.py
def bs5_names() -> set[str]:  # relative paths under crispy_bootstrap5/templates/bootstrap5
def pack_names() -> set[str]:  # same, under crispy_tabler/templates/crispy_tabler, excluding widget/

def test_every_bootstrap5_template_has_a_counterpart():
    assert bs5_names() - pack_names() == set()

def test_the_pack_adds_nothing_unexpected():
    assert pack_names() - bs5_names() == set()

def test_no_template_references_the_bootstrap5_pack():
    offenders = [p for p in pack_files() if "bootstrap5" in p.read_text()]
    assert offenders == []

def test_every_template_records_its_provenance():
    for p in pack_files():
        assert CRISPY_BOOTSTRAP5_VERSION in p.read_text()
```

- [ ] **Step 2: Run them and watch them fail**

Run: `uv run --extra test pytest tests/test_pack_parity.py -v`
Expected: all four fail — the template directory does not exist.

- [ ] **Step 3: Vendor the templates**

Copy the 42 files preserving the `layout/` subdirectory. Apply exactly two mechanical changes to every file and nothing else: replace the `bootstrap5/` prefix in include paths with `crispy_tabler/`, and prepend one Django comment line recording source and version, e.g. `{# vendored from crispy-bootstrap5 2026.9: bootstrap5/field.html #}`. Script it rather than editing by hand, so a re-vendor is repeatable.

- [ ] **Step 4: Run the tests and watch them pass**

Run: same command. Expected: 4 passed.

- [ ] **Step 5: Add a rendering smoke test over the whole pack**

```python
# tests/forms.py — a form with one field per render path, mirroring catalog's ProductForm
# tests/test_pack_parity.py
def test_a_form_renders_through_the_pack_without_touching_bootstrap5(settings):
    settings.INSTALLED_APPS = [a for a in settings.INSTALLED_APPS if a != "crispy_bootstrap5"]
    html = render_crispy_form(CoverageForm())
    assert "form-control" in html
```

Removing `crispy_bootstrap5` from `INSTALLED_APPS` makes any surviving `bootstrap5/` include raise `TemplateDoesNotExist`, which is the point of the test. `CoverageForm` carries: char, textarea, select, multi-select, checkbox, radio group, checkbox group, file, email, url, number, date, time.

- [ ] **Step 6: Run it, fix any include the rewrite missed, commit**

Run: `uv run --extra test pytest -v`

```bash
git add -A && git commit -m "feat: vendor the crispy-bootstrap5 2026.9 pack as crispy_tabler"
```

---

### Task 3: `field.html` — range, colour, and the shrunken group label

**Files:**
- Create: `crispy-tabler/src/crispy_tabler/templatetags/__init__.py`, `templatetags/crispy_tabler_field.py`
- Modify: `crispy-tabler/src/crispy_tabler/templates/crispy_tabler/field.html`
- Create: `crispy-tabler/tests/test_field_template.py`

**Interfaces:**
- Produces: template filters `is_range(field) -> bool`, `is_color(field) -> bool` in library `crispy_tabler_field`

- [ ] **Step 1: Write the failing tests**

```python
def test_range_input_gets_form_range_not_form_control():
    html = render_field(forms.IntegerField(widget=forms.NumberInput(attrs={"type": "range"})))
    assert "form-range" in html and "form-control" not in html

def test_color_input_gets_form_control_color():
    html = render_field(forms.CharField(widget=forms.TextInput(attrs={"type": "color"})))
    assert "form-control-color" in html and 'class="textinput form-control"' not in html

def test_range_and_color_carry_is_invalid_when_the_field_has_errors():   # Review Focus 1
    for html in (bound_with_error("rating"), bound_with_error("accent_color")):
        assert "is-invalid" in html

def test_a_radio_group_legend_is_a_plain_form_label():                    # finding 6
    html = render_field(forms.ChoiceField(choices=[("a", "A")], widget=forms.RadioSelect))
    assert "fs-6" not in html and "form-label" in html

def test_a_hidden_field_renders_bare():                                   # Review Focus 2
    html = render_field(forms.CharField(widget=forms.HiddenInput()))
    assert "<label" not in html and "mb-3" not in html

def test_a_file_field_renders_its_help_text_once():                       # Review Focus 4
    html = render_field(forms.FileField(help_text="Max 2 MB"))
    assert html.count("Max 2 MB") == 1

def test_a_checkbox_in_a_table_cell_has_no_wrapper_div():                 # Review Focus 5
    html = render_field(forms.BooleanField(), tag="td")
    assert html.count("<div") == 0
```

`render_field` builds a one-field form and renders it through the pack; `bound_with_error` binds invalid data to force `field.errors`. **Put these in `tests/helpers.py`** — Tasks 4, 5 and 6 reuse them, and add `render_layout(*layout_objects)` and `render_horizontal(*layout_objects)` (the latter with `helper.form_class = "form-horizontal"`, `label_class = "col-sm-3"`, `field_class = "col-sm-9"`) to the same module.

- [ ] **Step 2: Run them and watch the first four fail**

Run: `uv run --extra test pytest tests/test_field_template.py -v`
Expected: the range, colour, is-invalid and legend tests fail; the hidden, file and `td` tests pass already (they guard behaviour the vendored template has and must keep).

- [ ] **Step 3: Implement the filters in `templatetags/crispy_tabler_field.py`**

Register `is_range(field)` and `is_color(field)`, each reading `field.field.widget.attrs.get("type")` **first** and falling back to `widget.input_type`. This ordering is required: the demo asks for a slider with `NumberInput(attrs={"type": "range"})`, whose `input_type` is `"number"`, and for a picker with `TextInput(attrs={"type": "color"})`, whose `input_type` is `"text"`.

- [ ] **Step 4: Edit `field.html`**

`{% load crispy_tabler_field %}` next to the existing `{% load crispy_forms_field %}`. Add `is_range` and `is_color` branches to the control chain **before** the `form-control` fall-through, each with an `is-invalid` variant mirroring the existing `is_select` branch. In the label block, drop ` fs-6` from the `use_fieldset` legend class. Change nothing else.

- [ ] **Step 5: Run the tests and watch them all pass**

Run: same command. Expected: 7 passed.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat: form-range, form-control-color and full-size group labels in field.html"
```

---

### Task 4: `uneditable_input.html`, `formactions.html`, `fieldset.html`

**Files:**
- Modify: those three templates
- Create: `crispy-tabler/tests/test_layout_templates.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_uneditable_field_is_a_plaintext_control():          # finding 1
    html = render_layout(UneditableField("sku"))
    assert "form-control-plaintext" in html and "uneditable-input" not in html

def test_uneditable_field_label_is_a_form_label():
    assert "form-label" in render_layout(UneditableField("sku"))

def test_form_actions_get_the_tabler_footer():               # finding 5
    html = render_layout(FormActions(Submit("save", "Save")))
    assert "form-footer" in html

def test_fieldset_gets_the_tabler_class_by_default():        # finding 4
    assert "form-fieldset" in render_layout(Fieldset("Internal", "notes"))

def test_an_explicit_css_class_still_wins_on_fieldset():
    html = render_layout(Fieldset("Internal", "notes", css_class="custom"))
    assert "custom" in html

def test_a_horizontal_form_keeps_its_label_columns():        # Review Focus 3
    html = render_horizontal(UneditableField("sku"))
    assert "col-form-label" in html
```

- [ ] **Step 2: Run them and watch the first four fail**

Run: `uv run --extra test pytest tests/test_layout_templates.py -v`
Expected: the four finding tests fail; `test_an_explicit_css_class_still_wins_on_fieldset` and the horizontal-form test pass already, guarding behaviour the vendored templates have and must keep.

- [ ] **Step 3: Edit the three templates**

`uneditable_input.html`: `form-control-plaintext` replaces `uneditable-input`, and the label gains `form-label` (the Bootstrap version omits it), keeping the existing `form-horizontal` branch intact. `formactions.html`: `form-footer` replaces `mb-3`. `fieldset.html`: `form-fieldset` as the default class, with `fieldset.css_class` still appended.

- [ ] **Step 4: Run the tests and watch them pass**

Run: same command. Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: plaintext controls, a Tabler form footer and form-fieldset"
```

---

### Task 5: `layout.py` — the two objects that escape the pack

**Files:**
- Create: `crispy-tabler/src/crispy_tabler/layout.py`, `tests/test_layout_objects.py`

**Interfaces:**
- Produces: `crispy_tabler.layout.FloatingField`, `crispy_tabler.layout.Switch`

- [ ] **Step 1: Write the failing tests**

```python
def test_floating_field_and_switch_templates_follow_the_pack():
    assert FloatingField.template == "%s/layout/floating_field.html"
    assert Switch.template == "%s/layout/switch.html"

def test_they_render_with_crispy_bootstrap5_absent(settings):
    settings.INSTALLED_APPS = [a for a in settings.INSTALLED_APPS if a != "crispy_bootstrap5"]
    html = render_layout(FloatingField("email"), Switch("featured"))
    assert "form-floating" in html and "form-switch" in html
```

The second test is the whole point: crispy-bootstrap5's versions hardcode `"bootstrap5/layout/…"`, and `LayoutObject.get_template_name` substitutes the pack only when the string contains `%s`, so theirs would raise `TemplateDoesNotExist` here.

- [ ] **Step 2: Run them and watch them fail**

Run: `uv run --extra test pytest tests/test_layout_objects.py -v`
Expected: the first fails on the inherited `"bootstrap5/layout/…"` value, the second with `TemplateDoesNotExist`.

- [ ] **Step 3: Implement**

Subclass crispy-bootstrap5's `FloatingField` and `Switch`, overriding `template` with the `%s`-relative string. Nothing else changes; the rendering lives in the vendored templates.

- [ ] **Step 4: Run the tests and watch them pass**

Run: same command. Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: pack-relative FloatingField and Switch"
```

---

### Task 6: Widgets and fields

**Files:**
- Create: `crispy-tabler/src/crispy_tabler/widgets.py`, `fields.py`
- Create: `crispy-tabler/src/crispy_tabler/templates/crispy_tabler/widget/plaintext.html`
- Create: `crispy-tabler/tests/test_widgets.py`

**Interfaces:**
- Produces: `widgets.PlaintextInput`, `widgets.RangeInput`, `widgets.ColorInput`; `fields.PlaintextField`, `fields.RangeField`, `fields.ColorField`

- [ ] **Step 1: Write the failing tests**

```python
def test_range_and_color_widgets_are_detected_by_the_filters():
    assert is_range(field_with(RangeInput(min=1, max=5)))
    assert is_color(field_with(ColorInput()))

def test_plaintext_widget_renders_the_value_not_an_input():
    html = render_field(forms.CharField(widget=PlaintextInput()), initial="SKU-1")
    assert "form-control-plaintext" in html and "<input" not in html

def test_range_widget_carries_its_bounds():
    html = render_field(forms.IntegerField(widget=RangeInput(min=1, max=5)))
    assert 'min="1"' in html and 'max="5"' in html and "form-range" in html
```

- [ ] **Step 2: Run them and watch them fail**

Run: `uv run --extra test pytest tests/test_widgets.py -v`
Expected: 3 failed — the module does not exist.

- [ ] **Step 3: Implement**

`RangeInput(forms.NumberInput)` and `ColorInput(forms.TextInput)` set `input_type` and accept bounds as keyword arguments, so Task 3's filters match them on `input_type` alone. `PlaintextInput(forms.Widget)` sets `template_name = "crispy_tabler/widget/plaintext.html"` and renders the value inside a `form-control-plaintext` element. `fields.py` binds each widget to a thin `forms.Field` subclass and nothing more.

- [ ] **Step 4: Run the whole package suite, not just this file**

Run: `uv run --extra test pytest -v`
Expected: every test from Tasks 1–6 passes. The new widgets must not change what Task 3's filter tests see.

- [ ] **Step 5: Write the README and CHANGELOG, then commit**

README: what the package is, the install snippet, the three settings, the import swap for `FloatingField` / `Switch`, the six fixes as a table, and the known gap from Task 7. CHANGELOG: `0.1.0`.

```bash
git add -A && git commit -m "feat: plaintext, range and colour widgets with matching fields"
```

---

### Task 7: Switch the demo onto the pack

**Files:**
- Modify: `tabler-test/config/settings.py`, `catalog/views.py`, `catalog/tests.py`, `docs/crispy_tabler_coverage.md`

- [ ] **Step 1: Switch the settings**

`INSTALLED_APPS` gains `"crispy_tabler"`; `CRISPY_TEMPLATE_PACK = 'crispy_tabler'`; `CRISPY_ALLOWED_TEMPLATE_PACKS = ('crispy_tabler', 'bootstrap5')`. `crispy_bootstrap5` **stays** in `INSTALLED_APPS`: django-crud-views' own `crud_views/detail/field.html` still includes four `bootstrap5/…` partials, so detail pages need them until that is fixed upstream (Task 8).

- [ ] **Step 2: Swap the two imports in `catalog/views.py`**

`FloatingField` and `Switch` now come from `crispy_tabler.layout` instead of `crispy_bootstrap5.bootstrap5`. No other line changes.

- [ ] **Step 3: Run the demo suite and watch the coverage markers fail**

Run: `cd <repo> && uv run python manage.py test catalog -v 1`
Expected: failures in `test_input_group_floating_and_uneditable_paths` — it asserts `uneditable-input`, which the new pack deliberately no longer emits.

- [ ] **Step 4: Update `catalog/tests.py` to assert the fixed markup**

Replace the `uneditable-input` assertion with `form-control-plaintext`; add assertions for `form-range`, `form-control-color`, `form-footer`, `form-fieldset`, and that `fs-6` no longer appears. The coverage table in `docs/crispy_tabler_coverage.md` says which field covers which path; keep one marker per path.

- [ ] **Step 5: Add the guard test for the remaining gap**

```python
# catalog/tests.py
def test_create_and_update_pages_use_no_bootstrap5_template(self):
    # detail pages are excluded: crud_views/detail/field.html hardcodes four bootstrap5 includes
```

Assert by rendering with `crispy_bootstrap5` removed from `INSTALLED_APPS` via `override_settings`, and mark it `skipUnless` the upstream fix is present, with the reason naming the upstream issue from Task 8. The spec requires this to ship as a skipped test with its reason recorded, not to be dropped.

- [ ] **Step 6: Run the whole suite**

Run: `uv run python manage.py test` and `uv run python manage.py check`
Expected: all tests pass (68 plus the new ones), no check issues.

- [ ] **Step 7: Verify in the browser**

Load `/product/create/`. Confirm: the rating slider has a track, the accent colour is a swatch and not a full-width bar, the SKU reads as plain text, "Internal" is a tinted fieldset, Save/Cancel are separated from the last field, and "Size" / "Channels" / "Shipping" labels match the other labels in size.

- [ ] **Step 8: Record the result and commit**

Update `docs/crispy_tabler_coverage.md`: each of the six findings marked fixed with the class now emitted, and a new section for the detail-page gap. Update `docs/crud_views_tabler.md` where it names the crispy pack.

```bash
git add -A && git commit -m "Demo: render through the crispy_tabler pack; coverage findings fixed"
```

---

### Task 8: The two upstream issues

**Files:**
- Create: two drafts under the scratchpad, then file after the maintainer approves

- [ ] **Step 1: Draft the crispy-bootstrap5 issue**

`FloatingField.template` and `Switch.template` hardcode `"bootstrap5/layout/…"` while every other layout object in crispy-forms is `%s`-relative, so they ignore `CRISPY_TEMPLATE_PACK`. Include the `get_template_name` excerpt, the two class definitions, and the one-line fix.

- [ ] **Step 2: Draft the django-crud-views issue**

`src/crud_views/templates/crud_views/detail/field.html` includes `bootstrap5/…` at lines 22, 35, 39 and 58, so a project on another crispy pack gets Bootstrap partials on detail pages only. Include the four line numbers, the symptom, and acceptance criteria.

- [ ] **Step 3: Show both drafts to the maintainer and file only on their explicit go-ahead**

Filing a public issue is an outward-facing action; it does not happen without a clear yes.

- [ ] **Step 4: Record the issue numbers**

Add them to `docs/crispy_tabler_coverage.md`, to the skip reason in Task 7's guard test, and to `docs/crud_views_upstream_status.md` alongside #208–#211.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "Docs: upstream issues for the pack-relative template gaps"
```
