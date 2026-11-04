"""Source collector for the "Show code" panel and the "How this is themed" page.

Reads files from disk and highlights them with Pygments. The set of files is fixed here, never taken from a request:
an example app's own code (``collect_app_sources``), the theme app ``src/crud_views_tabler`` plus a whitelist of
``settings.py`` assignments (``collect_theme_sources``), and a line count of ``src/django_tabler``
(``collect_shell_files``). Only text files with a known suffix (``LEXERS``) are read.

The crud pages only carry an empty panel shell (``code_app_label``); its content is fetched from
``/_code/<app_label>/`` when the panel opens (config/views.py:code_panel).
"""

import ast
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

from django.apps import apps
from django.conf import settings
from django.utils.safestring import SafeString, mark_safe
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import CssLexer, HtmlDjangoLexer, JavascriptLexer, PythonLexer

EXAMPLE_DIR = Path(settings.BASE_DIR).resolve()
SRC_DIR = EXAMPLE_DIR.parent / "src"
THEME_DIR = SRC_DIR / "crud_views_tabler"
SHELL_DIR = SRC_DIR / "django_tabler"
SETTINGS_FILE = EXAMPLE_DIR / "config" / "settings.py"

#: an app's Python files shown in the panel, in this order; ``views/*.py`` takes the place of ``views.py``
APP_FILES = ("models.py", "forms.py", "workflow.py", "resources.py", "views.py")

#: the settings.py assignments the theming page shows; nothing else of settings.py is ever read out
THEME_SETTINGS = (
    "INSTALLED_APPS",
    "CRISPY_ALLOWED_TEMPLATE_PACKS",
    "CRISPY_TEMPLATE_PACK",
    "CRUD_VIEWS_EXTENDS",
    "DJANGO_TABLES2_TEMPLATE",
)

#: CSS classes; the colours come from ``pygments_css()``, one light and one dark style scoped by data-bs-theme
FORMATTER = HtmlFormatter()
LIGHT_STYLE = "default"
DARK_STYLE = "github-dark"

LEXERS = {".py": PythonLexer, ".html": HtmlDjangoLexer, ".js": JavascriptLexer, ".css": CssLexer}


class Source(NamedTuple):
    label: str  # e.g. "sales/views/customers.py"
    path: str  # the same path, relative to the repository root
    html: SafeString  # Pygments output
    lines: int


def _lexer(suffix: str):
    return LEXERS[suffix]()


def pygments_css() -> str:
    """The token colours for ``.code-block``: the light style by default, the dark one under Tabler's dark mode."""
    light = ":root:not([data-bs-theme=dark]) .code-block"
    dark = "[data-bs-theme=dark] .code-block"
    parts = []
    for selector, style in ((light, LIGHT_STYLE), (dark, DARK_STYLE)):
        formatter = HtmlFormatter(style=style)
        parts += [formatter.get_background_style_defs(selector), formatter.get_token_style_defs(selector)]
    return "\n".join("\n".join(p) for p in parts) + "\n"


def _count(text: str) -> int:
    return len(text.splitlines())


def _read(path: Path) -> str | None:
    """A file's text, or None for a file that is not UTF-8 text."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


@lru_cache(maxsize=256)
def _highlighted(path: Path, mtime_ns: int) -> tuple[str, int] | None:
    text = _read(path)
    if text is None:
        return None
    return highlight(text, _lexer(path.suffix), FORMATTER), _count(text)


def _sources(paths, label_for) -> list[Source]:
    sources = []
    for path in paths:
        result = _highlighted(path, path.stat().st_mtime_ns)
        if result is not None:
            html, lines = result
            sources.append(Source(label_for(path), path.relative_to(EXAMPLE_DIR.parent).as_posix(), mark_safe(html), lines))
    return sources


def _example_app_dir(label: str) -> Path | None:
    """The directory of an installed app that lives directly in ``example/``, else None."""
    try:
        config = apps.get_app_config(label)
    except LookupError:
        return None
    app_dir = Path(config.path).resolve()
    return app_dir if app_dir.parent == EXAMPLE_DIR else None


def _code_app_dir(label: str) -> Path | None:
    """An example app that gets a code panel: lives in ``example/``, and is not the dashboard."""
    app_dir = _example_app_dir(label)
    return app_dir if app_dir is not None and app_dir.name != "dashboard" else None


def code_app_label(view) -> str | None:
    """The app label of a view's code panel, or None; reads no files."""
    label = type(view).__module__.split(".")[0]
    return label if _code_app_dir(label) is not None else None


def own_module_label(view) -> str:
    """``sales/views/customers.py`` for a view in ``sales.views.customers``: the file the panel opens on."""
    return f"{type(view).__module__.replace('.', '/')}.py"


def collect_sources_for_app(label: str) -> list[Source]:
    """``models.py``, ``forms.py``, ``views.py`` (or ``views/*.py``) and templates of an example app.

    Seed data, tests, admin and the dashboard (not a crud_views app) stay out.
    """
    app_dir = _code_app_dir(label)
    if app_dir is None:
        return []
    paths = []
    for name in APP_FILES:
        if (app_dir / name).is_file():
            paths.append(app_dir / name)
        elif name == "views.py" and (app_dir / "views").is_dir():
            paths += sorted(p for p in (app_dir / "views").glob("*.py") if p.name != "__init__.py")
    paths += sorted((app_dir / "templates").rglob("*.html"))
    return _sources(paths, lambda p: f"{label}/{p.relative_to(app_dir).as_posix()}")


def collect_app_sources(view) -> list[Source]:
    """The app code behind a crud_views page; the view's own module comes first."""
    own = own_module_label(view)
    label = code_app_label(view)
    return sorted(collect_sources_for_app(label), key=lambda s: s.label != own) if label else []


def _assigned_names(node) -> list[str]:
    """The plain names a top-level ``x = ...``, ``x: T = ...`` or ``x += ...`` statement assigns."""
    if isinstance(node, ast.Assign):
        targets = node.targets
    elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
        targets = [node.target]
    else:
        return []
    return [t.id for t in targets if isinstance(t, ast.Name)]


def settings_excerpt(text: str) -> list[str]:
    """The THEME_SETTINGS statements of a settings module (found with ``ast``), in file order, one string each."""
    lines = text.splitlines()
    return [
        "\n".join(lines[node.lineno - 1 : node.end_lineno])
        for node in ast.parse(text).body
        if any(name in THEME_SETTINGS for name in _assigned_names(node))
    ]


def _settings_excerpt() -> Source:
    blocks = settings_excerpt(SETTINGS_FILE.read_text(encoding="utf-8"))
    excerpt = "\n\n".join(blocks) + "\n"
    return Source(
        "example/config/settings.py (excerpt)",
        SETTINGS_FILE.relative_to(EXAMPLE_DIR.parent).as_posix(),
        mark_safe(highlight(excerpt, PythonLexer(), FORMATTER)),
        sum(_count(b) for b in blocks),
    )


def _package_files(root: Path) -> list[Path]:
    """Every non-empty text file (a ``LEXERS`` suffix) of a package, without tests and caches."""
    return sorted(
        p
        for p in root.rglob("*")
        if p.is_file()
        and "__pycache__" not in p.parts
        and "tests" not in p.parts
        and not p.name.startswith("test")
        and p.suffix in LEXERS
        and p.stat().st_size > 0
    )


def collect_theme_sources() -> list[Source]:
    """The whole crud_views theme: every file of ``src/crud_views_tabler`` plus the settings that switch it on."""
    return _sources(_package_files(THEME_DIR), lambda p: p.relative_to(SRC_DIR).as_posix()) + [_settings_excerpt()]


class FileInfo(NamedTuple):
    label: str
    lines: int


def collect_shell_files() -> list[FileInfo]:
    """``src/django_tabler`` (page shell, icons, crispy pack) as a file list with line counts, not highlighted."""
    files = ((p, _read(p)) for p in _package_files(SHELL_DIR))
    return [FileInfo(p.relative_to(SRC_DIR).as_posix(), _count(text)) for p, text in files if text is not None]
