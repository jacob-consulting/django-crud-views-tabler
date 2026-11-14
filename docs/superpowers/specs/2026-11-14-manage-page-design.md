# Design: a structured manage page for django-crud-views

**Date:** 2026-11-13 / 2026-11-14 (two design sessions)
**Status:** approved by the maintainer, filed upstream as
[django-crud-views#366](https://github.com/jacob-consulting/django-crud-views/issues/366) (body: D-01–D-16; addendum
comment: D-17–D-24). This document consolidates both into one text. Where the two disagree, the later decision wins,
and the affected entries below say so.
**Mockup:** [`2026-11-14-manage-page-mockup.html`](2026-11-14-manage-page-mockup.html), next to this file
(self-contained apart from Tabler 1.6.1 CSS from jsDelivr; open it in a browser).
**Tracking here:** finding 35 in `docs/crud_views_upstream_findings_roastery.md`.

## How to read the mockup

- It renders the demo's real `/customer/manage/` data (a Guardian ViewSet with 6 views) in the Tabler theme. The
  upstream implementation uses stock Bootstrap 5 markup, and themes recolour it through class-registry keys (D-15).
  Tabler's soft badges (`bg-*-lt`) are therefore a theme choice, not part of the upstream design.
- The views (`list`, `detail`, …) and the Presentation card expand on click. The **Show defaults** switch works.
  `detail` is open, to show an expanded view.
- **Known differences from the design:**
  - Some rows merge keys (`success_key · cancel_key`, `*_template_code`). D-10 requires one key per row; only
    `*_template_code` may merge, and only when all four are empty (D-12).
  - The "?" buttons and the badge links go to the closest **existing** readthedocs pages, so they work today. The
    implementation links to sections of a new `reference/manage/` page instead (D-24).
  - Only `list` and `detail` have full content when expanded. The other views are stubs.
  - The checks strip only shows the "no issues" state. The alert state (D-17) is not drawn.

## Why

The manage page (developer-only since #361) is hard to read. At commit `4510cee9`, `/customer/manage/` was about
10,800 px tall with 216 table rows: one `<h3>`, twelve `<h4>`, every section a `table table-striped`, separated by
`<br><hr><br>`. Most of the page is a 25-row key/value table per view, and most of those rows are `None` or the
library's stock value. Values print as raw Python (`True`, `None`, `['home']`). Declared and effective values look
the same.

The maintainer opens the page for two things: **permissions** and **view configuration**. Both are scattered:
- "Who holds which permission" is split across three tables:
  - Permissions, which covers only the current user;
  - Permission Holders, which covers groups;
  - Global permission fallback, which is per view.
- "Which permission does this view need" (`cv_permission`) is not shown at all.

Defects found along the way:
- **Bug:** the `class` row shows `<class 'crud_views.lib.view.meta.CrudViewMetaClass'>` for every view.
  `get_view_data()` iterates `get_all_views()`, which returns view *classes*, so `str(view.__class__)` is the metaclass.
- **Gap:** user-level Guardian object grants are invisible. Sam's actual access (`view_customer` and
  `change_customer` on 4 customers, via `UserObjectPermission`) does not appear. This is because
  `GuardianManageView.get_permission_holders()` only counts `GroupObjectPermission`, and the users list only covers
  direct model permissions.
- **No `.table-responsive`:** the manage tables don't scroll on narrow screens. tabler-test makes them scroll below
  768 px with theme CSS (finding 25).

Relevant upstream code:
- `src/crud_views/lib/views/manage.py`
- `src/crud_views/templates/crud_views/view_manage.html`
- `src/crud_views_guardian/lib/views.py` (`GuardianManageView`)
- `src/crud_views_guardian/templates/crud_views/view_guardian_manage.html`
- `src/crud_views_guardian/templates/crud_views/snippets/guardian/config_table.html`
- `src/crud_views/lib/button_classes.py` (class registry)

## Goals, non-goals, anti-goals

**Goals:**
- A developer answers "who holds which permission" and "how is this view configured, and what is special about
  it" at a glance.
- The stock Bootstrap 5 page looks structured, not only the Tabler one.
- Every card leads to its documentation.

**Non-goals:**
- **Access and impersonation:**
  - No change to manage access (#361).
  - No impersonation or "check as user X".
  - No access evaluation for another user. A command-line access trace is a separate placeholder,
    [#370](https://github.com/jacob-consulting/django-crud-views/issues/370).
- **Page features:**
  - No editing from the manage page.
  - No new settings.
  - No tabs.
  - No views-as-columns comparison grid.
- **Docs:** no full reference pages for core permissions/`cv_permission`, the `cv_*` view attributes, ViewSet fields
  or the system-check catalogue. The new manage docs page (D-24) covers what the page shows and links onward.

**Anti-goals (failure even if it works):**
- **A copied theme template:** a Tabler-only override template that drifts from upstream while the stock page stays
  flat.
- **Colour-only meaning:** colour as the only carrier of meaning.
- **Broken overrides:** breaking existing project templates that extend `crud_views/view_manage.html`.

## Approaches considered (how it is built)

1. **Templates only.** Rewrite the two templates and detect defaults with `{% if value is None %}`.
   - Smallest diff.
   - Cannot tell a stock template path from a custom one.
   - Pivoting the permission table in template loops is ugly.
   - **Rejected.**
2. **The view prepares the data, the template lays it out.** Presentation-ready structures in Python, `is_default`
   flags, existing blocks and context keys kept, badge colours through the class registry. **Chosen.**
3. **Like 2, plus a Tabler-only manage template in the theme.**
   - Full control over the look.
   - Copied templates drift silently, and the stock page stays flat.
   - **Rejected.**

Page-structure alternatives were compared as mockups:
- **A, tabs.** Rejected: hides content from browser search and needs hash handling.
- **B, one page of cards.** Chosen.
- **C, overview plus a views-as-columns grid.** Rejected: too wide once a ViewSet has workflow or custom action views.

## Decisions

Numbering matches #366, so a reviewer can map each entry to the issue. *Assistant's call* marks decisions the
assistant made and the maintainer accepted. Everything else was decided by the maintainer.

### Purpose and layout

- **D-01 — Reader and focus.**
  - The reader is a developer, i.e. a manage-group member (#361).
  - The page is optimised for permissions and view configuration.
  - Everything else (ViewSet facts, hierarchy, ancestor policy, Guardian) stays on the page but is secondary.
- **D-02 — One page of cards (layout "B").** A single page, so browser search, printing and anchors keep working.
  On large screens:
  - **Main column:** checks alert (only when a check fails, D-17), Permissions, Views, Presentation (collapsed,
    D-21).
  - **Side column:** checks strip (D-17), ViewSet (D-18), Hierarchy (D-19), URL names (D-20), Ancestor policy,
    Guardian.
  - Below the large breakpoint the side column stacks under the main one.
  - **Ancestor policy card:** two labelled parts, "as ancestor of nested requests" and "requests to this ViewSet",
    and it keeps the "configuration only, not an access result" note.
  - **Guardian card:** on Guardian pages only. A plain card rather than the current warning alert, showing
    `get_objects_for_user` (strict). `parent_viewset`, provider and `accept_global_perms` are not repeated there,
    because the Hierarchy and Ancestor policy cards already show them. *Assistant's call.*
  - *Superseded detail:* #366's body lists `parent` in the ViewSet card. It moved to the Hierarchy card (D-19).
- **D-03 — Stock Bootstrap 5 only.**
  - Cards, list groups, tables, badges, a form switch and `<details>`.
  - No theme-specific markup upstream.
  - Every table sits inside `.table-responsive`.

### Permissions card

- **D-04 — Holder × permission matrix.**
  - **Columns:** the ViewSet's permissions (`viewset.permissions`). Each header shows the key with the codename as a
    sub-label, custom permissions included.
  - **Rows:** holders, in two labelled sections, **Groups** then **Users**. Holders are rows so that many of them
    make the table longer, not wider.
  - **Cells:** **model** (model-level permission), **n objects** (Guardian object grants), or a dash.
  - A footer legend explains the two badges.
- **D-05 — No current-user column.** The current user's `has_perm` table is dropped. Since #361 the viewer is always
  a developer, so it only reported the developer's own rights.
- **D-06 — Users behind the existing setting.**
  - The Users section renders only when `CRUD_VIEWS_MANAGE_SHOW_USERS` is on. Its default (False) is unchanged.
  - It lists users with a direct model permission or a direct Guardian object grant. Rights that come through a
    group show in that group's row.
  - Beyond about 20 users, the rest fold under a "+ n more" `<details>`.
- **D-07 — User-level Guardian grants.** `GuardianManageView` also counts `UserObjectPermission` per user and
  permission. Group object grants stay as today.

### Views card

- **D-08 — One summary line per view.**
  - Shows `cv_key`, the URL path, and the real view class as a dotted path (this fixes the metaclass bug).
  - Badges:
    - the view's requirement (D-23);
    - on Guardian pages, the effective global-fallback policy: **global fallback**, **strict** or **not
      applicable**.
  - The separate "Global permission fallback" table is removed. Its content moves into this badge and into the
    expanded view's Guardian section.
- **D-09 — Collapsed by default.** Each view is a native `<details>` element with the stable anchor
  `#cv-view-<key>`. All views start collapsed.
- **D-10 — The expanded view is one two-column key/value table.**
  - Keys sit in a fixed-width column that never wraps. Values take the remaining width.
  - Sections are thin heading rows:
    - **Navigation:** context and list actions, home/success/cancel keys, list action method, backend-only.
    - **Templates.**
    - **Icons.**
    - **Guardian**, on Guardian pages only: `guardian_mixin`, and `cv_guardian_accept_global_perms` with its
      effective policy.
  - **One key per row**, always in the same section and order, so two views compare line by line. *Assistant's
    call.*
  - Keys are displayed without the `cv_` prefix.
  - Rejected:
    - three side-by-side columns, because values wrapped and it looked unclean;
    - set values first with defaults at the bottom, because a key's position would depend on whether it's set.
- **D-11 — Effective values; "set" means set by a project class.**
  - Each row shows the value in effect.
  - Where `None` is a placeholder that resolves elsewhere, the row shows the resolved value and its source, e.g.
    `icon_header` → `building-store (from ViewSet)`.
  - A row is **set** only when a class outside the crud_views packages defines the attribute in the view's MRO,
    i.e. the project's view class or a project base class. Everything else is a **default**. That includes library
    class values and values the library copied from a `CRUD_VIEWS_*` setting at import (e.g.
    `ListView.cv_context_actions` from `CRUD_VIEWS_LIST_CONTEXT_ACTIONS`).
  - Accepted consequence: a project-wide setting shows greyed out on every view. It stays visible while defaults are
    shown.
  - Rejected: comparing against crud_views' shipped defaults, which would need provenance tracking for settings
    copied at import.
- **D-12 — Dimmed and switchable.**
  - Default rows are greyed out.
  - In every row the key stays visually stronger than the value: keys are darker and medium weight, default values
    are muted.
  - One **Show defaults** switch in the Views card header shows or hides default rows for all views at once, and in
    the Presentation card too (D-21).
  - Without JS, all rows are visible.
  - The four `*_template_code` entries may collapse into one row when all of them are empty.

### ViewSet facts (side column)

- **D-17 — System checks for this ViewSet.** Runs `viewset.checks()` on page load.
  - **No messages:** a small strip at the top of the side column: "✓ no issues · n system checks for this ViewSet".
  - **Warnings or errors:** an alert at the top of the main column, above Permissions, listing each message with its
    check id (e.g. `viewset.W280`).
- **D-18 — ViewSet identity card.**
  - Shows name, prefix, pk/pk_name and app.
  - Adds the model as a dotted path, or a **Resource** badge for Resource ViewSets.
  - Adds verbose name and plural, ordering, and the header icon (drawn, plus its name).
  - Values the ViewSet doesn't set show the effective value with its source, e.g. `customer · customers (model
    Meta)`.
- **D-19 — Hierarchy card.**
  - **Parents:** the full chain up to the top level, each linked to its manage page.
  - **Children:** every registered ViewSet whose `parent` is this one, with its model, plus the URL name and pattern
    of its manage page (e.g. `order-manage → /customer/<customer_pk>/order/manage/`).
  - **Links go up only.** A nested manage URL needs a parent object, and the parent's manage page has none. Going
    up, any required ancestor pks come from the current URL.
  - Rejected:
    - linking through a sample object, which costs extra queries and permission checks and gives no link for an
      empty table;
    - a new route for nested manage pages that needs no parent object, which would change URL routing and nested
      permissions.
- **D-20 — URL names card.** Each view's route name and path pattern, e.g. `customer-list → /customer/`.
- **D-22 — "Set" for ViewSet fields.**
  - A ViewSet field is **set** when the project passed it, i.e. it is in pydantic's `model_fields_set`.
  - This is D-11 applied to the ViewSet instance.
  - For `customer` the set fields are name, prefix, pk, model, context_buttons, icon_header and ancestor_policy.

### Presentation card (main column)

- **D-21 — Presentation, collapsed.**
  - A `<details>` card below Views, collapsed on load. Its header shows "n set · m defaults · applies to all views".
  - It sits in the main column because the button targets need the width.
  - Rows follow D-10 to D-12.
  - **Context buttons:** a table with key, button type, **what it points to**, and label. "Points to" is derived from
    each button type's own fields:
    - `ContextButton` with `key_target`: the route name and path;
    - `ParentContextButton`: the parent's view, or "top level, never shown";
    - `ChildContextButton`: the route and path from `child_name`/`child_key`;
    - `SiblingContextButton`: the sibling ViewSet's view;
    - `FilterContextButton`: "toggles the list filter", plus its template;
    - a custom subclass: falls back to its type and template.

    Child and sibling targets are shown without links (same reason as D-19). A note says that each view's
    `context_actions` row decides where a button appears.
  - **Templates and actions:**
    - `extends`;
    - `inaccessible_actions`, showing the effective value and naming the setting it comes from, if any;
    - the three `*_actions_inline` lists.
  - **Label modes:** the context, list and form label modes.
  - **Other:**
    - `manage_view_class`, showing the effective class;
    - `resource_permissions`, for Resource ViewSets only (a dash for models).

### Badges and documentation links

- **D-23 — Short permission and group badges.**
  - **Blue = permission:** the badge text is the permission key (`view`, `add`, a custom key like `roast`). Its
    tooltip says "needs permission: sales.add_customer", the full Django permission string (app label first, then
    the codename, which starts with the action).
  - **Magenta = group membership:** the badge text is the group name. For the manage view that's the configured
    `CRUD_VIEWS_MANAGE_GROUP`. Its tooltip says "needs group membership: CRUD_VIEWS_MANAGE". The badge type is
    generic, so any view that requires a group can use it.
  - Colour is never the only carrier of meaning:
    - each badge has a native `title` tooltip;
    - a `visually-hidden` prefix ("permission", "group") is there for screen readers;
    - the Views card footer has a key: blue = required permission, magenta = required group, green = Guardian
      policy, "hover a badge for details".
  - Native `title` keeps the stock theme free of JS. A theme can upgrade it through `cv.adapters.tooltip`.
  - *Superseded detail:* #366's body (D-08) says "needs view" and "manage group". D-23 replaces that text.
- **D-24 — Documentation links through one new docs page, `docs/reference/manage.md`.**
  - **Where the links are:**
    - every card header gets a small round **"?"** button at the top right, after any existing card actions
      (e.g. after the Show defaults switch);
    - so do the checks strip and the Presentation sections "Templates and actions" and "Label modes";
    - the requirement badges and the Guardian-policy badges become links.
  - **How they open:** in a new tab (`target="_blank" rel="noopener"`, `aria-label="Documentation: <card>"`).
  - **Where they point:** every link goes to a section of the new manage page in the docs, one section per card. Each
    section explains its card and links on to the detailed pages:
    - `reference/nested/#ancestor-authorization`
    - `reference/guardian/#guardianmanageview`
    - `reference/context_buttons/`
    - `reference/action_menus/#label-mode`
    - `reference/settings/#manage-diagnostics`
  - **Why one page:** the anchors belong to this feature, so renaming headings elsewhere cannot silently break the
    page's links.
  - **Docs version:** links go to the **`stable`** docs. Readthedocs builds only `latest` and `stable`, and
    `stable` matches released code.
  - **Base URL:** a library constant, not a setting. A project that hosts its own docs overrides the template block.
  - **Help-button class:** comes from the class registry, e.g. `manage:help`; the stock class is
    `btn btn-sm btn-outline-secondary`.
  - **Rejected:**
    - linking each card straight to existing pages: four cards have no matching page (permissions/`cv_permission`,
      view attributes, ViewSet fields, system checks), and the links would depend on other pages' headings;
    - writing those missing reference pages in this issue, which doubles the scope (now a non-goal).

### Building it

- **D-13 — The view prepares, the template lays it out.**
  - `ManageView` builds presentation-ready structures:
    - permission columns and holder rows;
    - each view's summary and its sectioned entries, with an `is_default` flag on each entry;
    - the ViewSet facts, hierarchy, URL names, presentation rows and check results.
  - `GuardianManageView` extends the same structures (object counts including user grants, Guardian entries and
    badges) instead of keeping a parallel table.
  - Templates contain no default detection and no pivoting.
- **D-14 — Compatibility.**
  - The existing block names stay (`ancestor_policy`, `guardian_config`, `permission_holders`), and each card gets
    one new block.
  - The existing context keys stay with their current shapes (`cv`, `data`, `views`, `permission_holders`,
    `show_users`, `ancestor_policy`). New structures go under new keys.
  - The cards are fed by **new** data methods. `get_view_data()` and `get_permission_holders()` keep their output
    and only feed the old keys, so project overrides of those methods don't affect the new cards.
  - User grants (D-07) appear only in the new matrix data.
  - The `class` fix applies to both the old and the new data. *Assistant's call.*
  - Visible output changes are documented in the migration notes.
- **D-15 — Badge and row classes through the class registry.**
  - The keys follow the `workflow:badge-<colour>` pattern, e.g. `manage:badge-model`, `manage:badge-objects`,
    `manage:badge-permission`, `manage:badge-group`, `manage:badge-policy-<state>`, `manage:row-default`,
    `manage:help`. Exact names are a planning choice.
  - Stock defaults are Bootstrap 5 classes (`text-bg-*`, `text-body-secondary`).
  - Themes register their own. tabler-test will register `bg-*-lt`.
- **D-16 — Handoff.** The upstream deliverable is #366 with its `gsd-handover` section. Filing it doesn't implement
  the feature, create a phase or create a worktree.

## Left to the builder

- Exact names: context keys, blocks and class keys.
- The precise MRO rule for "outside the crud_views packages", and how lists and tuples compare.
- The "+ n more" threshold.
- JS or CSS-only for the switch.
- Card order inside the side column.
- Wording of labels, badges and tooltips (translatable).
- The section structure of `docs/reference/manage.md`.
- Example-app and docs coverage, in proportion to the change.

## Acceptance criteria

**Layout and data**
- Core and Guardian manage pages render the card layout of D-02. No `<br><hr><br>` remains.
- At 390 px viewport width, the page doesn't overflow sideways.
- Nested ViewSets render the full ancestor policy (cascade, read, write, actions).

**Permissions**
- Permissions render as the D-04 matrix.
- With `CRUD_VIEWS_MANAGE_SHOW_USERS` on, user-level Guardian grants are listed with per-permission counts. With it
  off, there is no Users section, on both core and Guardian pages.

**Views**
- The `class` entry shows the view class's dotted path (regression test).
- `is_default` follows D-11 and D-22, unit-tested on the data rather than the HTML:
  - library value → default;
  - value copied from a setting → default;
  - attribute on a project class → set;
  - a placeholder `None` → shows the resolved value and its source;
  - a ViewSet field is set when it is in `model_fields_set`.
- The Show defaults switch hides and shows default rows in Views and in Presentation. Without JS, all rows are
  visible.

**ViewSet facts and Presentation**
- System checks:
  - a ViewSet with a failing check shows the alert at the top of the main column, with the check id;
  - a clean ViewSet shows the "no issues" strip with the number of checks.
- Hierarchy:
  - on a top-level ViewSet, children are listed with their manage URL name and pattern, unlinked;
  - on a nested ViewSet, the parent chain links to the parents' manage pages, and those links resolve.
- Context-button targets render for `key_target`, parent, child, sibling and filter buttons. A custom subclass
  renders without error.
- Presentation is collapsed on load.
- Model and Resource ViewSets both render the identity card.

**Badges and docs**
- Requirement badges show the short key or group name, with the D-23 tooltip and hidden prefix. The Views card shows
  the key.
- `docs/reference/manage.md` exists, is linked from the reference index, and has one section per card.
- A test collects every docs anchor the templates link to and asserts that each exists as a heading in that page.
- Every "?" button and linked badge points at `https://django-crud-views.readthedocs.io/en/stable/reference/manage/#…`
  and opens in a new tab.

**Compatibility**
- A template that extends `crud_views/view_manage.html` and overrides `permission_holders` and `guardian_config`
  still renders (test).
- Badge and help classes resolve through the class registry with Bootstrap 5 defaults. A test registers a custom
  class and sees it rendered.

**Docs and example**
- Docs updated: the manage page reference and the migration notes.
- The bootstrap5 example updated.

## Downstream adoption in tabler-test (separate task, after release)

- Register Tabler classes for the `manage:*` keys in `crud_views_tabler`.
- Drop the finding-25 overflow rule (`#cv-ancestor-policy` scroll below 768 px) once the tables are in
  `.table-responsive`.
- Update finding 35.

## Points a reviewer may want to probe

These are judgement calls, not open questions:
- **Defaults rule (D-11):** grey means "not set by a project class". So a deliberate project-wide setting looks like
  a default.
- **Request-time work:** checks run on every page load (D-17). There are 178 checks for `customer` today, so the cost
  per request is probably small but has not been measured.
- **Two hiding mechanisms:** views and Presentation start collapsed, and on top of that the Show defaults switch
  hides rows. Together that's a lot of hidden content.
- **Help-link maintenance (D-24):** the docs URL is a constant pointing at `stable`. Unreleased features link to
  sections that `stable` doesn't have yet.
- **Unlinked children (D-19):** child manage pages can't be reached directly from the parent's manage page.
