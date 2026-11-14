# Design: a structured manage page for django-crud-views

**Date:** 2026-11-13 / 2026-11-14 (two design sessions)
**Status:** approved by the maintainer, filed upstream as
[django-crud-views#366](https://github.com/jacob-consulting/django-crud-views/issues/366) (body: D-01–D-16; addendum
comment: D-17–D-24). This document consolidates both into one text. Where the two disagree, the later decision wins,
and the affected entries below say so.
**Revised:** 2026-11-14, after a review against upstream `4510cee9` and the demo's live `customer` ViewSet. The
review added D-25–D-29 and amended D-05, D-07, D-08, D-10–D-12, D-14, D-17–D-24; amended entries carry a *Review:*
note. These changes are **not yet in #366**.
**Mockup:** [`2026-11-14-manage-page-mockup.html`](2026-11-14-manage-page-mockup.html), next to this file
(self-contained apart from Tabler 1.6.1 CSS from jsDelivr; open it in a browser).
**Tracking here:** finding 35 in `docs/crud_views_upstream_findings_roastery.md`.

## How to read the mockup

- It is modelled on the demo's `/customer/manage/` page (a Guardian ViewSet with 6 views) in the Tabler theme. The
  values are illustrative, not a dump: e.g. the real detail header template is
  `sales/snippets/customer_header.html`, and every real `context_actions` list ends in `manage`. The
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
  - The Presentation card is drawn open. D-21 has it collapsed on load.
  - The Show defaults switch is drawn on. D-12 has defaults hidden on load.
  - The Guardian section lacks the `guardian_mixin` row and shortens the key to `accept_global_perms` (D-10:
    `guardian_accept_global_perms`).
  - The review's additions are not drawn: the "Access for: you" block (D-05), the **Other** section (D-25) and the
    "no permission required" and parent-requirement badges (D-08).
  - The Presentation card shows a `resource_permissions` row. The review removed it (D-21).
  - The requirement and policy badges are drawn as links. The review made them plain badges (D-24).
  - The Ancestor policy card matches the review's two-column form (D-02).

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
  - No access evaluation for another user **in #366**. The page shows the signed-in user's own result (D-05).
    Checking another user, with an object and a trace of how access is decided, belongs to
    [#370](https://github.com/jacob-consulting/django-crud-views/issues/370) (D-29).
  - No manage page for Resource ViewSets. Upstream registers none (`viewset/__init__.py:205-208`), and this design
    doesn't change that.
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
    - *Review, decided by the maintainer:* two columns, the setting and its effective value, with an "inherited"
      marker where nothing is declared. The separate Declared column goes: in the current template a declared
      value is either `None` (inherited) or equal to the effective one (`view_manage.html:77-110`), so the marker
      carries the same information and the card fits the side column.
    - The card keeps `id="cv-ancestor-policy"` as its anchor.
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
- **D-05 — "Access for: you" block instead of the current-user table.** *Review: replaces "no current-user column".*
  - The old three-column `has_perm` table is dropped, but the signed-in user's result stays on the page as **one
    row at the top of the Permissions matrix**, labelled "Access for: *username* (you)". It uses the same cells as
    every other row:
    - **model** when `user.has_perm()` is true for that permission. Unlike the Users rows, this is the effective
      result: it includes rights through groups and superuser status.
    - **n objects**, on Guardian pages, for the objects the user reaches through object grants, their groups'
      grants included (`get_objects_for_user`, strict, one count per permission).
    - a dash otherwise.
  - **No per-view marks.** They were considered and rejected: without an object, `cv_has_access` returns `False`
    for every Guardian object view and `True` for a Guardian list as soon as the permission key exists
    (`crud_views_guardian/lib/mixins.py:129-146, 201-208`), so every user would read the same line. The view
    badges (D-08) say which permission each view needs; per-view and per-object answers come with #370, where an
    object pk makes them decidable.
  - Why it stays: `docs/reference/settings.md` ("Diagnose the signed-in account") and `guardian.md` tell developers
    to sign in as the affected user and read this result. Dropping it would remove a documented workflow with no
    replacement until #370.
  - The row's data method takes a user, so #370 can feed it another user (D-29).
  - The counts run after `_check_nested_auth`, like the other auth queries. *Assistant's call.*
- **D-06 — Users behind the existing setting.**
  - The Users section renders only when `CRUD_VIEWS_MANAGE_SHOW_USERS` is on. Its default (False) is unchanged.
  - It lists users with a direct model permission or a direct Guardian object grant. Rights that come through a
    group show in that group's row.
  - Beyond about 20 users, the rest fold under a "+ n more" `<details>`.
- **D-07 — User-level Guardian grants.** `GuardianManageView` also counts user object grants per user and
  permission. Group object grants stay as today.
  - *Review:* the query goes through Guardian's `get_user_obj_perms_model()` for the ViewSet's model, not the
    generic `UserObjectPermission` class directly, so direct-foreign-key grant tables are counted too. *Assistant's
    call.*
  - *Review:* in the new matrix, group grants use the matching `get_group_obj_perms_model()`, so user and group
    counts cover the same tables. "As today" refers to what is counted, and the old `get_permission_holders()`
    keeps its query. *Assistant's call.*
  - *Review:* like every auth query on this page, it runs only after `_check_nested_auth(..., provider="guardian")`
    (as `get_permission_holders()` does today, `crud_views_guardian/lib/views.py:419`).
- **D-26 — Superusers and group sizes.** *Review, decided by the maintainer.* Django grants an active superuser
  every permission, so without this the matrix can show a permission as held by nobody while several accounts
  have it. Two count queries per page.
  - Each group row shows its member count.
  - A line under the matrix states how many active superusers exist ("hold every permission"). Their names appear
    only with `CRUD_VIEWS_MANAGE_SHOW_USERS`.
  - Rejected: the superuser line alone (an empty group would still look like a holder), and leaving both out.

### Views card

- **D-08 — One summary line per view.**
  - Shows `cv_key`, the URL path, and the real view class as a dotted path (this fixes the metaclass bug).
  - Badges:
    - the view's requirement (D-23);
    - on Guardian pages, the effective global-fallback policy: **global fallback**, **strict** or **not
      applicable**.
  - The separate "Global permission fallback" table is removed. Its content moves into this badge and into the
    expanded view's Guardian section.
  - *Review:* the requirement badge has more states than "permission" and "group":
    - **no permission required**, for view variants without `cv_permission` (the non-PermissionRequired classes);
    - **custom**, when the view overrides the gate and declares nothing (see D-27).
  - *Review:* a view's requirement has two parts, and the summary line shows both:
    - its **own** requirement (one of the states above);
    - on a nested ViewSet, the **parent requirement** from the ancestor policy, as a second badge (e.g. `change`
      plus `parent: view`). It names the nearest ancestor's permission for the view's operation; the Ancestor
      policy card has the higher ancestors.
    - A nested Guardian **create** has no own requirement: `GuardianParentPermissionMixin.has_permission()` returns
      `True` there (`crud_views_guardian/lib/mixins.py:381-385`). It shows only `parent: change`. Nested Guardian
      detail, update and delete keep their own object permission (`get_object()`, `mixins.py:117-123`) and show
      both badges.
  - *Review:* the URL path is the ViewSet's own route made readable (D-20).
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
    - **Other** (D-25): every remaining `cv_*` attribute.
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
  - *Review: the rule, made precise.* It is no longer left to the builder, because the obvious reading fails.
    - An attribute is **set** when a class in the view's MRO whose module is outside the `crud_views*` packages has
      it in its own `vars()`. This is the test W280 already uses (`CheckUnknownAttributes._suspects`,
      `lib/check.py:387-394`); reuse that code, don't write a second walk.
    - **Exception, `cv_context_actions`:** `ViewSet.register_view_class()` writes
      `view_class.cv_context_actions = [*actions, "manage"]` onto the project class
      (`viewset/__init__.py:351-354`), so the attribute sits in every project view's `vars()` whether or not the
      project declared it. In the demo all five customer views have it; only `CustomerDetailView` declares it.
      `register_view_class()` therefore records, before it assigns, whether the class declared the attribute
      itself, and the page uses that record. The record is consulted for every registered class in the MRO, not
      only the leaf: a project view that subclasses another registered view would otherwise inherit the base's
      library-written copy and show "set". *Assistant's call.*
    - Known limit, shared with W280: a project package whose name starts with `crud_views` (a theme such as
      `crud_views_tabler`) counts as library code.
- **D-25 — "Other" section: every remaining `cv_*` attribute.** *Review, decided by the maintainer.*
  - After the curated sections, **Other** lists every `cv_*` data attribute of the view that no curated row
    shows. Without it the page hides what makes a view special: the demo's project-set `cv_modal`,
    `cv_show_related_objects`, `cv_message_template_code`, `cv_list_actions_inline`, `cv_object_detail_layout` and
    `cv_property_display` are in no curated section, nor is view-level `cv_context_buttons`.
  - The attributes are found the way W280 finds them (`_collect_cv_names`, `lib/check.py:296-306`): declared on a
    class in the MRO, data only (no methods, properties or other descriptors). `cv_viewset` is left out.
  - Rows are in alphabetical order, so two views still compare line by line.
  - Set/default follows D-11, and the Show defaults switch hides default rows here too.
  - An attribute W280 would flag as unknown is marked as such in its row.
  - Values: a class shows as its dotted path, anything else as a shortened `repr`. A name that is only annotated
    and has no value (e.g. `cv_formsets` on a view that doesn't set it) shows "not declared".
  - *Assistant's calls:* the order, the exclusions and the W280 mark.
- **D-12 — Dimmed and switchable.**
  - Default rows are greyed out.
  - In every row the key stays visually stronger than the value: keys are darker and medium weight, default values
    are muted.
  - One **Show defaults** switch in the Views card header shows or hides default rows for all views at once, and in
    the Presentation card too (D-21).
  - Without JS, all rows are visible.
  - *Review, decided by the maintainer:* with JS, default rows are **hidden on load**. The page exists to show what
    is special, and most rows are defaults; **Other** (D-25) adds more of them.
    - A section whose rows are all hidden says "n defaults hidden", so an expanded view never looks empty or
      broken.
    - The choice isn't stored. Rejected: remembering it in `localStorage` (more JS and a stored key), and defaults
      shown on load as the mockup draws them (the long lists return by default).
  - The four `*_template_code` entries may collapse into one row when all of them are empty.

### ViewSet facts (side column)

- **D-17 — System checks for this ViewSet.** Runs `viewset.checks()` on page load.
  - **No messages:** a small strip at the top of the side column: "✓ no issues · n system checks for this ViewSet".
  - **Warnings or errors:** an alert at the top of the main column, above Permissions, listing each message with its
    check id (e.g. `viewset.W280`).
  - *Review: scope.* `viewset.checks()` alone would show "no issues" while `manage.py check` fails, because several
    checks are registered separately. The strip also runs, filtered to this ViewSet: the ancestor declaration checks
    including E269 (`crud_views/checks.py:198`), the conditional checks (`:394`), the icon check (`:584`) and, on
    Guardian pages, `crud_views_guardian.E001`. Project-wide checks (settings, assets, button classes) are not
    shown; the strip says "for this ViewSet".
  - *Review:* messages whose id is in `SILENCED_SYSTEM_CHECKS` are left out, as Django's own runner does.
  - *Review, assistant's calls:* the registered check functions return messages for all ViewSets, and the icon
    check's messages carry no object to filter by (`crud_views/checks.py:592-601`). Each function is therefore
    split so that its per-ViewSet part can be called alone. The "n" in the strip counts the `viewset.checks()`
    entries only.
  - *Review, measured:* the 178 `viewset.checks()` for `customer` take about 10 ms on the first run and 1 ms
    after, in the demo.
- **D-18 — ViewSet identity card.**
  - Shows name, prefix, pk/pk_name and app.
  - Adds the model as a dotted path. *Review:* the **Resource** badge is dropped; Resource ViewSets have no manage
    page.
  - Adds verbose name and plural, ordering, and the header icon (drawn, plus its name).
  - Values the ViewSet doesn't set show the effective value with its source, e.g. `customer · customers (model
    Meta)`.
- **D-19 — Hierarchy card.**
  - **Parents:** the full chain up to the top level, each linked to its manage page.
  - **Children:** every registered ViewSet whose `parent` is this one, with its model, plus the URL name and pattern
    of its manage page (e.g. `order-manage → /customer/<customer_pk>/order/manage/`).
  - **Links go up only.** A nested manage URL needs a parent object, and the parent's manage page has none. Going
    up, any required ancestor pks come from the current URL.
  - *Review:* a Resource child has no manage route. It is listed with its model and the note "Resource, no manage
    page".
  - *Review:* the card says how to get to a child's manage page: open the child's list under a parent object and
    use its manage action. Every registered view gets that action (`viewset/__init__.py:351-354`).
  - Rejected:
    - linking through a sample object, which costs extra queries and permission checks and gives no link for an
      empty table;
    - a new route for nested manage pages that needs no parent object, which would change URL routing and nested
      permissions.
- **D-20 — URL names card.** Each view's route name and path pattern, e.g. `customer-list → /customer/`.
  - *Review:* the route is a regex (`^customer/(?P<pk>\d+)/detail/$`, built in `viewset/__init__.py:455`). It is
    shown through Django's `django.contrib.admindocs.views.simplify_regex`, which gives `/customer/<pk>/detail/`.
    The import works without `admindocs` in `INSTALLED_APPS`. *Assistant's call.*
  - *Review:* the pattern is the ViewSet's own route. A prefix added by the project's `include()` isn't known to
    the ViewSet, so the card labels the column "route (relative to where the ViewSet is included)".
- **D-22 — "Set" for ViewSet fields.**
  - A ViewSet field is **set** when the project passed it to the constructor.
  - This is D-11 applied to the ViewSet instance.
  - *Review:* `model_fields_set` is not that list. The validators assign `pk` and `prefix`
    (`viewset/__init__.py:182-196, 285-286`), and an assignment adds the field to the set. For `customer` it
    reports `pk` and `prefix`, which `example/sales/views/customers.py:35-46` never passes. The passed names are
    recorded before the validators run (e.g. the input keys in a `mode="before"` validator).
  - For `customer` the set fields are model, name, icon_header, ancestor_policy and context_buttons.

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
    - `manage_view_class`, showing the effective class.
    - *Review:* the `resource_permissions` row is dropped; a ViewSet with a manage page is never a Resource.
  - *Review:* a view's own `cv_context_buttons` are not listed here. They show in that view's **Other** section
    (D-25), and the note under the table says so.

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
  - *Review: replaces "native `title` keeps the stock theme free of JS".* Badges carry `title` **and** the
    `data-cv-tooltip` marker. The tooltip adapter only touches marked elements
    (`static/crud_views/js/tooltip.js:27`), so without the marker no theme could upgrade them. With it, the stock
    page gets Bootstrap tooltips through the stock adapter (`adapters.js:93`), and `title` remains the fallback
    without JS.
  - *Review:* the group badge is drawn for the manage view only. No other view in the library declares a group
    requirement; a custom view gets one through the hook in D-27.
  - *Superseded detail:* #366's body (D-08) says "needs view" and "manage group". D-23 replaces that text.
- **D-24 — Documentation links through one new docs page, `docs/reference/manage.md`.**
  - **Where the links are:**
    - every card header gets a small round **"?"** button at the top right, after any existing card actions
      (e.g. after the Show defaults switch);
    - so do the checks strip and the Presentation sections "Templates and actions" and "Label modes";
    - *Review, decided by the maintainer:* the requirement badges and the Guardian-policy badges are **not**
      links. They keep their tooltip (D-23). Their documentation is reached through the Views card's "?" button
      and the badge key in the card footer. Reason: the badges sit inside each view's `<summary>` (D-09), and a
      link there gives the line two click behaviours and adds tab stops before every view.
      - Rejected: badges as links (the mockup), and plain badges with a linked requirement row in the expanded
        view (one more row per view).
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
  - **Base URL:** not a setting. *Review:* it is an attribute of `ManageView`, passed to the template as one
    context value. A project that hosts its own docs sets it on a subclass named in
    `CRUD_VIEWS_MANAGE_VIEW_CLASS` / `manage_view_class`, which exist today. A template block can't do this: the
    URL is used by about fifteen links. *Assistant's call.*
  - **Help-button class:** comes from the class registry, e.g. `manage:help`; the stock class is
    `btn btn-sm btn-outline-secondary`.
  - **Rejected:**
    - linking each card straight to existing pages: four cards have no matching page (permissions/`cv_permission`,
      view attributes, ViewSet fields, system checks), and the links would depend on other pages' headings;
    - writing those missing reference pages in this issue, which doubles the scope (now a non-goal).

### Access description and the follow-up

- **D-27 — A view describes its own requirement.** *Review, decided by the maintainer.*
  - A public classmethod on `CrudView` returns what the view needs. The return value is small:
    - the view's **own** requirement: a permission key, a group, none, or "custom";
    - whether the **ancestor policy applies** to it.
  - The parent part of the badge is not returned by the method. The page reads it from the ancestor policy data it
    already computes (`ManageView.get_ancestor_policy_data()`), so no view duplicates it.
  - Each class that owns a gate implements the method next to it: `CrudViewPermissionRequiredMixin` from
    `cv_permission`, `ManageView` from `CRUD_VIEWS_MANAGE_GROUP`, the Guardian parent mixin for the nested create
    case, and the views of `crud_views_workflow`, `crud_views_polymorphic` and `crud_views_object_detail` where
    their gate differs.
  - The D-08 badges are drawn from this method, not from `cv_permission` directly. A project view that overrides
    `has_permission()` overrides the method to describe itself; otherwise it shows "custom".
  - Why a method and not logic inside `ManageView`: the answer depends on which mixins a view is built from,
    #370's trace needs the same answer, and a description kept next to the gate changes with it.
  - Risk: a description can drift from the real gate. The tests pair each shipped view class with a request that
    proves the described requirement is the enforced one.
  - The method's name and exact return type are the builder's choice.
- **D-29 — What #370 adds to this page.** *Review, decided by the maintainer. Not part of #366.*
  - The "Access for" row (D-05) gets a form: a typed username (no dropdown of all accounts), an optional object
    pk, and a Check button. It is a GET form and changes nothing.
  - Without an object pk the result is the matrix row for that user. With one, each view also gets a yes or no
    for that object.
  - The trace (which grant or ancestor rule decided) comes from one function shared by the page and the command
    line. Today that logic is bound to a request (`_cv_ancestor_guard()` in `dispatch`), which is #370's open
    design question.
  - This lifts the non-goal "no access evaluation for another user" for #370 only.

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
  - *Review, decided by the maintainer:* each old block **wraps its whole new card**: `permission_holders` the
    Permissions card, `ancestor_policy` the Ancestor policy card, `guardian_config` the Guardian card. A project
    override replaces that card at the card's position and is fed by the old context keys. The overriding project
    loses the new card (the "you" row and the superuser line included) until it updates its template; the migration
    notes say so.
    - Rejected: old blocks as empty hooks below the cards. Nothing would be lost, but an overriding project would
      show the same information twice.
  - *Review:* the core template renders the complete Guardian page from the data (D-13). The Guardian template
    stays as a file but adds nothing the page depends on, because a project may replace it entirely and fill only
    `guardian_config` (`tests/test1/test_authorization_templates.py:77`).
  - The existing context keys stay with their current shapes (`cv`, `data`, `views`, `permission_holders`,
    `show_users`, `ancestor_policy`, and on Guardian pages `guardian_config` and `views[*].guardian_policy`). New
    structures go under new keys.
  - The cards are fed by **new** data methods. `get_view_data()` and `get_permission_holders()` keep their output
    and only feed the old keys, so project overrides of those methods don't affect the new cards.
  - User grants (D-07) appear only in the new matrix data.
  - The `class` fix applies to both the old and the new data. *Assistant's call.*
  - Visible output changes are documented in the migration notes.
  - *Review:* the old keys `data`, `views` and `permission_holders` are computed lazily, on first use by a
    template. No stock template reads them any more, and `get_permission_holders()` costs a query per permission
    (`views/manage.py:77-92`). *Assistant's call.*
- **D-28 — Existing tests and docs that pin the old page.** *Review.* These change with the page:
  - `tests/test1/test_ancestor_manage.py:485-486` asserts rows of the "Global permission fallback" table that D-08
    removes;
  - `tests/test1/test_ancestor_manage.py:343-348` (`_policy_table`) parses the three-column
    `table table-striped#cv-ancestor-policy`; the helper is rewritten for the two-column card (D-02), and the tests
    that use it keep asserting the same declared/inherited and effective facts;
  - `tests/test1/test_authorization_templates.py:77` overrides the `guardian_config` block and must keep passing
    (D-14);
  - `docs/reference/guardian.md#guardianmanageview` and `docs/reference/theme.md:762` describe the current tables
    and context;
  - `docs/reference/settings.md` ("Diagnose the signed-in account") is reworded for the "Access for: you" block;
  - both packages ship a `de` locale, which gets the new strings.
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
- Where `register_view_class()` keeps its record of a declared `cv_context_actions` (D-11), and where the ViewSet
  keeps the passed field names (D-22).
- The name and return shape of the requirement method (D-27).
- How the separately registered checks are filtered to one ViewSet (D-17).
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
- The "Access for: you" row shows, per permission, **model** for the signed-in user's `has_perm` result (a right
  held only through a group counts) and, on Guardian pages, the number of objects reachable through grants. There
  are no per-view marks.
- Group rows show member counts, and the superuser line shows the count of active superusers.

**Views**
- The `class` entry shows the view class's dotted path (regression test).
- `is_default` follows D-11 and D-22, unit-tested on the data rather than the HTML:
  - library value → default;
  - value copied from a setting → default;
  - attribute on a project class → set;
  - a placeholder `None` → shows the resolved value and its source;
  - `cv_context_actions` that only gained the library's `manage` entry → default; declared on the project class →
    set;
  - a ViewSet field is set only when the project passed it: `pk` and `prefix` filled in by the validators are
    defaults.
- The **Other** section lists a project-set attribute outside the curated rows (e.g. `cv_modal`) as set, and
  contains no method or property.
- The Show defaults switch hides and shows default rows in Views (Other included) and in Presentation. With JS,
  defaults are hidden on load, and a section with only default rows shows "n defaults hidden". Without JS, all
  rows are visible.
- The requirement badges render each case: permission, group (manage view), no permission required, custom, own
  plus parent requirement (nested detail), and parent requirement only (nested Guardian create).
- For every shipped view class, a request test proves that the requirement the method describes is the one
  enforced.

**ViewSet facts and Presentation**
- System checks:
  - a ViewSet with a failing check shows the alert at the top of the main column, with the check id;
  - a clean ViewSet shows the "no issues" strip with the number of checks;
  - a ViewSet that fails only a separately registered check (e.g. E269) shows the alert;
  - a message silenced through `SILENCED_SYSTEM_CHECKS` is not shown.
- Hierarchy:
  - on a top-level ViewSet, children are listed with their manage URL name and pattern, unlinked;
  - on a nested ViewSet, the parent chain links to the parents' manage pages, and those links resolve.
- Context-button targets render for `key_target`, parent, child, sibling and filter buttons. A custom subclass
  renders without error.
- Presentation is collapsed on load.
- A Resource child is listed in Hierarchy without a manage route, and the page renders without error.
- URL patterns render in the readable form (`/customer/<pk>/detail/`), not as regexes.

**Badges and docs**
- Requirement badges show the short key or group name, with the D-23 tooltip and hidden prefix. The Views card shows
  the key.
- `docs/reference/manage.md` exists, is linked from the reference index, and has one section per card.
- A test collects every docs anchor the templates link to and asserts that each exists as a heading in that page.
- Every "?" button points at `https://django-crud-views.readthedocs.io/en/stable/reference/manage/#…` and opens
  in a new tab. The base URL comes from the manage view class; a subclass with another base URL changes every
  link.
- A view's `<summary>` contains no link.

**Compatibility**
- A template that extends `crud_views/view_manage.html` and overrides `permission_holders` and `guardian_config`
  still renders (test), and each override appears in place of its card, not next to it.
- A Guardian page whose Guardian template is replaced by one that fills only `guardian_config` still shows the
  matrix with object counts and the per-view Guardian badges.
- Badge and help classes resolve through the class registry with Bootstrap 5 defaults. A test registers a custom
  class and sees it rendered.

**Docs and example**
- Docs updated: the manage page reference, the migration notes and the pages named in D-28.
- The `de` locales of both packages contain the new strings.
- The old context keys trigger no query when no template reads them (query-count test).
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
- **Request-time work:** checks run on every page load (D-17). Measured for `customer`: about 10 ms cold, 1 ms
  warm. The separately registered checks added by the review are not measured.
- **"Access for: you" needs a second look:** the row answers per permission, not per view (D-05). The reader has
  to match it against the view badges until #370 exists.
- **Two hiding mechanisms:** views and Presentation start collapsed, and on top of that the Show defaults switch
  hides rows. Together that's a lot of hidden content.
- **Help-link maintenance (D-24):** the docs URL is a constant pointing at `stable`. Unreleased features link to
  sections that `stable` doesn't have yet.
- **Unlinked children (D-19):** child manage pages can't be reached directly from the parent's manage page.
