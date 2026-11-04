// Tabler's bundle exposes Bootstrap's components on window.tabler, not window.bootstrap.
// crud_views calls Bootstrap only through cv.adapters (adapters.js); point them at Tabler.
// The namespace is resolved on every adapter call, so tabler.min.js may load deferred.
Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler));
// Toolbar tooltips open below the buttons, so they do not cover the page header; the rest keep Tabler's default.
// Wrap crud_views' init instead of replacing it, so its tooltip-transition guard stays in place; Bootstrap reads
// the placement from the data-bs-placement attribute. An explicit placement on the button wins.
{
    const init = cv.adapters.tooltip.init;
    cv.adapters.tooltip.init = (el, options = {}) => {
        if (options.location === "context" && !el.hasAttribute("data-bs-placement")) {
            el.setAttribute("data-bs-placement", "bottom");
        }
        init(el, options);
    };
}
