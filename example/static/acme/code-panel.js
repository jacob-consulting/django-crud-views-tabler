// "Show code" panel (templates/project/code_panel_shell.html): the first time Tabler's collapse opens it, fetch the
// highlighted sources from data-code-url and show the page's own module (data-code-active) first.
(() => {
  const panel = document.getElementById("code-panel");
  if (!panel) return;
  const target = panel.querySelector("[data-code-target]");
  let loaded = false;

  const activate = (file) => {
    const pill = [...target.querySelectorAll("[data-code-file]")].find((a) => a.dataset.codeFile === file);
    if (!pill) return;
    target.querySelectorAll("[data-code-file]").forEach((a) => {
      a.classList.toggle("active", a === pill);
      a.setAttribute("aria-selected", String(a === pill));
    });
    const pane = target.querySelector(pill.getAttribute("href"));
    target.querySelectorAll(".tab-pane").forEach((p) => p.classList.toggle("active", p === pane));
    target.querySelectorAll(".tab-pane").forEach((p) => p.classList.toggle("show", p === pane));
  };

  panel.addEventListener("show.bs.collapse", (event) => {
    if (loaded || event.target !== panel) return;
    loaded = true;
    fetch(panel.dataset.codeUrl, { credentials: "same-origin", headers: { Accept: "text/html" } })
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.text();
      })
      .then((html) => {
        target.innerHTML = html;
        activate(panel.dataset.codeActive);
      })
      .catch(() => {
        loaded = false; // try again on the next open
        target.innerHTML = '<div class="card-body text-danger">The code could not be loaded.</div>';
      });
  });
})();
