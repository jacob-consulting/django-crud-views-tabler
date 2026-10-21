# crispy_tabler: a Tabler template pack for django-crispy-forms

Date: 2026-10-21
Status: design, discussed with the maintainer; builder check pending

## Intent

There is no crispy-forms template pack for Tabler. `crispy-tabler` is a 404 on PyPI and no GitHub repository
carries the name, so every Tabler project on django-crispy-forms today runs the Bootstrap 5 pack and lives with
whatever it gets. This project is one of them: `CRISPY_TEMPLATE_PACK = "bootstrap5"` with Tabler 1.6.1.

What that costs is measured, not guessed. The `catalog` demo app in this repository renders every branch of the
crispy template pack on one page (`/product/create/`), and
[`docs/crispy_tabler_coverage.md`](../../crispy_tabler_coverage.md) records the result field by field. **Most of
Tabler's form vocabulary is Bootstrap's** — `form-label`, `form-control`, `form-select`, `form-check`,
`form-switch`, `input-group`, `form-text`, `is-invalid` are all styled — so the Bootstrap 5 pack is right far more
often than it is wrong. Six things are wrong:

1. `UneditableField` emits `class="uneditable-input textinput"` — a Bootstrap **2** class — and no `form-control`
   at all. Tabler's class for a read-only value is `form-control-plaintext`.
2. `<input type="range">` falls through `field.html` to `form-control`: a slider inside a bordered box with no
   track. Tabler wants `form-range`.
3. `<input type="color">` falls through the same way: the picker stretches to the full column width as a solid
   bar. Tabler wants `form-control-color`.
4. `Fieldset` renders a bare `<fieldset><legend>`; Tabler has `.form-fieldset`.
5. `FormActions` renders `class="mb-3"`; Tabler separates a form's actions with `.form-footer` (`margin-top: 2rem`).
   Save and Cancel currently sit tight under the last field, and there is no CSS hook to fix it from outside.
6. Django's `use_fieldset` path renders a field's label as `<legend class="fs-6 form-label">`, so the labels of
   radio and checkbox groups ("Size", "Channels", "Shipping", and the filter's "Tags") read visibly smaller and
   lighter than every other label on the page.

Two things that looked broken are **not**: help text (crispy emits `form-text`, which Tabler styles alongside its
own `form-hint`) and the required marker (crispy emits `<span class="asteriskField">*</span>`, which the theme
already bridges to Tabler's `.form-label.required` in
`crud_views_tabler/static/crud_views_tabler/crud_views_tabler.css`).

The intent is to stop patching around the Bootstrap pack and **ship a Tabler pack that emits the right class in
the first place** — the difference between a theme and a shim.

## Decisions the maintainer made

These are given, not open:

- **Its own sibling repository**, installed into this demo as an editable path dependency, exactly the way
  `django-crud-views` is installed today (`[tool.uv.sources]`, `editable = true`).
- **Architecture modelled on an internal reference package the maintainer owns.** Its shape: one Django app whose
  name *is* the crispy template pack (`CRISPY_TEMPLATE_PACK = "<app>"`), 70 templates in the app's own template
  directory — the complete standard set plus its own additions — with **zero** references to the `bootstrap5/`
  pack anywhere inside them and 63 internal ones, next to roughly 1,550 lines of its own widgets, fields, layout
  objects and forms. Widgets carry their own `template_name`.
- **Copy-all, not a hybrid.** An earlier proposal to vendor only the templates carrying a delta and make the rest
  one-line `{% include "bootstrap5/…" %}` was rejected in favour of self-containment.
- **`crud_views_tabler` stays in this repository.** The new package is independent of django-crud-views and must
  not import it.
- **Public on PyPI**, MIT, English, with the metadata and README of a package strangers are meant to install.

## Why copy-all is the only self-contained option

Recorded because it is the question a reader will ask first:

- **There are no blocks to extend.** `grep -rc "{% block"` over all 42 crispy-bootstrap5 templates returns zero.
  Not one template defines a block, so `{% extends %}` can only replace a file wholesale. Template inheritance is
  not available here in any useful form.
- **Include-delegation leaks.** The templates contain 38 hardcoded `bootstrap5/…` include paths. A
  `crispy_tabler/field.html` that included `bootstrap5/field.html` would pull in `bootstrap5/layout/help_text.html`,
  `radio_checkbox_select.html` and `field_errors_block.html`; the pack's own versions of those would never load.
- **Its own components need siblings.** Once the pack ships layout objects of its own, their templates include the
  shared partials (help text, field errors, the required marker). Those partials must be in the same pack.

## Current state

- Demo repository `/home/alex/projects/alex/tabler-test`, branch `demo/catalog-form-coverage` @ `279832a`:
  `crud_views_tabler` (theme app), `customers` and `catalog` (demo apps), 68 tests passing.
- `config/settings.py`: `crispy_forms`, `crispy_bootstrap5` in `INSTALLED_APPS`;
  `CRISPY_TEMPLATE_PACK = 'bootstrap5'`, `CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'`.
- crispy-bootstrap5 2026.9, django-crispy-forms ≥ 2.4, Tabler 1.6.1 from the CDN.
- **django-crud-views never names a template pack.** Every call site is `{% crispy form form.helper %}` or
  `{% crispy filter.form filter.form.helper %}` with no pack argument, and nothing in `src/crud_views/lib/` passes
  `template_pack`. One setting therefore switches the whole project, and no second pack has to stay allowed.

## Goals

The first version ships a pack that is a drop-in replacement for `bootstrap5` on a Tabler page, with the six
findings fixed.

1. **The package.** A new repository at `/home/alex/projects/alex/crispy-tabler`: distribution `crispy-tabler`,
   one Django app `crispy_tabler`, `src/` layout, `pyproject.toml`, MIT `LICENSE`, `README.md`, its own test suite.
2. **The pack.** All 42 template names from crispy-bootstrap5, vendored under
   `src/crispy_tabler/templates/crispy_tabler/`, with every internal include path rewritten to the new pack. No
   `bootstrap5/` string survives anywhere in the template directory.
3. **The six fixes**, in the vendored templates and the new widgets (see *Design*).
4. **Own widgets** with their own `template_name`, in the shape the reference package uses, for the cases where
   Django's default widget cannot carry Tabler's markup.
5. **A parity test** that walks the installed `crispy_bootstrap5` template directory and asserts the pack has a
   file of the same name for every one of them, plus a recorded note of the crispy-bootstrap5 version each
   template was vendored from. This is the drift detector that upstream issue #211 asks for, built in from day one.
6. **Wired into this demo**: editable path dependency, `crispy_tabler` in `INSTALLED_APPS`,
   `CRISPY_TEMPLATE_PACK = 'crispy_tabler'`, the `catalog` and `customers` forms rendering through it unchanged,
   and `docs/crispy_tabler_coverage.md` updated to record what the new pack fixes.

## Non-goals

- Tabler's own form components that have no crispy equivalent — `form-selectgroup`, `form-imagecheck`,
  `form-colorinput`. They are the obvious wave 2 and the pack should leave room for them, but they are not in this
  version.
- Any JavaScript. The pack is templates, widgets and fields.
- Moving, changing or depending on `crud_views_tabler`.
- Dropping crispy-bootstrap5 as a dependency. It stays, for its **Python** layout objects (`FloatingField`,
  `Switch`, `BS5Accordion`) and as the source of truth the parity test compares against — never as a template
  fallback.
- Replacing the theme's existing CSS bridges (for example `.asteriskField`). Where the pack now emits a correct
  class, the corresponding bridge can go, but auditing the theme's stylesheet is not part of this.
- i18n of the package's own strings.

## Anti-goals

Things that would mean the design was not followed, even if the result looked right:

- Any `bootstrap5/` path inside `src/crispy_tabler/templates/`. Self-containment *is* the architecture; a test
  asserts this.
- A CSS file in the package that re-styles a class the pack itself emitted wrongly. Overriding a wrong class is
  what this package exists to stop; styling belongs to Tabler and to the theme.
- Importing `crud_views`, or any dependency on django-crud-views.
- Forking or vendoring crispy-forms **Python** code.
- Vendored templates drifting silently: every file keeps its provenance and the parity test keeps the file list
  honest.

## Constraints

- Python ≥ 3.12; Django 4.2, 5.2 and 6.x, matching django-crud-views' own support matrix.
- django-crispy-forms ≥ 2.4, crispy-bootstrap5 pinned to a lower bound that the vendored templates were taken
  from, and recorded as such.
- Tabler 1.6.1's class vocabulary. The checkout at `/home/alex/projects/alex/tabler/tabler-1.6.1` is the
  reference: `dashboard/form-elements.html` and `dashboard/form-layout.html` for markup, `dashboard/dist/css/tabler.css`
  for which classes exist.
- The demo repository stays the proving ground: `/product/create/` is the acceptance surface and `catalog/tests.py`
  the regression net. Its assertions are written against the *bootstrap5* pack today and will need updating as part
  of the switch — that is expected, and the coverage table says which marker belongs to which render path.

## Design

### Repository shape

```
crispy-tabler/
  pyproject.toml          # setuptools backend, src layout, MIT, PyPI classifiers
  README.md  LICENSE  CHANGELOG.md
  src/crispy_tabler/
    __init__.py  apps.py
    widgets.py            # Django widgets with their own template_name
    fields.py             # form fields that bind those widgets
    layout.py             # crispy layout objects (wave 2 grows here)
    templatetags/crispy_tabler_field.py
    templates/crispy_tabler/
      field.html  uni_form.html  errors.html  …          # the 42 vendored names
      layout/…                                            # vendored layout templates
      widget/…                                            # templates for the package's own widgets
  tests/
```

The app is listed in `INSTALLED_APPS` only so Django's app template loader finds
`templates/crispy_tabler/`; it has no models, no URLs and no `ready()` side effects.

### The template pack

Vendored verbatim from crispy-bootstrap5, with exactly two mechanical changes applied to every file: the
`bootstrap5/` prefix in include paths becomes `crispy_tabler/`, and a provenance header records the source version.
Beyond that, only the files below change. **A vendored template nobody needed to change must be byte-identical to
its source apart from those two things** — that is what makes the next re-diff cheap.

### The six fixes

| # | Finding | Where it is fixed | How |
|---|---|---|---|
| 1 | `uneditable-input`, no `form-control` | `layout/uneditable_input.html` | `form-control-plaintext`; the label gains `form-label`, which the Bootstrap version also omits |
| 2 | `type="range"` → `form-control` | `field.html` + templatetag | a new `is_range` filter and a branch that applies `form-range` |
| 3 | `type="color"` → `form-control` | `field.html` + templatetag | a new `is_color` filter and a branch that applies `form-control-color` |
| 4 | bare `<fieldset>` | `layout/fieldset.html` | `form-fieldset` as the default class, still overridable by the layout object's `css_class` |
| 5 | `FormActions` has `mb-3` | `layout/formactions.html` | `form-footer` |
| 6 | `use_fieldset` legend is `fs-6` | `field.html` | the legend gets the same `form-label` treatment as a normal label, without `fs-6` |

**Findings 2 and 3 are fixed in `field.html`, not in a widget — this is the one thing a builder is most likely to
get backwards.** crispy's `field.html` decides the control class itself: it distinguishes file, select and
checkbox, and sends everything else to `form-control` via `{% crispy_field field 'class' 'form-control' %}`. A
widget that sets `form-range` on itself would therefore end up with *both* classes. crispy's own filters live in
`crispy_forms.templatetags.crispy_forms_field` and cover only `is_checkbox`, `is_password`, `is_radioselect`,
`is_select`, `is_checkboxselectmultiple`, `is_file`, `is_clearable_file` and `is_multivalue` — there is nothing for
range or colour. So the pack ships its own templatetag library with `is_range` and `is_color`, and `field.html`
loads it alongside `crispy_forms_field` and branches before the `form-control` fall-through.

**Those filters must read `widget.attrs.get("type")` first and only then fall back to `widget.input_type`.** The
obvious implementation — `input_type` alone — detects neither of the demo's own fields: `catalog/views.py` asks for
a slider with `forms.NumberInput(attrs={"type": "range"})`, whose `input_type` is `"number"`, and for a colour
picker with `forms.TextInput(attrs={"type": "color"})`, whose `input_type` is `"text"`. Getting this wrong makes
findings 2 and 3 verify as unfixed on the acceptance page. Reading the attribute first also means a plain Django
widget with a `type` override is fixed without anyone adopting a new widget class.

### The widgets

`widgets.py` is then for markup Django's defaults cannot produce, not for class fixes. Wave 1 ships the small set
the findings justify, each with its own `template_name = "crispy_tabler/widget/<name>.html"`:

- a plaintext/read-only display widget, so a read-only value can be rendered as `form-control-plaintext` without
  going through `UneditableField`;
- range and colour inputs that set the right `input_type` and sensible attributes, as the ergonomic way to ask for
  what finding 2 and 3 fix (the `field.html` branches remain the safety net for projects that do not use them).

`fields.py` binds those widgets to form fields. The module exists in wave 1 mainly so that wave 2's Tabler-only
components have an established home; it should not grow speculative API.

### Settings, in the demo and in the README

```python
INSTALLED_APPS = [..., "crispy_forms", "crispy_bootstrap5", "crispy_tabler", ...]
CRISPY_ALLOWED_TEMPLATE_PACKS = "crispy_tabler"
CRISPY_TEMPLATE_PACK = "crispy_tabler"
```

`crispy_bootstrap5` stays installed for its Python layout objects. Because no crud_views call site names a pack,
nothing else has to change.

### Install into the demo

```toml
[tool.uv.sources]
django-crud-views = { path = "../django-crud-views", editable = true }
crispy-tabler = { path = "../crispy-tabler", editable = true }
```

### Testing

The package's own suite (pytest + a minimal settings module, the way both sibling packages do it) covers: the
parity test against the installed crispy-bootstrap5 file list; an anti-goal test that no `bootstrap5/` string
appears under the template directory; and a rendering test per fixed finding, asserting the emitted class.

The demo keeps its own net: `catalog/tests.py` already pins one marker per crispy render path, so switching the
pack and updating those markers *is* the acceptance test for "nothing else moved".

## Verification

1. `uv run python manage.py test` in the demo passes with `CRISPY_TEMPLATE_PACK = 'crispy_tabler'`.
2. `/product/create/` rendered in a browser: slider with a track, a colour swatch, the SKU as plaintext, a tinted
   fieldset, a separated action footer, and radio/checkbox group labels the same size as every other label.
3. `docs/crispy_tabler_coverage.md` updated: each of the six findings marked fixed, with the class now emitted.
4. No `bootstrap5/` string under `src/crispy_tabler/templates/`.
5. The parity test fails if a template name is added to crispy-bootstrap5 and not to the pack.

## Left to the builder

- The exact provenance mechanism (a header comment per file, a single `VENDORED.md`, or both) — as long as the
  crispy-bootstrap5 version is recorded and the parity test reads it.
- Test framework details in the new repository (pytest layout, a nox file or not, CI or not for the first version).
- Whether `layout.py` ships anything at all in wave 1 or is created empty with a docstring.
- Naming of the widget classes and their template files.
- Whether the theme's `.asteriskField` CSS bridge is left alone (default) or the pack emits Tabler's
  `form-label required` instead — the second is tempting, but it changes markup the theme currently depends on, so
  it needs its own decision rather than being folded in here.
