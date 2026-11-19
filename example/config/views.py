from functools import cache

from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils.html import strip_tags
from django.views.decorators.cache import cache_control

from .showcode import collect_shell_files, collect_sources_for_app, collect_theme_sources, pygments_css

THEME_PACKAGES = ("django_tabler", "crud_views_tabler")

THEME_GUIDE_URL = "https://django-crud-views.readthedocs.io/en/latest/reference/theme/"
THEME_DOC_URL = "https://django-crud-views-tabler.readthedocs.io/en/latest/theme_internals/"

#: how the theme's files are grouped on the page, in this order
GROUPS = (
    (
        "python",
        "Registration",
        "apps.py registers button classes, label modes and icons; checks.py flags missing icons.",
    ),
    (
        "templates",
        "Templates",
        "Page base and layout overrides. They shadow the stock templates; none renders a button.",
    ),
    (
        "static",
        "CSS and JavaScript",
        "A few CSS fixes and the adapter that hands crud_views Tabler's Bootstrap components.",
    ),
    (
        "settings",
        "Settings",
        "The settings.py lines that switch the theme on; INSTALLED_APPS is shown, and counted, whole for its order.",
    ),
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


def _app_short(label: str, app_label: str) -> str:
    """``sales/templates/sales/x.html`` -> ``sales/x.html``, ``sales/views/orders.py`` -> ``views/orders.py``."""
    return label.removeprefix(f"{app_label}/").removeprefix("templates/")


def code_panel(request, app_label):
    """The "Show code" panel's content for one example app; the label is checked against the app registry."""
    sources = collect_sources_for_app(app_label)
    if not sources:
        raise Http404("No code panel for this app.")
    return render(
        request,
        "project/code_panel.html",
        {
            "files": [{"source": s, "short": _app_short(s.label, app_label)} for s in sources],
            "app_label": app_label,
            "total_lines": sum(s.lines for s in sources),
            "imports_theme": any(name in strip_tags(s.html) for s in sources for name in THEME_PACKAGES),
        },
    )


@cache
def _pygments_css() -> str:
    return pygments_css()


@cache_control(max_age=3600)
def pygments_stylesheet(request):
    """Token colours for the highlighted code, light and dark (config/showcode.py:pygments_css)."""
    return HttpResponse(_pygments_css(), content_type="text/css")
