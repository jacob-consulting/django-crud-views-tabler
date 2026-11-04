// Sales pages: grind and bag size only apply to coffee lines; the packing slip's print button.
// Progressive enhancement only: OrderLineForm.clean() and OrderLine.save() clear the fields on the server anyway.
(function () {
  "use strict";

  function syncLine(product) {
    const row = product.closest(".cv-formset-row");
    if (!row) return;
    const option = product.options[product.selectedIndex];
    const beans = !product.value || (option && option.dataset.beans === "1");
    row.querySelectorAll("[data-order-line-beans-only]").forEach(function (select) {
      if (!beans) select.value = "";
      select.disabled = !beans;
    });
  }

  function syncAll(root) {
    root.querySelectorAll("select[data-order-line-product]").forEach(syncLine);
  }

  document.addEventListener("change", function (event) {
    if (event.target.matches("select[data-order-line-product]")) syncLine(event.target);
  });

  document.addEventListener("click", function (event) {
    if (event.target.closest("[data-print]")) window.print();
  });

  document.addEventListener("DOMContentLoaded", function () {
    syncAll(document);
    // rows added by formset.js arrive empty; re-sync whatever is inserted later
    new MutationObserver(function () { syncAll(document); }).observe(document.body, { childList: true, subtree: true });
  });
})();
