# Adopt upstream #361 (finding 25) and #362 (finding 33)

Short design for a small change.

## Intent

Two django-crud-views issues from the Roastery findings closed on 2026-11-13. The task is to record them in
`docs/crud_views_upstream_findings_roastery.md` and update the demo and theme to use the new features.

- **#362 / PR #364 (finding 33).** In button presentation, workflow transitions now use `custom["variant"]` and
  `custom["icon"]`. The variant is looked up through the class keys `workflow:transition-<variant>`, whose defaults
  are `btn btn-<variant>`.
- **#361 / PR #365 (finding 25, access part).** Manage pages require an active member of `CRUD_VIEWS_MANAGE_GROUP`.
  The default mode is now `"yes"`, `"no"` turns them off for everyone, and the new `cv_manage_group` command creates
  the group. The `.table-responsive` part of finding 25 was left out upstream and stays open.

## Approaches (finding 25)

- A. Keep the demo's `'no'` and only update the doc and tests. Least work, but the pages stay hidden.
- **B. Picked by the user.** Use upstream's `"yes"` and make `alex` (Owner) the only member of the manage group. The
  demo shows the manage pages without new accounts. Every demo password is public, so nobody gains access they did
  not already have.
- C. Like B, plus a read-only `dev` account with Guardian read grants. It mirrors upstream's `developer` account but
  adds the most seed work.

Finding 33 has one sensible way: use the upstream feature as it is.

## Design

**Setup.** Pull `../django-crud-views` to `origin/main` (`4510cee9`), then run `uv sync`.

**Finding 33.**
- The upstream defaults `btn btn-<variant>` are valid Tabler classes. Register `workflow:transition-*` in
  `TABLER_BUTTON_CLASSES` only if something renders wrong (for example `light`/`dark`). The demo uses only primary,
  success, warning and danger.
- Add a sales test showing that the order workflow page renders Confirm as `btn-success` and Cancel as
  `btn-danger`, each with its Tabler icon SVG and its label.
- Check the page in a browser.

**Finding 25.**
- In `example/config/settings.py`, change the env fallback from `'no'` to `'yes'`. The variable keeps working as
  an off switch (`CRUD_VIEWS_MANAGE_VIEWS_ENABLED=no`).
- The seed (`dashboard/seed.py`) calls `get_or_create` on the configured manage group and adds `alex` to it, so
  `seed_demo` and `--reset` work on their own.
- Add `cv_manage_group` to the Taskfile setup after `migrate`, as upstream recommends.
- Rewrite `ManageViewsTests`:
  - `alex` gets 200 and sees the manage action.
  - `sam`, `kim` and a superuser who is not a member get 403 and no manage action.
  - `"no"` gives 403 even for `alex`.
- Look at a manage page at 390 px. If the tables overflow, add a theme CSS rule (the theme fix order allows CSS
  before an override) and log it under finding 25.

**Docs.**
- In the findings file, mark 33 DONE and 25 as access DONE / table overflow still open, in the intro, the summary
  table and each finding's section.
- Update the manage-settings bullet in `CLAUDE.md`, and the demo account notes to say alex can open the manage
  pages.

## Left to the builder

The test placement and whether theme CSS is needed both depend on what the browser check shows.
