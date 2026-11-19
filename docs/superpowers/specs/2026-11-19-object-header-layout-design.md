# Object header layout for ViewSet Navigation: design

Date: 2026-11-19. Status: approved on 2026-11-19; page-template mechanism revised during planning (same look).

Follows `2026-11-19-object-navbar-adoption-design.md` (implemented on branch `adopt/object-navbar-381`, not merged),
which placed upstream's bar above the page header.

## Intent

The user is not happy with the bar above the page header: it sits above the breadcrumb, so the page reads
bottom-up, and the section links are far from the content they switch. On every page that has a bar, the owner
object becomes the page (avatar, name, section tabs) and the view's own header drops to a section heading above its
content, the way a CRM or GitHub shows "inside this customer".

Upstream changed meanwhile (branch `gsd/phase-06.40-object-navbar-opt-in-section-navigation-381`, head `498eaa84`):
the feature is now called "ViewSet Navigation" in the docs (Python names and `cv_navbar` unchanged), and two
component tags render the parts separately: `{% cv_navbar_identity %}` and `{% cv_navbar_items %}`. The branch is
now PR #383 (open, not merged; checkout head `271928a6`, no source change since `498eaa84`). The 11 navbar tests and
90 theme tests pass against it. Docs cite PR #383 as open, never as merged.

## Goals

- On a page with a bar, the Tabler page header shows, top to bottom: the breadcrumb (unchanged); one row with an
  avatar holding the owner ViewSet's header icon (`cv_navbar.icon`) and the owner's name (`cv_navbar.label`) as the
  page title; the section links as Tabler underline tabs, the active one marked, the row closing the header.
- The view's own header (icon, `cv_header`, `cv_paragraph`) and its context buttons form a section heading row
  below the tabs, title left and buttons right (option 1 of the mockups). The customer row has no
  buttons.
- Pages without a bar look exactly as today.
- Any project using `crud_views_tabler/page.html` gets this by attaching the mixin; the demo's views do not change.
  The demo's "Show code" button stays with the view's buttons, below the tabs, never in the owner row.

## Non-goals

- No subline ("Customer · Berlin") and no initials in the avatar: those need owner-specific data in a shared
  template.
- Same pages as now carry the bar (customer detail, update, delete, every order/address/subscription page nested
  under a customer). No change to which views attach the mixin, nor to green lots (context buttons stay).
- No change to breadcrumbs, the application menu, permissions or the sibling checkouts (read-only).

## Anti-goals

- A copied or overridden upstream navbar template (approach Y, rejected).
- Demo-only markup (approach Z, rejected): the theme owns the layout.
- Buttons beside the owner's name that act on the current view (option 2, rejected): "+" beside the customer name
  would mean "new order".

## Constraints

- Theme fix order (CLAUDE.md): upstream hook, then CSS in `crud_views_tabler.css`, then override. Every theme CSS
  rule and every upstream awkwardness gets an entry in `docs/crud_views_upstream_findings_roastery.md` in the same
  commit.
- App code under `example/` never imports `django_tabler` or `crud_views_tabler`.
- Upstream's template contract (`docs/reference/theme.md`, "ViewSet Navigation templates") says: "The identity
  must not become another page heading or replace the existing view header/actions." This design makes the owner's
  name the page heading on purpose and keeps the view header as a section heading. It reads `cv_navbar.label` and
  `cv_navbar.icon` from the documented context instead of using the identity leaf, so no upstream template changes.
  This deviation gets its own findings entry.
- Modals (`X-CV-Modal`) have no bar (`cv_navbar` is `None`) and keep today's layout.
- Print: Tabler's `.page-header` is already `d-print-none`; the packing slip must print as today.

## Approaches

Decided in conversation on 2026-11-19 after browser mockups (`.superpowers/brainstorm/`, screens
`navbar-layouts.html` and `navbar-buttons.html`).

Layout (screen 1): A today's bar above the header; B name as pretitle, pills above the content; C underline tabs
above the content; **D object header (chosen)**: the owner is the page, sections are its tabs, the view title
shrinks to a section heading.

Buttons (screen 2): **1 move down with the view's section heading (chosen)**; 2 stay beside the owner's name
(rejected, see anti-goals).

Build:

| Approach | Chosen | Trade-off |
|---|---|---|
| X: the theme's page template builds the header from `cv_navbar`, places `{% cv_navbar_items %}`, CSS scoped to the bar turns upstream's pills into Tabler underline tabs | yes | CSS imitating tabs must follow Tabler's tab styles; one findings entry |
| Y: as X, but override `navbar_items.html` with `nav-tabs` | no | a copied template drifts from upstream silently |
| Z: only the demo's `project/crud_views.html` | no | other projects get nothing; contradicts the theme owning the layout |

## Design

**Page template** (revised during planning, same look as the approved mockup). Django renders a block in one place
only, and projects override `page_title` (the demo's order detail appends the state badge), `cv_context` (order
detail) and `actions` (the demo's Show code). So the view's header row does not move in the DOM; the owner header
is inserted above it instead, and the row reads as the section heading below the tabs:

- `django_tabler/layouts/app.html` gets one more empty block, `page_header_top`, inside `.page-header >
  .container-xl` before the title row. `page_header_before` stays as an empty block.
- `crud_views_tabler/page.html`, with a bar, fills `page_header_top` with: the breadcrumb (`{% cv_breadcrumb %}`);
  an owner row: a Tabler `avatar` holding `cv_navbar.icon` and `<h1 class="page-title">` with `cv_navbar.label`
  (h1: the layout has no other h1, and the view title stays at its `CRUD_VIEWS_HEADER_LEVEL`, h2 while unset); then
  `{% block cv_navbar %}<div class="cv-tabler-navbar ...">{% cv_navbar_items %}</div>{% endblock %}`, the tabs,
  closing the owner part with the tab border. The `breadcrumb` block renders `{% cv_breadcrumb %}` only without a
  bar, so the breadcrumb appears once, at the top.
- The title row (`page_heading` with `page_title`, `subtitle` with `cv_paragraph`, `actions` with `cv_context`) is
  unchanged and follows the tabs: the view's title, subtitle and buttons, Show code included, sit together below
  the tabs, as in option 1. CSS scoped to the bar sizes that title as a section heading. No demo template changes.
- Emptying the `cv_navbar` block drops the tabs; the owner row stays.
- `.page-header` is `d-print-none`, so the owner row, tabs and view row are hidden in print as today.
- Browser `<title>` (my call): `cv_header` followed by the owner's label when a bar renders, e.g. "Orders · Bean &
  Bloom Café", so browser tabs of different customers differ.

**Heading that repeats the active tab** (added 2026-11-19 after review in the browser). With a bar, the view's
heading (icon and `cv_header`) is left out when its text equals the active tab's label (tags stripped, whitespace
collapsed): the tab already says it. Its subline and buttons stay in the row. A heading that says more than the tab
(order detail "Order #1073 Draft", "Edit order", "Create address") stays. Exact text match, so a near miss keeps
one heading too many, never one too few. The demo's customer detail is titled "Details" to match its tab.
Implemented as a theme template tag `cv_tabler_heading_repeats_tab` (library `crud_views_tabler`) reading the
documented `cv_navbar` mapping (`items`, `active`, `label`) and `view.cv_header`.

**CSS** (`crud_views_tabler.css`): replace the two pill rules of finding 36 with rules scoped to
`.cv-tabler-navbar` that make upstream's `nav nav-pills` look like Tabler's `nav-tabs` (underline/bordered active
tab, no pill background) in light and dark mode, keeping the icon gap. Exact rules are the builder's, checked in
the browser against Tabler 1.6.1's `nav-tabs`.

**Docs.**

- Findings: rewrite 36 for the new CSS; new finding: the theme deliberately makes the identity the page heading,
  against upstream's contract sentence quoted above, and why (the user's layout choice; the contract forbids a
  theme layout that is common elsewhere). Finding 23 and the "Not shown in the demo" bullet: describe the header
  layout instead of "above the page header". Use the upstream name "ViewSet Navigation" in new text and keep the
  existing headings (cross-references).
- `docs/crud_views_tabler.md` mapping table and paragraph; the template chain paragraph in `CLAUDE.md`.
- The adoption spec stays as written; this spec supersedes its "Placement" and "Look" parts.

## Tests

- Theme (`tests/crud_views_tabler/`): with a bar, the page title is the owner's label, the tabs are inside
  `.page-header`, the view's `cv_header` and context buttons appear after the tabs and not in the owner row; without
  a bar, the header is unchanged (title, subtitle, buttons in `.page-header`); emptying the
  `cv_navbar` block drops the tabs; the CSS test pins the new rules.
- Example (`example/sales/tests/test_navbar.py`): existing tests adapted to the new markup (the bar no longer sits
  before `.page-header`); the order detail's state badge sits in the view title, not the owner's; on customer detail Edit/Delete sit in the section heading; on a nested list the create
  button sits in the section heading; the owner's name appears once as the page title and is escaped; modal delete
  unchanged; packing slip prints without tabs.
- Browser check: customer detail, a nested list, a nested form; sidebar and top bar, light and dark, 375 px, print.
- `task test` and `manage.py check --fail-level WARNING` pass.

## Left to the builder

- The exact markup and spacing of the avatar row, the tab row and the section heading row.
- The CSS rules that turn pills into tabs.
- Whether to work on `adopt/object-navbar-381` or a new branch on top of it.
