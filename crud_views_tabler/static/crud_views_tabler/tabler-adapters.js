// Tabler's bundle exposes Bootstrap's components on window.tabler, not window.bootstrap.
// crud_views calls Bootstrap only through cv.adapters (adapters.js); point them at Tabler.
// The namespace is resolved on every adapter call, so tabler.min.js may load deferred.
Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler));
