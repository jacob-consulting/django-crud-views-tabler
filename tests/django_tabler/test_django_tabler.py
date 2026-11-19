import re
import subprocess
import sys
from pathlib import Path

from django.contrib.messages import constants
from django.contrib.messages.storage.base import Message
from django.template import Context, Template
from django.template.loader import render_to_string
from django.test import SimpleTestCase, override_settings
from django.utils.safestring import mark_safe

import django_tabler

PACKAGE = Path(django_tabler.__file__).parent
INCLUDES = PACKAGE / "templates" / "django_tabler" / "includes"


def render_messages(*messages):
    return render_to_string("django_tabler/includes/messages.html", {"messages": list(messages)})


class MessagesIncludeTests(SimpleTestCase):
    def test_levels_map_to_alert_classes(self):
        for level, css in (
            (constants.ERROR, "alert alert-danger"),
            (constants.WARNING, "alert alert-warning"),
            (constants.SUCCESS, "alert alert-success"),
            (constants.INFO, "alert alert-info"),
            (constants.DEBUG, "alert alert-secondary"),
        ):
            with self.subTest(level=level):
                html = render_messages(Message(level, "x"))
                self.assertIn(css, html)
                self.assertIn("<svg", html)

    def test_custom_level_renders_as_info(self):
        self.assertIn("alert alert-info", render_messages(Message(35, "x")))

    def test_body_is_escaped_and_safe_strings_pass(self):
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", render_messages(Message(constants.INFO, "<b>x</b>")))
        self.assertIn("<b>x</b>", render_messages(Message(constants.INFO, mark_safe("<b>x</b>"))))

    def test_extra_tags_reach_the_alert(self):
        html = render_messages(Message(constants.INFO, "x", extra_tags="probe"))
        self.assertRegex(html, r'class="alert [^"]*\bprobe\b')


WITHOUT_CRISPY = """
import sys
sys.modules["crispy_forms"] = None
sys.modules["crispy_bootstrap5"] = None

import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=["django_tabler"],
    TEMPLATES=[{"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True}],
)
django.setup()

from django.contrib.messages import constants
from django.contrib.messages.storage.base import Message
from django.template.loader import render_to_string

import django_tabler.crispy.fields

html = render_to_string("django_tabler/includes/messages.html", {"messages": [Message(constants.INFO, "x")]})
assert "alert-info" in html
"""


class PackageTests(SimpleTestCase):
    def test_package_works_without_crispy_installed(self):
        result = subprocess.run([sys.executable, "-c", WITHOUT_CRISPY], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_package_does_not_reference_crud_views(self):
        for path in PACKAGE.rglob("*"):
            if path.is_file() and path.name != "tests.py" and "__pycache__" not in path.parts:
                with self.subTest(path=path):
                    self.assertIsNone(re.search(r"crud[-_ ]views|cv_", path.read_text(), re.IGNORECASE))

    def test_default_site_name(self):
        self.assertEqual((INCLUDES / "site_name.html").read_text(), "Django Tabler")

    def test_default_head_include_is_empty(self):
        self.assertEqual(re.sub(r"\{#.*?#\}", "", (INCLUDES / "head.html").read_text()).strip(), "")

    def test_default_nav_menu_is_empty(self):
        self.assertEqual((INCLUDES / "nav_menu.html").read_text().strip(), "")

    def test_page_header_actions_wrap_below_the_title_on_phones(self):
        layout = (INCLUDES.parent / "layouts" / "app.html").read_text()
        self.assertRegex(layout, r'<div class="col-12 col-md">\s*\{% block breadcrumb %\}')
        self.assertIn('<div class="col-auto ms-auto d-print-none">', layout)

    def test_nav_menu_is_told_which_navigation_it_renders(self):
        # A project's nav_menu.html can render sections as headings in the sidebar and as dropdowns in the top bar.
        for include, layout in (("navbar.html", "horizontal"), ("sidebar.html", "vertical")):
            with self.subTest(include=include):
                self.assertIn(
                    f'{{% include "django_tabler/includes/nav_menu.html" with nav_layout="{layout}" %}}',
                    (INCLUDES / include).read_text(),
                )


LAYOUT_SWITCH_JS = PACKAGE / "static" / "django_tabler" / "layout-switch.js"


def render_layout_attrs(defaults: str | None = None) -> str:
    """``{% layout_defaults_attrs %}`` with the package's include, or with ``defaults`` as the include's content."""
    if defaults is None:
        return Template("{% load tabler %}{% layout_defaults_attrs %}").render(Context())
    loaders = [
        ("django.template.loaders.locmem.Loader", {"django_tabler/includes/layout_defaults.html": defaults}),
        "django.template.loaders.app_directories.Loader",
    ]
    engine = {"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "OPTIONS": {"loaders": loaders}}
    with override_settings(TEMPLATES=[engine]):
        return Template("{% load tabler %}{% layout_defaults_attrs %}").render(Context())


class LayoutDefaultsTests(SimpleTestCase):
    """A project sets its default layout in django_tabler/includes/layout_defaults.html.

    The user's choice still wins.
    """

    def test_package_default_sets_nothing(self):
        self.assertEqual(render_layout_attrs((INCLUDES / "layout_defaults.html").read_text()), "")
        self.assertIn(
            '<html lang="en"{% layout_defaults_attrs %}>', (PACKAGE / "templates/django_tabler/base.html").read_text()
        )

    def test_project_defaults_become_server_values_and_a_json_attribute(self):
        html = render_layout_attrs('{"navbar-position": "vertical", "navbar-theme": "dark", "sidebar": "default"}')
        # tabler-theme.js reads data-bs-<key> as the server value (localStorage wins over it); Tabler's own default
        # ("sidebar": "default") needs no attribute.
        self.assertIn(' data-bs-navbar-position="vertical"', html)
        self.assertIn(' data-bs-navbar-theme="dark"', html)
        self.assertNotIn("data-bs-sidebar", html)
        self.assertIn(' data-tabler-layout-defaults="{&quot;navbar-position&quot;: &quot;vertical&quot;', html)

    def test_unknown_keys_and_odd_values_are_refused(self):
        for bad in ('{"theme-primary": "green"}', '{"navbar-position": "x\\" onload=1"}', "not json"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                render_layout_attrs(bad)

    def test_switch_reads_the_project_defaults_and_keeps_tablers_as_fallback(self):
        js = LAYOUT_SWITCH_JS.read_text()
        for pair in (
            'layout: "default"',
            '"navbar-position": "horizontal"',
            '"navbar-style": "default"',
            '"navbar-theme": "default"',
            'sidebar: "default"',
        ):
            self.assertIn(pair, js)
        self.assertIn("document.documentElement.dataset.tablerLayoutDefaults", js)
        self.assertIn("const DEFAULTS = { ...TABLER_DEFAULTS, ...projectDefaults() };", js)
        # stored only when it differs from the project default; the attribute only when it differs from Tabler's,
        # since tabler-theme.js removes it for Tabler's default values
        self.assertRegex(js, r"if \(value === DEFAULTS\[key\]\) localStorage\.removeItem")
        self.assertRegex(js, r"if \(value === TABLER_DEFAULTS\[key\]\) document\.documentElement\.removeAttribute")
