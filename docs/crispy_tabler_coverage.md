# Crispy render-path coverage: the `catalog` demo app

The `catalog` app exists to make one page — `/product/create/` — render **every branch of the crispy
template pack at once**, so the Tabler theme can be judged field by field instead of guessing. It is the
groundwork for a `crispy_tabler` template pack (no such package exists: `crispy-tabler` is 404 on PyPI and
there is no GitHub repository under that name).

Checked on 2026-10-21 against crispy-bootstrap5 2026.9 (`CRISPY_TEMPLATE_PACK = "bootstrap5"`, unchanged),
Tabler 1.6.1 and django-crud-views main.

```
uv run python manage.py seed_demo_catalog     # 40 products, 5 categories, 6 tags, 4 channels
uv run python manage.py test catalog          # pins the coverage below
```

`catalog/tests.py` asserts one marker per render path. If a field is removed from `ProductForm.get_layout_fields`
the matching test fails, so the coverage cannot rot silently.

## What each field is for

| Form field | Layout object / widget | crispy template | Under Tabler |
|---|---|---|---|
| `name` | plain | `field.html`, text | ok |
| `slug` | `help_text` | `layout/help_text.html` → `form-text` | ok — Tabler styles `.form-text` as well as its own `.form-hint` |
| `description` | plain | `field.html`, textarea | ok |
| `sku` | `UneditableField` | `layout/uneditable_input.html` | **broken** (below) |
| `category` | FK | `field.html`, `is_select` → `form-select` | ok |
| `tags` | M2M `SelectMultiple` | `field.html`, `is_select` | ok |
| `channels` | M2M `CheckboxSelectMultiple` | `layout/radio_checkbox_select.html` | ok |
| `size` | choices `RadioSelect` | `layout/radio_checkbox_select.html` | ok |
| `shipping` | `InlineRadios` + `RadioSelect` | `layout/radioselect_inline.html` | ok |
| `price` | `PrependedText("€")` | `layout/prepended_appended_text.html` → `input-group` | ok |
| `warranty_months` | `AppendedText("months")` | same | ok |
| `stock` | plain | `field.html`, number | ok |
| `rating` | `type="range"` | `field.html`, fall-through | **wrong class** (below) |
| `released_on` / `published_at` / `restock_at` | native `date` / `datetime-local` / `time` | `field.html` | ok |
| `is_active` | Boolean | `field.html`, `is_checkbox` → `form-check` | ok |
| `is_featured` | `Switch` | `layout/switch.html` → `form-switch` | ok |
| `accent_color` | `type="color"` | `field.html`, fall-through | **wrong class** (below) |
| `contact_email` | `FloatingField` | `layout/floating_field.html` → `form-floating` | ok |
| `website` | URL | `field.html` | ok |
| `datasheet` | `FileField` | `layout/field_file.html` | ok |
| `internal_notes` | inside `Fieldset` | `layout/fieldset.html` | **plain `<fieldset>`** (below) |
| Save / Cancel | `FormActions` | `layout/formactions.html` → `mb-3` | **no `form-footer`** (below) |

The **filter form** (`ProductFilter`) covers what a ModelForm cannot reach: `BooleanFilter` renders a
`NullBooleanSelect` ("Unknown / Yes / No"), two `NumberFilter`s make the price pair, and
`InlineCheckboxes("tags")` renders `layout/checkboxselectmultiple_inline.html`.

## What is actually wrong under Tabler

Six findings, all seen in the browser on `/product/create/`:

1. **`UneditableField` has no Tabler equivalent.** `uneditable_input.html` emits
   `class="uneditable-input textinput"` — a Bootstrap 2 class that no longer exists anywhere — and **no**
   `form-control`. The SKU field renders as a grey square-cornered box next to proper inputs. Tabler's class
   for this is `form-control-plaintext`.
2. **`type="range"` gets `form-control`.** `field.html` only distinguishes file / select / checkbox and sends
   everything else to `form-control`, so the slider sits inside a bordered input box with no visible track.
   Tabler wants `form-range`.
3. **`type="color"` gets `form-control`.** Same fall-through: the colour picker stretches to the full column
   width as a solid bar. Tabler wants `form-control-color`.
4. **`Fieldset` renders a bare `<fieldset><legend>`.** Tabler has `.form-fieldset` (a padded, tinted block);
   crispy's template takes `css_class`, so this one a project *can* work around, but the default is wrong.
5. **`FormActions` has no footer spacing.** It renders `class="mb-3"`; Tabler separates a form's actions with
   `.form-footer` (`margin-top: 2rem`). Save and Cancel currently sit tight under the last field.
6. **Django's `use_fieldset` labels shrink.** For `RadioSelect` / `CheckboxSelectMultiple`, `field.html`
   renders the label as `<legend class="fs-6 form-label requiredField">`. Next to the normal `form-label`
   fields, "Size", "Channels", "Shipping" and the filter's "Tags" read noticeably smaller and lighter.

Two things are **not** deltas, although the earlier guess was that they would be:

- **Help text.** crispy emits `form-text`; Tabler styles `.form-text` alongside its own `.form-hint`, so it
  already looks right.
- **The required marker.** crispy emits `<span class="asteriskField">*</span>` where Tabler styles
  `.form-label.required::after`. The theme already bridges this in
  `crud_views_tabler/static/crud_views_tabler/crud_views_tabler.css`.

## Tabler widgets crispy cannot reach at all

`form-selectgroup` (button-style single/multi select), `form-imagecheck` (image tiles) and `form-colorinput`
(colour swatch radios) have no crispy layout object. They are candidates for new layout objects in a
`crispy_tabler` package rather than demo fields, so this app does not use them.

## A gotcha worth remembering

`InlineRadios("shipping")` only swaps the *template*. Without `widget=forms.RadioSelect` on the field, the
widget stays a `Select` and `radioselect_inline.html` renders `<input type="select">` — invalid HTML that the
browser paints as small boxes showing the raw choice values. `catalog/tests.py` asserts `type="select"` never
appears.
