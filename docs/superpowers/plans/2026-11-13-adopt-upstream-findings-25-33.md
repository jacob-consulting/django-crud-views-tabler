# Adopt upstream #361 / #362 (findings 25, 33) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update the demo to use upstream's workflow transition variants/icons (#362) and the manage pages that only
manage-group members can open (#361), and record both in the findings doc.

**Architecture:** No new theme code is expected. The upstream defaults `btn btn-<variant>` are valid Tabler classes.
The demo switches `CRUD_VIEWS_MANAGE_VIEWS_ENABLED` to upstream's `"yes"` and makes `alex` the only member of the
manage group, in the seed.

**Tech Stack:** Django 6.1, django-crud-views (editable sibling checkout), Django test runner, Taskfile.

**Spec:** `docs/superpowers/specs/2026-11-13-adopt-upstream-findings-25-33-design.md`

## Global Constraints

- `../django-crud-views` must be at `origin/main` `4510cee9` or later. The checkout is read-only for this repo: pull
  only, no edits.
- The group name comes from `crud_views.lib.settings.crud_views_settings.manage_group` (default
  `CRUD_VIEWS_MANAGE`). Never hard-code the name.
- Settings line: `CRUD_VIEWS_MANAGE_VIEWS_ENABLED = os.environ.get('CRUD_VIEWS_MANAGE_VIEWS_ENABLED', 'yes')`.
- Only `alex` joins the manage group. `sam`, `kim` and `admin` do not.
- Any theme CSS rule must get a findings-doc entry in the same commit (CLAUDE.md).

## Review Focus

- `seed_demo --reset` recreates `alex`. The new `alex` must be in the manage group again, and the group must
  survive or be recreated (it is not in `DEMO_GROUPS`). Test: `test_reset_keeps_alex_in_the_manage_group`
  (Task 2).
- A superuser outside the group (`admin`) must get 403 and no manage button. Test:
  `test_superuser_outside_the_group_is_refused` (Task 2).
- A Cancel button blocked by a required comment must keep its `*` marker as well as its icon. Test:
  `test_transition_buttons_use_variant_and_icon` asserts both (Task 1).
- Under the `no` mode even `alex` must get 403. Test: `test_no_mode_refuses_alex` (Task 2).
- Nested manage pages (for example a customer's addresses) must follow the same gate. Test:
  `test_alex_opens_the_manage_page` also requests one nested manage URL (Task 2).

---

### Task 1: Workflow transition buttons use variant and icon (finding 33)

**Files:**
- Modify: `example/sales/tests/test_orders.py` (`OrderWorkflowTests`)
- Modify: `docs/crud_views_upstream_findings_roastery.md` (finding 33 section, summary row 33)
- Possibly modify: `src/crud_views_tabler/buttons.py` (only if Step 4 shows a wrong look)

**Interfaces:**
- Consumes: upstream keys `workflow:transition-<variant>`, and the `button_class`/`icon` handling in
  `crud_views_workflow/lib/widgets.py`.
- Produces: nothing used by later tasks.

- [ ] **Step 1: Pull upstream and sync**

Run: `git -C ../django-crud-views pull --ff-only && uv sync`
Expected: HEAD at `4510cee9` or later. Then run `git -C ../django-crud-views log --oneline -3`; it must show #364
and #365.

- [ ] **Step 2: Write the test `test_transition_buttons_use_variant_and_icon`**

As `self.login()` user, GET the workflow page of a draft order that has lines. Assert:
- A regex matches `<button[^>]*value="wf_confirm"[^>]*class="btn btn-success` (or class-before-value; use a
  regex that allows both orders, like the existing tests).
- The Confirm button contains `<svg` (the Tabler icon) and `Confirm`.
- The `wf_cancel` button has `btn btn-danger`, contains `<svg` and `Cancel order`, and still contains
  `<span aria-hidden="true">*</span>`.

- [ ] **Step 3: Run the test**

Run: `uv run python example/manage.py test sales.tests.test_orders.OrderWorkflowTests`
Expected: PASS after the pull. Before the pull it would fail, because every transition was `btn btn-primary`
without an SVG. If it fails after the pull, look at the HTML before you change any code.

- [ ] **Step 4: Check in the browser**

With `task up` running, sign in as alex and open the workflow page of a draft order. Check:
- Confirm is green, Cancel is red, and both show their icon next to the label.
- The disabled state works: an order without lines gets a disabled Confirm.
- The icon spacing is right in both the light and the dark theme.

Only if something looks wrong, register the affected `workflow:transition-<variant>` keys in
`TABLER_BUTTON_CLASSES` and log that under finding 33.

- [ ] **Step 5: Update finding 33 in the findings doc**

Add a `**Status: DONE upstream**` bullet at the top of finding 33, in the same style as finding 34. It links
issue #362 and PR #364, merged as `b21370e3` on 2026-11-13, and gives the keys `workflow:transition-<variant>` with
defaults `btn btn-<variant>`. Then add an `**Adopted here (2026-11-13):**` bullet: the order workflow page shows each
transition's variant and icon; no theme keys or CSS were needed (unless Step 4 added some); give the test name. In
summary row 33, set the status column to `**DONE** upstream #362 / PR #364; order transitions show variant and
icon`.

- [ ] **Step 6: Commit**

```bash
git add example/sales/tests/test_orders.py docs/crud_views_upstream_findings_roastery.md
git commit -m "Demo: adopt upstream workflow transition variants and icons (#362, finding 33)"
```

### Task 2: Only `alex` can open the manage pages (finding 25)

**Files:**
- Modify: `example/config/settings.py:187` (`'no'` → `'yes'`)
- Modify: `example/dashboard/seed.py` (`seed()`: create the manage group and add `alex`)
- Modify: `Taskfile.yaml` (`migrate` task: add `{{.MANAGE}} cv_manage_group` after `migrate`)
- Modify: `example/dashboard/tests.py` (rewrite `ManageViewsTests`)
- Modify: `example/templates/registration/login.html` (Alex's line: `Owner: sees everything, including the
  manage pages`)
- Modify: `CLAUDE.md` (Conventions bullet on `CRUD_VIEWS_MANAGE_VIEWS_ENABLED`; the demo accounts line)
- Modify: `docs/crud_views_upstream_findings_roastery.md` (finding 25 section, summary row 25)

**Interfaces:**
- Consumes: `crud_views_settings.manage_group`, `crud_views_settings.manage_views_enabled`, and the management
  command `cv_manage_group`.
- Produces: after `seed_demo`, `alex` is a member of the `crud_views_settings.manage_group` group.

- [ ] **Step 1: Rewrite `ManageViewsTests` (failing tests)**

`setUp` runs `call_command("seed_demo", stdout=StringIO())` and creates a superuser `admin`. Mode patches use
`mock.patch.object(crud_views_settings, "manage_views_enabled", ...)`, as in the current test. Tests:
- `test_settings_default_to_yes_without_the_environment_variable`: the settings source contains the
  Global-Constraints line.
- `test_alex_opens_the_manage_page`:
  - As alex, GET `/customer/manage/` returns 200.
  - GET `/customer/` contains `href="/customer/manage/"`.
  - One nested manage URL also returns 200. Find it with `reverse()` on an address/order manage name that takes a
    seeded customer pk; list the names with `example/manage.py show_urls` or `grep manage` in the URLconf.
- `test_sam_and_kim_are_refused`: each gets 403 on `/customer/manage/`, and `/customer/` for sam has no
  `/customer/manage/` link.
- `test_superuser_outside_the_group_is_refused`: `admin` gets 403 on `/customer/manage/`.
- `test_no_mode_refuses_alex`: under `"no"`, alex gets 403.
- `test_reset_keeps_alex_in_the_manage_group`: after `call_command("seed_demo", "--reset", ...)`, the new alex is
  in the group named `crud_views_settings.manage_group`.

- [ ] **Step 2: Run the tests to see them fail**

Run: `uv run python example/manage.py test dashboard.tests.ManageViewsTests`
Expected: FAIL. The settings test fails (the value is still `'no'`), and alex gets 403.

- [ ] **Step 3: Implement**

- Change the settings fallback to `'yes'`.
- In `seed()`, call `Group.objects.get_or_create(name=crud_views_settings.manage_group)` and add `alex`'s user to
  it.
- Add `cv_manage_group` to the Taskfile's `migrate` task.
- Update the login text and both CLAUDE.md lines. The new bullet says: default `yes`; only members of
  `CRUD_VIEWS_MANAGE` (alex, from the seed) can open the pages; `no` turns them off for everyone.

- [ ] **Step 4: Run the tests to see them pass, then the whole suite**

Run: `uv run python example/manage.py test dashboard` and then `task test`
Expected: all PASS, including the `check --fail-level WARNING` step.

- [ ] **Step 5: Check in the browser at phone width**

As alex, open `/customer/manage/` at 1280 px and at 390 px. Then run `document.documentElement.scrollWidth`; it
should be `<= 390`. If the tables overflow:
- Add a rule to `src/crud_views_tabler/static/crud_views_tabler/crud_views_tabler.css` that scrolls the manage
  tables horizontally. Use the manage page's own wrapper or table selector; read the upstream manage template for
  it.
- Re-check the width.
- Log the rule under finding 25.

- [ ] **Step 6: Update finding 25 in the findings doc**

- Retitle finding 25 to "Manage pages were open to every signed-in user while DEBUG was on".
- Add a `**Status: DONE upstream (access)**` bullet. It links issue #361 and PR #365, merged as `4510cee9` on
  2026-11-13, and gives the mode table (yes = group members, debug_only = members and DEBUG, no = nobody) and
  `cv_manage_group`.
- Add an `**Adopted here (2026-11-13):**` bullet: default `'yes'`, alex the only member from the seed, Taskfile
  runs `cv_manage_group`, plus the test names.
- Add a line on the tables: upstream left `.table-responsive` out of #361 on purpose. Say what Step 5 found (theme
  CSS added, or no overflow).
- Rename the old `What we did` bullet to `What we did before #361`.
- In summary row 25, set the status to `**DONE** upstream #361 / PR #365 (access); alex in the manage group;
  table overflow: <result>`.

- [ ] **Step 7: Commit**

```bash
git add example/config/settings.py example/dashboard/seed.py example/dashboard/tests.py Taskfile.yaml \
  example/templates/registration/login.html CLAUDE.md docs/crud_views_upstream_findings_roastery.md
# plus crud_views_tabler.css if Step 5 added a rule
git commit -m "Demo: adopt upstream developer-only manage pages (#361, finding 25)"
```

### Task 3: Findings doc intro

**Files:**
- Modify: `docs/crud_views_upstream_findings_roastery.md:1-32`

- [ ] **Step 1: Update the intro paragraph**

After the "Findings 2, 3 and 19 are **DONE upstream**" sentence, add: findings 33 and 25 (access) are **DONE
upstream** as of 2026-11-13 via #362 (PR #364) and #361 (PR #365), adopted here against the sibling checkout at
`4510cee9`. Do not touch the 2026-11-04 line references paragraph.

- [ ] **Step 2: Verify and commit**

Run `grep -n '#36[12]' docs/crud_views_upstream_findings_roastery.md`. It must show the intro, both summary rows
and both sections.

```bash
git add docs/crud_views_upstream_findings_roastery.md
git commit -m "Docs: findings 25 and 33 done upstream"
```
