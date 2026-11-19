# Adopt compact formset layout for cupping scores

Date: 2026-11-11.

## Intent

Use django-crud-views' merged compact formset support (#347 / PR #348) in the Acme Roasters cupping editor. Its one row per taster currently repeats eight labels on every row. Shared desktop headings should shorten the editor while each input keeps an associated label, and narrow screens should show labelled row cards.

## Goals and boundaries

- Opt only `CUPPING_FORMSETS["scores"]` into compact mode, with `taster` and all seven score fields in their existing order and grid proportions, including room for row controls.
- Keep existing field widgets, quarter-point validation, add/delete behavior, create/update permissions and save behavior.
- Check the rendered create and update pages under the Tabler theme, including a narrow viewport and an invalid form redisplay. Add narrowly scoped Tabler CSS only if the new upstream hooks need it; record any theme CSS in the upstream findings tracker.
- Update finding 22 and the known rough edge in `docs/crud_views_upstream_findings_roastery.md` to reflect adoption and verification.

Order line items remain classic. Their `ProductSelect` subclass supplies per-option `data-beans` attributes for the existing row script, and compact mode currently rejects widget subclasses. That separate gap is tracked as finding 34 and upstream issue #349. Do not change either upstream checkout or the order-line widget, script or formset.

## Approaches

- **Chosen: upstream compact declaration.** Add `CompactLayout` / `CompactColumn` to the cupping `FormSet`; upstream owns headings, row labels and mobile cards. This uses the supported stock `Select` and `NumberInput` widgets and keeps one source of rendering behavior.
- **Local template or CSS workaround.** Hide repeated labels and add a custom heading strip. This would duplicate responsive rendering and label behavior that upstream now provides, with more upkeep.
- **Keep classic layout.** This leaves the repeated-label finding unresolved.

## Builder calls

Use the existing Django demo and editable upstream dependency. Map the current `Column3("taster")`, seven `Column1` scores and `form_control_col2` to spans 3 + 7 + 2 = 12. Remove the cupping-specific classic helper layout if compact rendering no longer uses it; retain no unnecessary duplicate layout. Verify the rendered headings and labels, row controls, invalid POST redisplay and score persistence with focused existing tests or one meaningful regression test. Run the project check and relevant roastery/theme tests. Keep the tracker accurate about what was actually verified.
