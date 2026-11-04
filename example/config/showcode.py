"""Source collector for the "Show code" panel and the "How this is themed" page.

Reads files from disk and highlights them with Pygments. The set of files is fixed here, never taken from a request:
an example app's own code (``collect_app_sources``), the theme app ``src/crud_views_tabler`` plus a whitelist of
``settings.py`` assignments (``collect_theme_sources``), and a line count of ``src/django_tabler``
(``collect_shell_files``).
"""

import ast
import re
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

#: dark code on a fixed dark background, so it reads the same in Tabler's light and dark mode
FORMATTER = HtmlFormatter(noclasses=True, style="github-dark", nobackground=True)

LEXERS = {".py": PythonLexer, ".html": HtmlDjangoLexer, ".js": JavascriptLexer, ".css": CssLexer}


class Source(NamedTuple):
    label: str  # e.g. "sales/views/customers.py"
    path: str  # the same path, relative to the repository root
    html: SafeString  # Pygments output
    lines: int


def _lexer(suffix: str):
    return LEXERS.get(suffix, PythonLexer)()


def _count(text: str) -> int:
    return len(text.splitlines())


@lru_cache(maxsize=256)
def _highlighted(path: Path, mtime_ns: int) -> tuple[str, int]:
    text = path.read_text(encoding="utf-8")
    return highlight(text, _lexer(path.suffix), FORMATTER), _count(text)


def _source(path: Path, label: str) -> Source:
    html, lines = _highlighted(path, path.stat().st_mtime_ns)
    return Source(label, path.relative_to(EXAMPLE_DIR.parent).as_posix(), mark_safe(html), lines)


def _example_app_dir(label: str) -> Path | None:
    """The directory of an installed app that lives directly in ``example/``, else None."""
    try:
        config = apps.get_app_config(label)
    except LookupError:
        return None
    app_dir = Path(config.path).resolve()
    return app_dir if app_dir.parent == EXAMPLE_DIR else None


def collect_sources_for_app(label: str) -> list[Source]:
    """``models.py``, ``forms.py``, ``views.py`` (or ``views/*.py``) and templates of an example app.

    Seed data, tests, admin and the dashboard (not a crud_views app) stay out.
    """
    app_dir = _example_app_dir(label)
    if app_dir is None or app_dir.name == "dashboard":
        return []
    paths = []
    for name in APP_FILES:
        if (app_dir / name).is_file():
            paths.append(app_dir / name)
        elif name == "views.py" and (app_dir / "views").is_dir():
            paths += sorted(p for p in (app_dir / "views").glob("*.py") if p.name != "__init__.py")
    paths += sorted((app_dir / "templates").rglob("*.html"))
    return [_source(p, f"{label}/{p.relative_to(app_dir).as_posix()}") for p in paths]


def collect_app_sources(view) -> list[Source]:
    """The app code behind a crud_views page; the view's own module comes first."""
    module = type(view).__module__
    sources = collect_sources_for_app(module.split(".")[0])
    own = f"{module.replace('.', '/')}.py"
    return sorted(sources, key=lambda s: s.label != own)


def without_code_panel(html: str) -> str:
    """A page without its "Show code" panel, for tests that assert some text is *not* on the page: the panel
    shows the app's source, which mentions every label the app can render."""
    return re.sub(r"<!-- code-panel -->.*?<!-- /code-panel -->", "", html, flags=re.S)


def _settings_excerpt() -> Source:
    """Only the THEME_SETTINGS assignments of settings.py (found with ``ast``), in file order."""
    text = SETTINGS_FILE.read_text(encoding="utf-8")
    lines = text.splitlines()
    blocks = []
    for node in ast.parse(text).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id in THEME_SETTINGS for t in node.targets
        ):
            blocks.append("\n".join(lines[node.lineno - 1 : node.end_lineno]))
    excerpt = "\n\n".join(blocks) + "\n"
    return Source(
        "example/config/settings.py (excerpt)",
        SETTINGS_FILE.relative_to(EXAMPLE_DIR.parent).as_posix(),
        mark_safe(highlight(excerpt, PythonLexer(), FORMATTER)),
        sum(_count(b) for b in blocks),
    )


def _package_files(root: Path) -> list[Path]:
    """Every non-empty file of a package, without tests and caches."""
    return sorted(
        p
        for p in root.rglob("*")
        if p.is_file()
        and "__pycache__" not in p.parts
        and "tests" not in p.parts
        and not p.name.startswith("test")
        and p.stat().st_size > 0
    )


def collect_theme_sources() -> list[Source]:
    """The whole crud_views theme: every file of ``src/crud_views_tabler`` plus the settings that switch it on."""
    sources = [_source(p, p.relative_to(SRC_DIR).as_posix()) for p in _package_files(THEME_DIR)]
    return sources + [_settings_excerpt()]


class FileInfo(NamedTuple):
    label: str
    lines: int


def collect_shell_files() -> list[FileInfo]:
    """``src/django_tabler`` (page shell, icons, crispy pack) as a file list with line counts, not highlighted."""
    return [
        FileInfo(p.relative_to(SRC_DIR).as_posix(), _count(p.read_text(encoding="utf-8", errors="replace")))
        for p in _package_files(SHELL_DIR)
    ]
