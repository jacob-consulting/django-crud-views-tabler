from django.shortcuts import render

from .showcode import collect_shell_files, collect_theme_sources

THEME_GUIDE_URL = "https://django-crud-views.readthedocs.io/en/latest/reference/theme/"
THEME_DOC_URL = "https://github.com/alexander-jacob/tabler-test/blob/main/docs/crud_views_tabler.md"

#: how the theme's files are grouped on the page, in this order
GROUPS = (
    ("python", "Registration", "apps.py registers button classes, label modes and icons; checks.py flags missing icons."),
    ("templates", "Templates", "Page base and layout overrides. They shadow the stock templates; none renders a button."),
    ("static", "CSS and JavaScript", "A few CSS fixes and the adapter that hands crud_views Tabler's Bootstrap components."),
    ("settings", "Settings", "The settings.py lines that switch the theme on; INSTALLED_APPS is shown, and counted, whole for its order."),
)


def _group(label: str) -> str:
    if label.startswith("example/"):
        return "settings"
    if "/templates/" in label:
        return "templates"
    if "/static/" in label:
        return "static"
    return "python"


def _short(label: str) -> str:
    for prefix in ("crud_views_tabler/templates/", "crud_views_tabler/static/crud_views_tabler/", "crud_views_tabler/"):
        if label.startswith(prefix):
            return label.removeprefix(prefix)
    return label


def theming(request):
    """'How this is themed': every file of the crud_views theme, with line counts computed now."""
    sources = collect_theme_sources()
    groups = []
    for key, title, text in GROUPS:
        members = [s for s in sources if _group(s.label) == key]
        groups.append(
            {
                "key": key,
                "title": title,
                "text": text,
                "sources": members,
                "lines": sum(s.lines for s in members),
                # the file list drops the package and templates/static prefixes the group heading already says
                "short": [(s, _short(s.label)) for s in members],
            }
        )
    shell = collect_shell_files()
    return render(
        request,
        "project/theming.html",
        {
            "sources": sources,
            "groups": groups,
            "total_files": len(sources),
            "total_lines": sum(s.lines for s in sources),
            "shell_files": shell,
            "shell_lines": sum(f.lines for f in shell),
            "theme_guide_url": THEME_GUIDE_URL,
            "theme_doc_url": THEME_DOC_URL,
        },
    )
