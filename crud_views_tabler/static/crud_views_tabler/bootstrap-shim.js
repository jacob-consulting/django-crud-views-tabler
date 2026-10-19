// Bridges Tabler's bundle to what django-crud-views' scripts expect.
//
// 1. Tabler's UMD bundle exposes the Bootstrap components on `window.tabler` (tabler.Modal, tabler.Tooltip, ...);
//    modal.js and tooltip.js look for a global `bootstrap`.
// 2. list.filter.js calls the jQuery plugins (`$(el).collapse("toggle")`). Bootstrap only registers them when
//    jQuery is present as it initialises, but tabler.min.js runs before jQuery here, so register them now.
//    This script is deferred and runs after both tabler.min.js and jQuery.
(function () {
    const tabler = globalThis.tabler;
    if (!tabler) {
        return;
    }
    globalThis.bootstrap ??= tabler;

    const $ = globalThis.jQuery;
    if (!$) {
        return;
    }
    for (const component of Object.values(tabler)) {
        if (typeof component?.jQueryInterface === "function" && component.NAME && !$.fn[component.NAME]) {
            $.fn[component.NAME] = component.jQueryInterface;
            $.fn[component.NAME].Constructor = component;
        }
    }
})();
