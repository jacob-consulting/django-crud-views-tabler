# Crispy render-path coverage: the `catalog` demo app

The `catalog` app exists to make one page — `/product/create/` — render **every branch of the crispy
template pack at once**, so the Tabler theme can be judged field by field instead of guessing. It is the
groundwork for the `crispy_tabler` template pack, which now exists as the sibling package `../crispy-tabler`
and which the demo renders through (`CRISPY_TEMPLATE_PACK = "crispy_tabler"`).

The findings below were recorded on 2026-10-21 against crispy-bootstrap5 2026.9 (`CRISPY_TEMPLATE_PACK = "bootstrap5"`) and
are now fixed by `crispy_tabler`; the third column of the table shows the state before the switch. Checked against
Tabler 1.6.1 and django-crud-views main.

```
uv run python manage.py seed_demo_catalog     # 40 products, 5 categories, 6 tags, 4 channels
uv run python manage.py test catalog          # pins the coverage below
```

`catalog/tests.py` asserts one marker per render path, now against the fixed markup. If a field is removed from
`ProductForm.get_layout_fields` the matching test fails, so the coverage cannot rot silently.

## What each field is for

| Form field | Layout object / widget | crispy template | Under Tabler (before the switch) |
|---|---|---|---|
| `name` | plain | `field.html`, text | ok |
| `slug` | `help_text` | `layout/help_text.html` → `form-text` | ok — Tabler styles `.form-text` as well as its own `.form-hint` |
| `description` | plain | `field.html`, textarea | ok |
| `sku` | `UneditableField` | `layout/uneditable_input.html` | **broken**, now fixed (below) |
| `category` | FK | `field.html`, `is_select` → `form-select` | ok |
| `tags` | M2M `SelectMultiple` | `field.html`, `is_select` | ok |
| `channels` | M2M `CheckboxSelectMultiple` | `layout/radio_checkbox_select.html` | ok |
| `size` | choices `RadioSelect` | `layout/radio_checkbox_select.html` | ok |
| `shipping` | `InlineRadios` + `RadioSelect` | `layout/radioselect_inline.html` | ok |
| `price` | `PrependedText("€")` | `layout/prepended_appended_text.html` → `input-group` | ok |
| `warranty_months` | `AppendedText("months")` | same | ok |
| `stock` | plain | `field.html`, number | ok |
| `rating` | `type="range"` | `field.html`, fall-through | **wrong class**, now fixed (below) |
| `released_on` / `published_at` / `restock_at` | native `date` / `datetime-local` / `time` | `field.html` | ok |
| `is_active` | Boolean | `field.html`, `is_checkbox` → `form-check` | ok |
| `is_featured` | `Switch` | `layout/switch.html` → `form-switch` | ok |
| `accent_color` | `type="color"` | `field.html`, fall-through | **wrong class**, now fixed (below) |
| `contact_email` | `FloatingField` | `layout/floating_field.html` → `form-floating` | ok |
| `website` | URL | `field.html` | ok |
| `datasheet` | `FileField` | `layout/field_file.html` | ok |
| `internal_notes` | inside `Fieldset` | `layout/fieldset.html` | **plain `<fieldset>`**, now fixed (below) |
| Save / Cancel | `FormActions` | `layout/formactions.html` → `mb-3` | **no `form-footer`**, now fixed (below) |

The **filter form** (`ProductFilter`) covers what a ModelForm cannot reach: `BooleanFilter` renders a
`NullBooleanSelect` ("Unknown / Yes / No"), two `NumberFilter`s make the price pair, and
`InlineCheckboxes("tags")` renders `layout/checkboxselectmultiple_inline.html`.

## What was wrong under Tabler, and what `crispy_tabler` emits now

Six findings, all seen in the browser on `/product/create/`. **All six are fixed** by the pack and pinned in
`catalog/tests.py`.

1. **`UneditableField` had no Tabler equivalent.** Bootstrap's template emitted `class="uneditable-input textinput"`
   (a Bootstrap 2 class) and no `form-control`. **Fixed:** now `form-control-plaintext`, and `uneditable-input` is
   absent. crispy's own `UneditableField` hardcodes the dead class in Python, so the demo imports `UneditableField`
   from `crispy_tabler.layout`, not `crispy_forms.bootstrap`.
2. **`type="range"` got `form-control`.** **Fixed:** now `form-range` **alone**. Tabler's `.form-range` resets
   `appearance` and `background-color`, which `form-control` would fight.
3. **`type="color"` got `form-control`.** **Fixed:** now `form-control form-control-color`, **both**. Unlike range,
   Tabler's `.form-control-color` sets only width/height/padding and relies on `.form-control` for border and
   radius. Do not "simplify" this into one class to match the range fix.
4. **`Fieldset` rendered a bare `<fieldset><legend>`.** **Fixed:** now `form-fieldset`; a caller's `css_class` is
   kept alongside it.
5. **`FormActions` had no footer spacing.** **Fixed:** now `form-footer`.
6. **Django's `use_fieldset` labels shrank** (`fs-6 form-label`). **Fixed:** plain `form-label` everywhere. The fix
   spans **three** templates in `crispy_tabler`: `field.html` ("Size", "Channels") plus
   `layout/radioselect_inline.html` ("Shipping") and `layout/checkboxselectmultiple_inline.html` (the filter's
   "Tags"). The two inline ones were missed at first and caught by this demo; `fs-6` now appears nowhere on
   `/product/create/`.

## Known gap: detail pages still need `crispy_bootstrap5`

`crispy_bootstrap5` stays in `INSTALLED_APPS`. django-crud-views' `crud_views/detail/field.html` hardcodes four
`bootstrap5/...` includes, so the **detail** page renders Bootstrap-pack partials regardless of
`CRISPY_TEMPLATE_PACK`. Create, update and delete pages do not. Fixing it in the Tabler theme app is an explicit
non-goal; it belongs upstream in django-crud-views (issue not yet filed; its number goes here).
`test_form_and_detail_pages_use_no_bootstrap5_template` guards the other side: it renders the create, update and
**detail** pages with the `bootstrap5/` templates unavailable (a loader refuses any `bootstrap5/` name), and is **skipped** while `crud_views/detail/field.html` still
hardcodes them (the skip condition reads the template source, so it un-skips itself once upstream is fixed).
Because the detail page is in its URL list, un-skipping proves that very fix: it passes only if detail pages
render without any Bootstrap-pack template.

Two things are **not** deltas, although the earlier guess was that they would be:

- **Help text.** crispy emits `form-text`; Tabler styles `.form-text` alongside its own `.form-hint`, so it
  already looks right.
- **The required marker.** crispy emits `<span class="asteriskField">*</span>` where Tabler styles
  `.form-label.required::after`. The theme already bridges this in
  `crud_views_tabler/static/crud_views_tabler/crud_views_tabler.css`.

## Tabler widgets crispy cannot reach at all

`form-selectgroup` (button-style single/multi select), `form-imagecheck` (image tiles) and `form-colorinput`
(colour swatch radios) have no stock crispy layout object. They are candidates for new layout objects in
`crispy_tabler` rather than demo fields, so this app does not use them.

## A gotcha worth remembering

`InlineRadios("shipping")` only swaps the *template*. Without `widget=forms.RadioSelect` on the field, the
widget stays a `Select` and `radioselect_inline.html` renders `<input type="select">` — invalid HTML that the
browser paints as small boxes showing the raw choice values. `catalog/tests.py` asserts `type="select"` never
appears.
