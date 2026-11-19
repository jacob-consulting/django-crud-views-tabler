# Adopt Upstream Navbar Class Keys Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The ViewSet Navigation tabs use Tabler's `nav nav-bordered` through upstream's new `navbar:*` class keys
(#384), the pill-to-tab CSS goes, and findings 36 and 38 are recorded as resolved.

**Architecture:** Two entries in `TABLER_BUTTON_CLASSES` (registered in `CrudViewsTablerConfig.ready()` already);
`page.html` keeps its structure (it already matches upstream's owner-heading recipe); the CSS keeps two rules.

**Tech Stack:** Django 6.1, django-crud-views (editable `../django-crud-views`, branch for #384), Tabler 1.6.1.

**Spec:** `docs/superpowers/specs/2026-11-19-adopt-navbar-class-keys-design.md`

## Global Constraints

- `navbar:nav` = `nav nav-bordered flex-wrap`; `navbar:link` = `nav-link mw-100 text-break gap-2`; no other `navbar:*` key registered.
- No new template override; `../django-crud-views` is read-only.
- Every theme CSS rule change is reflected in `docs/crud_views_upstream_findings_roastery.md` in the same commit (CLAUDE.md).

## Review Focus

- Dark mode: the active tab must stay readable (link colour, not plain primary sienna) — Task 1 CSS test + Task 2 browser check.
- Narrow widths: tabs wrap without horizontal scroll; `nav-bordered` uses `margin-inline-start` between items, so a wrapped row starts indented — Task 2 browser check at ~375px.
- Icon/label spacing: Tabler's `.nav-link` is a flex row; `gap-2` must replace the deleted `gap: .375rem` rule — Task 1 test asserts the class.
- Project override precedence: `CRUD_VIEWS_BUTTON_CLASSES={"navbar:nav": ...}` still wins over the theme — Task 1 test.
- Example navbar test helper regexes on `class="nav-link[^"]*"`; must keep matching — Task 1 Step 4 runs the example suite.

---

### Task 1: Register the navbar keys, trim the CSS, record findings 36 and 38

**Files:**
- Modify: `src/crud_views_tabler/buttons.py` (add two keys next to the `card-order:*` entries, with a comment citing #384 / finding 36)
- Modify: `src/crud_views_tabler/static/crud_views_tabler/crud_views_tabler.css:95-126`
- Modify: `src/crud_views_tabler/templates/crud_views_tabler/page.html` (comments only, lines 6-9)
- Modify: `tests/crud_views_tabler/test_theme.py` (`test_bar_page_builds_the_owner_header` ~line 199, replace `test_object_navbar_pills_look_like_tabs` ~line 819)
- Modify: `docs/crud_views_upstream_findings_roastery.md` (table rows 36, 38; entries at ~1011 and ~1055)
- Modify: `docs/crud_views_tabler.md` (lines ~50, ~58-66: PR #383 merged, class keys, no tab CSS)

**Interfaces:**
- Consumes: upstream `crud_views/tags/navbar_items.html` rendering `{% cv_button_class "navbar" "nav" %}` etc.
- Produces: rendered `<ul class="nav nav-bordered flex-wrap">` and `<a class="nav-link mw-100 text-break gap-2[ active]">`.

- [ ] **Step 1: Write the failing tests** in `tests/crud_views_tabler/test_theme.py`

In `test_bar_page_builds_the_owner_header` add:
```python
self.assertIn('<ul class="nav nav-bordered flex-wrap">', header)
self.assertNotIn("nav-pills", header)
self.assertRegex(header, r'class="nav-link mw-100 text-break gap-2 active" href="[^"]+" aria-current="true"')
```
Add `test_project_setting_overrides_the_navbar_keys` (same class, uses `detail_html`):
```python
with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"navbar:nav": "nav nav-tabs"}):
    html = self.detail_html()
self.assertIn('<ul class="nav nav-tabs">', html)
```
(If the registry caches resolved classes, clear it the way existing override tests in this file do.)

Replace `test_object_navbar_pills_look_like_tabs` with `test_object_navbar_tabs_use_tabler_classes`:
```python
css = (...crud_views_tabler.css).read_text()
self.assertNotIn(".nav-pills", css)
self.assertNotRegex(css, r"\.cv-tabler-navbar \.nav-link \{\s*gap:")
self.assertRegex(css, r"\.cv-tabler-navbar \.nav-link\.active \{[^}]*--tblr-link-color")
self.assertRegex(css, r"\.cv-tabler-owner ~ \.row \.page-title \{\s*font-size: 1rem;")
self.assertEqual({k: TABLER_BUTTON_CLASSES[k] for k in TABLER_BUTTON_CLASSES if k.startswith("navbar:")},
                 {"navbar:nav": "nav nav-bordered flex-wrap", "navbar:link": "nav-link mw-100 text-break gap-2"})
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --group test pytest tests/crud_views_tabler --ds tests.crud_views_tabler.settings -q -k "owner_header or navbar_keys or tabler_classes"`
Expected: 3 FAIL (`nav-pills` still rendered, `.nav-pills` in CSS, no `navbar:` keys).

- [ ] **Step 3: Implement**

- `buttons.py`: the two keys from Global Constraints.
- CSS: delete the four `.cv-tabler-navbar .nav-link` / `.nav-pills` rules; keep one rule
  `.cv-tabler-navbar .nav-link.active { color: var(--tblr-link-color); border-color: var(--tblr-link-color); }`
  (Tabler's `nav-bordered` active uses `--tblr-primary`, too dim in dark mode, about 2.9:1) and the
  `.cv-tabler-owner ~ .row .page-title` rule. Rewrite the block comment: keys from #384, Tabler `nav-bordered`.
- `page.html`: comment says PR #383 merged, the tabs take Tabler classes from the `navbar:*` keys (#384), the
  layout follows upstream's owner-as-page-heading recipe; duplicate-heading suppression is theme-owned.
- Findings doc: rows 36 and 38 → `**DONE** upstream #384: ...` in the style of row 35; in each entry add a
  `- **Resolved:** upstream #384 (branch ...06.40.1...)` line and reword "What we do" (36: keys registered, CSS down
  to the active colour and view-title size; 38: contract reworded, recipe published, our layout matches it, view
  heading `h2` with a bar, suppression stays ours). Change "PR #383 (open)" to merged.
- `docs/crud_views_tabler.md`: same facts at lines ~50 and ~58-66.

- [ ] **Step 4: Run all suites**

Run: `task test`
Expected: all pass, `check` clean.

- [ ] **Step 5: Commit**

```bash
git add src/crud_views_tabler tests/crud_views_tabler docs/crud_views_upstream_findings_roastery.md docs/crud_views_tabler.md
git commit -m "Adopt upstream navbar class keys (#384): Tabler nav-bordered tabs; findings 36 and 38 resolved"
```

### Task 2: Browser check

**Files:** possibly `crud_views_tabler.css` + findings entry 36 if a fix is needed.

- [ ] **Step 1:** `task up` (or the running server), log in as `alex`/`demo`, open a customer detail and a nested
  list (Orders). Check light and dark (layout switch gear): tab underline, active colour readable, icon/label gap,
  hover. Check at 375px width: tabs wrap, no horizontal page scroll, wrapped row indentation acceptable.
- [ ] **Step 2:** If a fix is needed, add a scoped rule, add its line to finding 36, re-run `task test`, commit
  `"Theme: navbar tab polish after browser check"`. Otherwise add "(browser check on 2026-11-19, light/dark, 375px)" to finding 36 and commit that doc line alone.
