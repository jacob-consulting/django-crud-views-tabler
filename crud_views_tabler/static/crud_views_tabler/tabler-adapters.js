// Tabler's bundle exposes Bootstrap's components on window.tabler, not window.bootstrap.
// crud_views calls Bootstrap only through cv.adapters (adapters.js); point them at Tabler.
// The namespace is resolved on every adapter call, so tabler.min.js may load deferred.
Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler));
// Toolbar tooltips open below the buttons, so they do not cover the page header; the rest keep Tabler's default.
cv.adapters.tooltip.init = (el, {location} = {}) => {
    const Tooltip = globalThis.tabler?.Tooltip;
    if (!Tooltip) {
        return;
    }
    Tooltip.getOrCreateInstance(el, {placement: location === "context" ? "bottom" : "top"});
};
