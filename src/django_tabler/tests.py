import re
from pathlib import Path

from django.contrib.messages import constants
from django.contrib.messages.storage.base import Message
from django.template.loader import render_to_string
from django.test import SimpleTestCase
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


class PackageTests(SimpleTestCase):
    def test_package_does_not_reference_crud_views(self):
        for path in PACKAGE.rglob("*"):
            if path.is_file() and path.name != "tests.py" and "__pycache__" not in path.parts:
                with self.subTest(path=path):
                    self.assertIsNone(re.search(r"crud[-_ ]views|cv_", path.read_text(), re.IGNORECASE))

    def test_default_site_name(self):
        self.assertEqual((INCLUDES / "site_name.html").read_text(), "Django Tabler")

    def test_default_nav_menu_is_empty(self):
        self.assertEqual((INCLUDES / "nav_menu.html").read_text().strip(), "")
