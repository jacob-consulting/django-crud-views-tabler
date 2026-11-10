# Adopt upstream findings 24 and 29

Date: 2026-11-10.

## Intent

Finish the Acme demo's adoption of the upstream custom-permission documentation/checks (finding 24) and snippet context support (finding 29). Finding 28 is already adopted and is outside this change.

## Goals

- **24:** Keep the existing `CustomerSubscription.Meta.permissions` declaration of `run_customersubscription` and `RunSubscriptionsView.cv_permission = "run"`. Reference upstream's `docs/reference/custom_form_view.md#a-permission-of-its-own` from the subscription module's explanation of the recipe. Verify that the configured demo passes the upstream startup checks and that existing subscription tests still establish Owner access and denial for other users. This adopts documentation and diagnostics; no permission behavior changes are needed.
- **29:** Set `OrderDuplicateView.cv_message_template_code` to `_("Created {{ view.duplicate }} from {{ object }}")`. The message identifies the new draft and its source, using the view's existing `duplicate` attribute and the original `object`.
- **29:** Set the nested `OrderCreateView.cv_header_template_code` to `_("New order for {{ parent_object }}")`. The heading identifies the customer before the order exists. Keep the top-level `AllOrdersCreateView` heading as `New order`, since that page asks the user to select a customer.
- Update findings 24 and 29's summary rows and detailed entries to distinguish implemented upstream support from actual demo adoption. Replace obsolete pending-adoption wording for the two snippet examples and retain historical descriptions as history. Preserve any unrelated tracker edits.

## Non-goals and anti-goals

No broader order or subscription cleanup, new features, schema changes, migrations, permission changes, theme/template overrides, or edits to either upstream checkout. Preserve order creation/duplication behavior and redirects, action labels, breadcrumbs, and the top-level create flow. Do not reimplement upstream snippet context or permission checks locally. Do not accidentally make class-level labels depend on page-only snippet variables.

## Constraints

Use the existing Django demo, lazy translations, and editable sibling upstream dependencies. The local upstream checkout already provides `view`, lazy `parent_object`, and `viewset.E269`. Its declared-permission checks cover core model ViewSets, excluding Guardian and Resource ViewSets; passing the check does not prove database permission rows or user grants. Existing request-level permission tests remain necessary. Record adoption based on local code and verification; do not infer GitHub issue closure from a local implementation.

## Approaches

- **Adopt and demonstrate upstream support (chosen):** use `view.duplicate` and `parent_object` in the two demo snippets, reference the existing permission recipe, verify rendered behavior and access, and reconcile the tracker. This improves the demo while keeping the change small.
- **Documentation and verification only:** retain the old order text and check compatibility. Lower code churn, but leaves finding 29's new capabilities unused and does not deliver the chosen scope.

## Verification

Extend existing order tests to verify the actual duplicate success message contains both the new draft and its source and that the redirect still targets the duplicate. Verify the rendered nested create heading names the URL's customer, including escaping of customer-provided text, on GET and invalid form redisplay. Verify the top-level create heading remains `New order` and unauthorized customers remain inaccessible using existing access coverage. Reuse existing subscription permission tests rather than copying upstream's check implementation into local tests.

Run the focused order and subscription tests and `uv run python example/manage.py check --fail-level WARNING`; complete the repository's `task test` verification before integration. No new dependencies or visual mockups are needed for these text changes.

## Builder decisions

The builder may choose assertion helpers and test organization within the existing sales tests. Preserve translated template autoescaping and assert user-visible output rather than source declarations.
