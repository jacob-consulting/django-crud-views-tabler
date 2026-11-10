# Adopt upstream finding 28: subscription ViewSet names

Date: 2026-11-10.

## Intent and scope

Use upstream's ViewSet naming support (#338 / PR #342) so the Acme demo consistently calls customer subscriptions “Subscription(s)” in generated page labels. This is a small adoption change, limited to finding 28.

## Goals

Set `verbose_name=_("subscription")` and `verbose_name_plural=_("subscriptions")` on both `cv_subscription` and `cv_all_subscriptions` in `example/sales/views/subscriptions.py`. Remove the `cv_header_template_code` overrides from the nested and top-level list views. Generated list headings, breadcrumbs, and create/update/delete headings must use the ViewSet names.

Update finding 28's summary and detailed entry in `docs/crud_views_upstream_findings_roastery.md` to record adoption and removal of the old workaround, preserving the existing uncommitted upstream-status edits.

## Non-goals and anti-goals

No broader subscription cleanup, model renaming, migrations, permission changes, theme changes, or edits to either upstream checkout. Keep the custom “Run subscriptions” labels and existing subscription success messages. Avoid changing model-centric delete summaries or other texts that upstream intentionally derives from the model.

## Constraints

Build on the existing Django demo and editable upstream dependency, which already exposes both naming fields. Use the existing lazy translation convention. Preserve unrelated work in the tracker.

## Approaches

- **ViewSet names (chosen by the user):** declare the singular and plural once on each ViewSet and let upstream propagate them. This removes redundant list overrides and covers the other generated labels.
- **Individual view overrides:** retain the list overrides and add more per-view text overrides. This duplicates upstream functionality and makes naming inconsistent as views evolve.
- **Model names:** rename the model's metadata. This affects a wider scope than the requested ViewSet presentation change.

## Verification and builder decisions

Verify rendered headings and breadcrumbs for the two lists and nested create/update/delete views, including the delete modal where applicable. Confirm the custom run page label still reads “Run subscriptions”. Use the existing subscription test fixtures and run the subscription tests plus Django's system check; choose precise assertions based on the rendered output. No new UI or visual design is needed.

The builder may choose test structure and formatting; the names and scope above are settled.
