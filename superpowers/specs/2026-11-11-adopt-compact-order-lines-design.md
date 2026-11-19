# Adopt compact formset layout for order lines

Date: 2026-11-11.

## Intent

Use django-crud-views' merged custom-widget compatibility support (issue #349 / PR #350) to give the Acme Roasters order-line editor shared desktop headings and labelled mobile row cards. This completes the remaining formset adoption noted as finding 34.

## Goals and boundaries

- Opt only `ORDER_FORMSETS["lines"]` into compact mode. Preserve the field order and existing grid proportions: product 4, grind 2, bag size 2, quantity 2, controls 2.
- Mark `ProductSelect` as compact compatible. Its ordinary `Select` rendering and `data-beans` option attributes must survive in existing and dynamically added rows.
- Preserve coffee-only grind and bag-size behavior, server validation and saving, add/delete controls, errors, labels, and create/update behavior.
- Use the existing upstream checkout and Tabler theme. Update finding 34 to reflect adoption and verification; make narrowly scoped theme adjustments only if rendered pages need them.
- Leave cupping scores and other formsets unchanged. Do not alter upstream code or broaden custom-widget compatibility beyond `ProductSelect`.

## Approaches

- **Chosen: upstream compatibility marker and compact declaration.** Add `CompactWidgetCompatible` to `ProductSelect` and `CompactLayout` to the order-line `FormSet`. Upstream provides headings, associated labels, mobile cards, and row controls. This is a small adoption change, with the application responsible for verifying its widget behavior.
- **Local template override.** Build shared headings and responsive cards in this project. This would duplicate the upstream formset presentation and add upkeep for dynamic rows and accessibility.

## Builder calls

Remove the order-line classic helper layout if compact mode no longer uses it. Verify rendered create and update pages, the `data-beans` option attribute, coffee-only controls after changing a product and adding a row, invalid form redisplay, and existing persistence tests. Run focused sales and theme checks. Record only checks actually performed in the findings tracker.
