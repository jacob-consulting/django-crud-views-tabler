// The layout switch: writes the settings Tabler's theme script reads on the next
// page load (tabler-<key> in localStorage) and applies them to <html> right away.
// A project's default layout (django_tabler/includes/layout_defaults.html) arrives
// as data-tabler-layout-defaults on <html>, plus a data-bs-<key> server value that
// tabler-theme.js uses when nothing is stored.
(function () {
  // Tabler's own defaults (tabler-theme.js): it removes data-bs-<key> for these values.
  const TABLER_DEFAULTS = {
    layout: "default",
    "navbar-position": "horizontal",
    "navbar-style": "default",
    "navbar-theme": "default",
    sidebar: "default",
  };

  function projectDefaults() {
    try {
      return JSON.parse(document.documentElement.dataset.tablerLayoutDefaults || "{}");
    } catch {
      return {};
    }
  }

  const DEFAULTS = { ...TABLER_DEFAULTS, ...projectDefaults() };
  const buttons = document.querySelectorAll("[data-layout-settings]");

  function settingsOf(button) {
    return JSON.parse(button.dataset.layoutSettings);
  }

  function current(key) {
    return document.documentElement.getAttribute("data-bs-" + key) ?? TABLER_DEFAULTS[key];
  }

  function store(key, value) {
    try {
      if (value === DEFAULTS[key]) localStorage.removeItem("tabler-" + key);
      else localStorage.setItem("tabler-" + key, value);
    } catch {
      // Storage can be blocked; the choice then lasts for this page only.
    }
  }

  function apply(key, value) {
    if (value === TABLER_DEFAULTS[key]) document.documentElement.removeAttribute("data-bs-" + key);
    else document.documentElement.setAttribute("data-bs-" + key, value);
  }

  function refresh() {
    for (const button of buttons) {
      const active = Object.entries(settingsOf(button)).every(([key, value]) => current(key) === value);
      button.classList.toggle("btn-primary", active);
      button.setAttribute("aria-pressed", active);
    }
  }

  for (const button of buttons) {
    button.addEventListener("click", () => {
      for (const [key, value] of Object.entries(settingsOf(button))) {
        store(key, value);
        apply(key, value);
      }
      refresh();
      // Charts size themselves from the window; the content area has just changed width.
      window.dispatchEvent(new Event("resize"));
    });
  }
  refresh();
})();
