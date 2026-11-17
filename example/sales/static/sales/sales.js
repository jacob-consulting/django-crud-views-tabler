// Sales pages: the packing slip's print button. (Grind and bag size of order lines follow the product through
// upstream's QuerysetConditions, see sales/forms.py.)
(function () {
  "use strict";

  document.addEventListener("click", function (event) {
    if (event.target.closest("[data-print]")) window.print();
  });
})();
