import os
import re
import subprocess
import sys
from html.parser import HTMLParser
from types import SimpleNamespace
from pathlib import Path
from unittest import mock

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.messages import constants
from django.contrib.messages.storage.base import Message
from django.core.checks import run_checks
from django.core.management import call_command
from django.template import Context, Template, TemplateDoesNotExist, engines
from django.template.loader import get_template, render_to_string
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from crud_views.lib.button_classes import _get_default_button_classes, get_button_classes
from crud_views.lib.crispy import CrispyDeleteForm
from crud_views.lib.icons import DEFAULT_ICONS
from crud_views.lib.icons import render_icon as cv_render_icon
from crud_views.lib.view.label_mode import LABEL_MODES
from crud_views.lib.view.variant import VARIANTS
import crud_views_tabler
from crud_views_tabler.buttons import TABLER_BUTTON_CLASSES
from crud_views_tabler.icons import TABLER_ICONS, render
from django_tabler.icons import ICONS, svg
from tests.crud_views_tabler.testapp.models import Customer
from tests.crud_views_tabler.testapp.views import CustomerDeleteView, CustomerListView


class ProbeWidget(forms.TextInput):
    class Media:
        js = ("probe/probe.js",)
        css = {"all": ("probe/probe.css",)}


class ProbeForm(forms.Form):
    x = forms.CharField(widget=ProbeWidget)


class TablerIconTests(SimpleTestCase):
    def test_svg_for_a_tabler_name(self):
        html = svg("eye", "icon-sm")
        self.assertIn('class="icon icon-sm"', html)
        self.assertIn("<path", html)
        self.assertIn('aria-hidden="true"', html)

    def test_svg_without_extra_classes_has_no_trailing_space(self):
        self.assertIn('class="icon"', svg("eye"))

    def test_unknown_or_empty_name_renders_nothing(self):
        self.assertEqual(svg("not-an-icon"), "")
        self.assertEqual(svg(None), "")
        self.assertEqual(render("not-an-icon", css="", config={}), "")

    def test_css_is_escaped(self):
        self.assertIn('class="icon a&quot; onload=&quot;x"', svg("eye", 'a" onload="x'))

    def test_renderer_matches_svg(self):
        self.assertEqual(render("trash", css="icon-sm", config={"renderer": "x"}), svg("trash", "icon-sm"))

    def test_every_upstream_icon_name_is_mapped(self):
        self.assertEqual(set(TABLER_ICONS), set(DEFAULT_ICONS))
        for name, value in TABLER_ICONS.items():
            prefix, tabler_name = value.split(":", 1)
            self.assertEqual(prefix, "tabler", name)
            self.assertIn(tabler_name, ICONS, f"{name} -> {value} has no path in ICONS")

    def test_registry_renders_tabler_svg(self):
        self.assertEqual(cv_render_icon("detail"), svg("eye"))
        self.assertEqual(cv_render_icon("tabler:building-store", css="icon-sm"), svg("building-store", "icon-sm"))

    @override_settings(CRUD_VIEWS_ICONS={"detail": "far:eye"})
    def test_project_setting_wins_over_the_theme(self):
        self.assertEqual(cv_render_icon("detail"), '<i class="fa-regular fa-eye" aria-hidden="true"></i>')


class ButtonClassTests(SimpleTestCase):
    def test_theme_classes_are_registered(self):
        resolved = get_button_classes()
        for key, classes in TABLER_BUTTON_CLASSES.items():
            self.assertEqual(resolved[key], classes, key)

    def test_every_theme_key_is_an_upstream_key(self):
        # A label-mode key (location:variant:mode, #209) extends an upstream action key.
        for key in TABLER_BUTTON_CLASSES:
            base, _, mode = key.rpartition(":") if key.count(":") == 2 else (key, "", "")
            self.assertIn(base, _get_default_button_classes(), key)
            if mode:
                self.assertIn(mode, LABEL_MODES, key)

    def test_btn_icon_only_on_icon_only_buttons(self):
        # btn-icon squares a button; a labelled button (label or both) must not get it.
        for key, classes in TABLER_BUTTON_CLASSES.items():
            if key.split(":")[0] in ("context", "list", "card") and key.split(":")[1] in VARIANTS:
                self.assertEqual("btn-icon" in classes.split(), key.endswith(":icon"), key)

    def test_table_values(self):
        expected = {
            "context:primary": "btn btn-primary",
            "context:secondary": "btn",
            "context:tertiary": "btn",
            "context:danger": "btn btn-outline-danger",
            "list:primary": "btn btn-sm btn-ghost-primary",
            "list:secondary": "btn btn-sm btn-ghost-secondary",
            "list:tertiary": "btn btn-sm btn-ghost-secondary",
            "list:danger": "btn btn-sm btn-ghost-danger",
            "card:primary": "btn btn-sm btn-primary",
            "card:secondary": "btn btn-sm",
            "card:tertiary": "btn btn-sm btn-ghost-secondary",
            "card:danger": "btn btn-sm btn-ghost-danger",
            "context:primary:icon": "btn btn-primary btn-icon",
            "context:secondary:icon": "btn btn-icon",
            "context:tertiary:icon": "btn btn-icon",
            "context:danger:icon": "btn btn-icon btn-outline-danger",
            "list:primary:icon": "btn btn-sm btn-icon btn-ghost-primary",
            "list:secondary:icon": "btn btn-sm btn-icon btn-ghost-secondary",
            "list:tertiary:icon": "btn btn-sm btn-icon btn-ghost-secondary",
            "list:danger:icon": "btn btn-sm btn-icon btn-ghost-danger",
            "card:primary:icon": "btn btn-sm btn-icon btn-primary",
            "card:secondary:icon": "btn btn-sm btn-icon",
            "card:tertiary:icon": "btn btn-sm btn-icon btn-ghost-secondary",
            "card:danger:icon": "btn btn-sm btn-icon btn-ghost-danger",
            "context:container": "btn-list",
            "list:container": "btn-list flex-nowrap justify-content-end gap-1",
            "card:container": "btn-list",
            "context:menu-toggle": "btn btn-icon",
            "list:menu-toggle": "btn btn-sm btn-icon btn-ghost-secondary",
            "card:menu-toggle": "btn btn-sm btn-icon",
            "card:root": "card",
            "context:menu-wrapper": "dropdown",
            "list:menu-wrapper": "dropdown",
            "form:delete": "btn btn-danger",
            "form:actions": "d-flex flex-wrap gap-2",
            "form:filter-actions": "d-flex flex-wrap gap-1",
            "alert:dismissible": "alert-dismissible fade show",
            "alert:close": "btn-close",
            "card-order:toggle": "btn btn-icon",
            "card-order:container": "btn-group",
            "formset:control": "btn btn-icon",
            "formset:control-danger": "btn btn-icon btn-danger",
            "conditional:legend": "cv-tabler-section-legend",
            "formset:legend": "cv-tabler-section-legend",
            **{f"workflow:badge-{colour}": f"badge bg-{colour}-lt" for colour in
               ("primary", "secondary", "success", "danger", "warning", "info", "light", "dark")},
            **{f"workflow:transition-{colour}": f"btn btn-{colour}" for colour in
               ("primary", "secondary", "success", "danger", "warning", "info", "light", "dark")},
            "workflow:history-table": "table table-vcenter",
            "manage:badge-model": "badge bg-secondary-lt",
            "manage:badge-resource": "badge bg-azure-lt",
            "manage:badge-objects": "badge badge-outline text-secondary",
            "manage:badge-permission": "badge bg-blue-lt",
            "manage:badge-group": "badge bg-pink-lt",
            "manage:badge-policy-global": "badge bg-green-lt",
            "manage:badge-policy-strict": "badge bg-green-lt",
            "manage:badge-policy-na": "badge bg-secondary-lt",
            "manage:help": "btn btn-sm",
            **{f"manage:trace-{state}": "badge bg-green-lt" for state in ("allowed", "passed")},
            "manage:trace-denied": "badge bg-red-lt",
            **{f"manage:trace-{state}": "badge bg-yellow-lt" for state in
               ("not-found", "login-redirect", "error", "no-such-route", "not-evaluated")},
            **{f"manage:trace-{state}": "badge bg-secondary-lt" for state in ("skipped", "not-reached")},
        }
        self.assertEqual(TABLER_BUTTON_CLASSES, expected)

    @override_settings(CRUD_VIEWS_BUTTON_CLASSES={"list:danger": "x-danger"})
    def test_project_setting_wins_over_the_theme_classes(self):
        self.assertEqual(get_button_classes()["list:danger"], "x-danger")


class ThemeRenderingTests(TestCase):
    """Renders the test app's customers ViewSet through the theme's templates."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser("root", "root@example.com", "s3cret-pass")
        Customer.objects.bulk_create(Customer(name=f"Customer {i:02}", revenue=i) for i in range(15))
        cls.customer = Customer.objects.get(name="Customer 03")

    def setUp(self):
        self.client.force_login(self.admin)

    @staticmethod
    def tag(html, key):
        """The first opening <a> or <button> tag with cv-key=key."""
        return re.search(rf'<(?:a|button)\b[^>]*\bcv-key="{key}"[^>]*>', html).group(0)

    def test_system_checks_pass(self):
        call_command("check", "--fail-level", "WARNING")

    # ViewSet Navigation (PR #383): the owner header at the top of the page header, the view's title row below the tabs
    def detail_html(self):
        return self.client.get(reverse("customer-detail", kwargs={"pk": self.customer.pk})).content.decode()

    def test_bar_page_builds_the_owner_header(self):
        html = self.detail_html()
        header = html[html.index('class="page-header') : html.index('class="page-body')]
        order = [
            header.index('class="breadcrumb'),
            header.index("<h1"),
            header.index('class="cv-tabler-navbar'),
            header.index("<h2"),
            header.index('cv-key="update"'),
        ]
        self.assertEqual(order, sorted(order))
        self.assertRegex(header, r'<h1 class="page-title[^"]*">\s*Customer 03\s*</h1>')
        self.assertEqual(header.count('<ol class="breadcrumb'), 1)
        self.assertNotIn('class="cv-navbar ', html)  # the full wrapper tag is not used
        self.assertIn('aria-label="Sections for Customer 03"', header)
        self.assertRegex(header, r'class="nav-link[^"]* active" href="[^"]+" aria-current="true"')

    def test_bar_page_title_names_the_owner(self):
        self.assertRegex(self.detail_html(), r"<title>[^<]*· Customer 03 · ")

    def test_owner_icon_is_a_tabler_svg(self):
        html = self.detail_html()
        header = html[html.index('class="page-header') : html.index('class="page-body')]
        owner = header[header.index('class="avatar') : header.index("</h1>")]
        tabs_start = header.index('class="cv-tabler-navbar')
        tabs = header[tabs_start : header.index("</nav>", tabs_start)]
        self.assertIn("<svg", owner)
        self.assertIn("<svg", tabs)
        self.assertNotIn("fa-", owner + tabs)

    def test_emptying_the_navbar_block_drops_only_the_tabs(self):
        # docs/crud_views_tabler.md: a project drops the tabs by overriding the cv_navbar block; the owner row stays
        response = self.client.get(reverse("customer-detail", kwargs={"pk": self.customer.pk}))
        source = '{% extends "crud_views_tabler/page.html" %}{% block cv_navbar %}{% endblock %}'
        html = engines["django"].from_string(source).render(response.context_data, response.wsgi_request)
        self.assertNotIn("cv-tabler-navbar", html)
        self.assertNotIn('<nav aria-label="Sections', html)
        self.assertIn("<h1", html)

    def test_page_without_navbar_keeps_todays_header(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        self.assertNotIn("cv-tabler-navbar", html)
        self.assertNotIn("<h1", html)
        header = html[html.index('class="page-header') : html.index('class="page-body')]
        self.assertLess(header.index('class="breadcrumb'), header.index("<h2"))

    def test_list_uses_tabler_table_and_icons(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        self.assertIn("table table-vcenter card-table", html)
        self.assertIn('class="table-sort"', html)
        self.assertIn("Showing 1–10 of 15", html)
        self.assertIn('cv-key="delete"', html)
        self.assertIn("btn-ghost-danger", html)
        self.assertNotIn("fa-regular", html)
        self.assertNotIn("fa-solid", html)
        self.assertNotIn("<i class=", html)  # every icon on the page is a Tabler SVG
        self.assertIn(svg("building-store"), html)  # the ViewSet header icon, tabler:building-store

    def test_table_pagination_uses_the_semantic_arrows(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        footer = html[html.index('class="pagination'):]
        self.assertIn(str(svg("chevron-right")), footer[:2000])
        with override_settings(CRUD_VIEWS_ICONS={"page-next": "tabler:arrow-left"}):
            html = self.client.get(reverse("customer-list")).content.decode()
        self.assertIn(str(svg("arrow-left")), html[html.index('class="pagination'):][:2000])

    def test_table_pagination_matches_upstream_accessibility(self):
        # upstream Phase 05 (pagination parity): a labelled <nav> landmark, the current page as a non-link, the
        # ellipsis disabled; the hidden labels use the pagination:hidden-label class key
        page = self.client.get(reverse("customer-list")).content.decode()
        nav = re.search(r'<nav class="ms-auto" aria-label="pagination">.*?</nav>', page, re.S).group(0)
        self.assertRegex(nav, r'<li class="page-item active" aria-current="page"><span class="page-link">1</span>')
        self.assertIn('<span class="visually-hidden">next</span>', nav)
        self.assertNotRegex(nav, r'<a class="page-link"\s*>')  # every link-less item says it is disabled

    def test_disabled_action_renders_a_tabler_icon(self):
        viewer = get_user_model().objects.create_user("viewer", password="viewer-pass")
        viewer.user_permissions.add(Permission.objects.get(codename="view_customer", content_type__app_label="testapp"))
        self.client.force_login(viewer)
        with mock.patch.object(CustomerDeleteView, "cv_inaccessible_actions", "disable"):
            html = self.client.get(reverse("customer-list")).content.decode()
        button = re.search(r'<button[^>]*data-cv-disabled="permission"[^>]*>.*?</button>', html, re.S)
        self.assertIsNotNone(button)
        self.assertIn('class="btn btn-sm btn-icon btn-ghost-danger"', button.group(0))
        self.assertIn("<svg", button.group(0))
        self.assertNotIn("<i class=", button.group(0))

    def test_sorted_column_is_marked(self):
        html = self.client.get(reverse("customer-list"), {"sort": "-revenue"}).content.decode()
        self.assertIn('aria-sort="descending"', html)
        self.assertIn('class="table-sort desc"', html)
        self.assertLess(html.index("Customer 14"), html.index("Customer 13"))

    def test_scripts_use_the_tabler_adapter_without_jquery(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        self.assertNotIn("jquery", html.lower())
        self.assertNotIn("bootstrap-shim", html)
        core = html.index("crud_views/js/adapters.js")
        theme = html.index("crud_views_tabler/tabler-adapters.js")
        self.assertLess(core, theme)
        self.assertIn("crud_views/js/modal.js", html)

    def test_tooltip_adapter_places_toolbar_tooltips_below(self):
        from django.contrib.staticfiles import finders
        with open(finders.find("crud_views_tabler/tabler-adapters.js"), encoding="utf-8") as f:
            source = f.read()
        self.assertIn("cv.bootstrapAdapters(() => globalThis.tabler)", source)
        self.assertIn("cv.adapters.tooltip.init", source)
        self.assertIn('location === "context"', source)
        self.assertIn('setAttribute("data-bs-placement", "bottom")', source)

    def test_upstream_adapter_set_includes_tab_and_theme_takes_all_of_it(self):
        # crud_views/js/adapters.js's bootstrapAdapters returns a `tab:` entry using component(ns, "Tab"), which
        # the object-detail tabs.js initialises through (#328); the theme assigns the whole set, so no tab shim.
        from django.contrib.staticfiles import finders
        with open(finders.find("crud_views/js/adapters.js"), encoding="utf-8") as f:
            core = f.read()
        self.assertRegex(core, r'tab: \{\s*init\(el\) \{ component\(ns, "Tab"\)')
        with open(finders.find("crud_views_tabler/tabler-adapters.js"), encoding="utf-8") as f:
            source = f.read()
        self.assertIn("Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler))", source)
        self.assertNotRegex(source, r"cv\.adapters\.tab\b")

    def test_tooltip_adapter_wraps_upstream_init(self):
        # crud_views' init guards Bootstrap 5.3 tooltip transitions that outlive dispose() (06.8); the theme must
        # delegate to it rather than call Tooltip.getOrCreateInstance itself, or it silently drops that guard.
        from django.contrib.staticfiles import finders
        with open(finders.find("crud_views_tabler/tabler-adapters.js"), encoding="utf-8") as f:
            source = f.read()
        self.assertIn("const init = cv.adapters.tooltip.init;", source)
        self.assertIn("init(el, options);", source)
        self.assertNotIn("getOrCreateInstance", source)

    def test_tooltip_adapter_keeps_upstream_lifecycle(self):
        # Only init is replaced, so crud_views' hide(el) / dispose(el) (#205) keep resolving tabler.Tooltip.
        from django.contrib.staticfiles import finders
        with open(finders.find("crud_views_tabler/tabler-adapters.js"), encoding="utf-8") as f:
            source = f.read()
        self.assertNotRegex(source, r"cv\.adapters\.tooltip\s*=")
        self.assertNotIn("cv.adapters.tooltip.hide", source)
        self.assertNotIn("cv.adapters.tooltip.dispose", source)
        with open(finders.find("crud_views/js/adapters.js"), encoding="utf-8") as f:
            core = f.read()
        self.assertIn("hide(el)", core)
        self.assertIn("dispose(el)", core)

    def test_form_page_wraps_form_in_card(self):
        html = self.client.get(reverse("customer-create")).content.decode()
        self.assertIn('<div class="card"><div class="card-body">', html)
        self.assertIn('class="cv-form"', html)

    def test_modal_form_has_no_card(self):
        html = self.client.get(reverse("customer-create"), headers={"X-CV-Modal": "true"}).content.decode()
        self.assertIn('class="cv-form"', html)
        self.assertNotIn('<div class="card">', html)

    def test_form_pages_frame_through_upstream_content_templates(self):
        # upstream #239: the theme overrides only the frame, not the form templates
        self.assertIn("crud_views_tabler", get_template("crud_views/snippets/form_frame.html").origin.name)
        for name in ("view_create", "view_update", "view_delete", "view_custom_form"):
            template = f"crud_views/{name}.content.html"
            self.assertNotIn("crud_views_tabler", get_template(template).origin.name, template)

    def test_alerts_go_through_the_theme_frame_only(self):
        # upstream #250: every alert renders through tags/alert.html; the theme overrides that frame and nothing else
        self.assertIn("crud_views_tabler", get_template("crud_views/tags/alert.html").origin.name)
        for name in ("tags/messages.html", "snippets/delete/protection_errors.html",
                     "snippets/delete/related_objects.html", "snippets/alert/text.html", "snippets/alert/list.html"):
            self.assertNotIn("crud_views_tabler", get_template(f"crud_views/{name}").origin.name, name)

    def test_protection_errors_render_as_tabler_alert(self):
        html = render_to_string(
            "crud_views/snippets/delete/protection_errors.html", {"delete_protection_errors": ["Has open orders"]}
        )
        self.assertIn('class="alert alert-danger"', html)
        self.assertIn(f'<div class="alert-icon">{svg("alert-circle", "alert-icon")}</div>', html)
        self.assertIn('<h4 class="alert-heading">This object cannot be deleted:</h4>', html)
        self.assertRegex(html, r'<div class="alert-description">\s*<ul[^>]*>\s*<li>Has open orders</li>')
        self.assertNotIn("btn-close", html)

    def test_related_objects_alerts_get_the_tabler_layout(self):
        html = render_to_string(
            "crud_views/snippets/delete/related_objects.html",
            {"has_protected_objects": True, "protected_objects": ["Order 7"], "related_summary": {"order": 2},
             "related_summary_items": ["order: 2"],
             "related_objects": []},
        )
        self.assertEqual(html.count('<div class="alert-icon">'), 2)
        self.assertEqual(html.count('class="alert-heading"'), 2)
        self.assertNotIn("Details about the related objects to be deleted:", html)
        self.assertIn(str(svg("alert-triangle", "alert-icon")), html)  # warning
        self.assertIn("<li>order: 2</li>", html)

    def test_create_and_update_post_multipart(self):
        # upstream #236: without the enctype a FileField arrives empty
        for url in (reverse("customer-create"), reverse("customer-update", args=[self.customer.pk])):
            html = self.client.get(url).content.decode()
            form = re.search(r'<form class="cv-form"[^>]*>', html).group(0)
            self.assertIn('enctype="multipart/form-data"', form, url)

    def test_create_and_update_emit_widget_media_once(self):
        # upstream #191: crispy already renders form.media; the content template must not add it again
        request = RequestFactory().get("/")
        for template in ("crud_views/view_create.content.html", "crud_views/view_update.content.html"):
            html = render_to_string(template, {"form": ProbeForm(), "request": request, "view": None}, request=request)
            self.assertEqual(html.count("probe/probe.js"), 1, template)
            self.assertEqual(html.count("probe/probe.css"), 1, template)

    def test_messages_render_as_tabler_alerts(self):
        url = reverse("customer-delete", args=[self.customer.pk])
        html = self.client.post(url, {"confirm": "on", "delete": "Delete"}, follow=True).content.decode()
        alert = re.search(r'<div class="alert alert-success[^"]*"[^>]*>.*?</div>\s*</div>', html, re.S).group(0)
        self.assertIn("alert-dismissible", alert)
        self.assertIn('<div class="alert-icon">', alert)
        self.assertIn(str(svg("check", "alert-icon")), alert)
        self.assertIn("<div>Deleted »Customer 03«", alert)  # no heading: the text sits in a plain div
        self.assertNotIn("alert-heading", alert)

    def test_delete_modal_partial_has_no_card_and_a_danger_button(self):
        url = reverse("customer-delete", args=[self.customer.pk])
        html = self.client.get(url, headers={"X-CV-Modal": "true"}).content.decode()
        self.assertIn('class="modal-header"', html)
        self.assertNotIn('<div class="card">', html)
        self.assertIn("btn btn-danger", html)
        self.assertIn("data-cv-modal-dismiss", html)
        self.assertNotIn("data-bs-dismiss", html)

    def test_delete_form_is_the_stock_crispy_delete_form(self):
        self.assertIs(CustomerDeleteView.form_class, CrispyDeleteForm)
        html = self.client.get(reverse("customer-delete", args=[self.customer.pk])).content.decode()
        self.assertRegex(html, r'<button type="submit" name="delete"[^>]*class="btn btn-danger"')
        self.assertNotIn("btn-primary btn-danger", html)

    def test_delete(self):
        url = reverse("customer-delete", args=[self.customer.pk])
        response = self.client.post(url, {"confirm": "on", "delete": "Delete"}, follow=True)
        self.assertContains(response, "Deleted »Customer 03«")
        self.assertFalse(Customer.objects.filter(pk=self.customer.pk).exists())

    def test_invalid_form_shows_tabler_validation(self):
        response = self.client.post(reverse("customer-create"), {"email": "nope", "status": "lead", "revenue": "0"})
        self.assertContains(response, "is-invalid")
        self.assertContains(response, "invalid-feedback")

    def test_modal_shell_is_tabler(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        self.assertIn('class="modal modal-blur fade" id="cv-modal"', html)
        self.assertIn('class="modal-dialog modal-dialog-centered" id="cv-modal-dialog"', html)
        self.assertIn('id="cv-modal-content"', html)

    def test_filter_toggle_contract(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        button = re.search(r'<button[^>]*id="cv-filter-toggle"[^>]*>.*?</button>', html, re.S).group(0)
        self.assertIn('aria-controls="filter-collapse"', button)
        self.assertIn('aria-expanded="false"', button)
        self.assertIn('class="btn btn-icon"', button)
        self.assertIn('data-cv-tooltip="context"', button)
        self.assertIn('<span data-cv-filter-icon="open">', button)
        self.assertIn('<span data-cv-filter-icon="close" hidden>', button)
        self.assertEqual(button.count("<svg"), 2)

    def test_filter_toggle_reflects_the_session_state(self):
        response = self.client.post(
            reverse("customer-list"), data='{"filter_expanded": true}', content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        html = self.client.get(reverse("customer-list")).content.decode()
        button = re.search(r'<button[^>]*id="cv-filter-toggle"[^>]*>.*?</button>', html, re.S).group(0)
        self.assertIn('aria-expanded="true"', button)
        self.assertIn('<span data-cv-filter-icon="open" hidden>', button)
        self.assertIn('<span data-cv-filter-icon="close">', button)
        self.assertIn('class="collapse show" id="filter-collapse"', html)

    def test_pinned_filter_has_no_toggle(self):
        with mock.patch.object(CustomerListView, "cv_filter_pinned", True):
            html = self.client.get(reverse("customer-list")).content.decode()
        self.assertIn('id="filter-pinned"', html)
        self.assertNotIn('id="cv-filter-toggle"', html)
        self.assertIn("<svg", html[html.index('id="filter-pinned"'):][:800])  # the card header's filter icon

    def test_action_tooltips_are_initialised_by_crud_views(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        buttons = re.findall(r"<(?:a|button)\b[^>]*\bcv-key=[^>]*>", html)
        self.assertGreater(len(buttons), 3)
        for tag in buttons:
            self.assertNotIn('data-bs-toggle="tooltip"', tag)
        self.assertTrue(any("data-cv-tooltip" in tag for tag in buttons))
        for key in ("list", "card", "create"):  # the filter toggle is checked by id in test_filter_toggle_contract
            self.assertIn('data-cv-tooltip="context"', self.tag(html, key), key)

    def test_toolbar_uses_theme_classes(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        create = self.tag(html, "create")
        self.assertIn('class="btn btn-primary btn-icon"', create)
        self.assertIn('data-cv-tooltip="context"', create)
        self.assertIn('class="btn btn-icon active"', self.tag(html, "list"))
        self.assertIn('aria-current="page"', self.tag(html, "list"))
        self.assertRegex(html, r'<fieldset class="btn-list" aria-label="Actions" cv-context-container="true">')

    def test_row_actions_use_theme_classes(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        delete = self.tag(html, "delete")
        self.assertIn('class="btn btn-sm btn-icon btn-ghost-danger"', delete)
        self.assertIn('data-cv-tooltip="list"', delete)
        self.assertIn('class="btn btn-sm btn-icon btn-ghost-secondary"', self.tag(html, "update"))
        self.assertIn('<fieldset class="btn-list flex-nowrap justify-content-end gap-1"', html)

    def test_overflow_menu_uses_theme_classes(self):
        with mock.patch.object(CustomerListView, "cv_list_actions_inline", ["detail"]):
            html = self.client.get(reverse("customer-list")).content.decode()
        self.assertIn('<div class="dropdown">', html)
        self.assertRegex(html, r'class="btn btn-sm btn-icon btn-ghost-secondary dropdown-toggle cv-menu-toggle"')

    def test_upstream_templates_are_not_overridden(self):
        # Near copies (spacing or markup Tabler does not need) and every template whose only job was button classes,
        # the primary action or the tooltip marker: the class table and crud_views' leaves cover those.
        for name in ("crud_views/modal/content.html", "crud_views/tags/actions_menu_item_label.html",
                     "crud_views/tags/breadcrumb.html", "crud_views/tags/context_action.html",
                     "crud_views/tags/list_action.html", "crud_views/tags/card_action.html",
                     "crud_views/tags/context_actions.html", "crud_views/columns/actions.html",
                     "crud_views/tags/actions_menu_toggle.html", "crud_views/tags/context_action_filter.html",
                     "crud_views/snippets/card_order.html"):
            self.assertNotIn("crud_views_tabler", get_template(name).origin.name, name)
        with self.assertRaises(TemplateDoesNotExist):
            get_template("crud_views/tags/list_action.inner.html")
        for name in ("crud_views/tags/button/action.html", "crud_views/tags/button/container.html",
                     "crud_views/tags/button/menu_item.html", "crud_views/tags/button/menu_item_label.html"):
            self.assertNotIn("crud_views_tabler", get_template(name).origin.name, name)

    def test_menu_items_use_the_fixed_width_icon_slot(self):
        with mock.patch.object(CustomerListView, "cv_list_actions_inline", ["detail"]):
            html = self.client.get(reverse("customer-list")).content.decode()
        item = re.search(r'<a\b[^>]*class="dropdown-item[^"]*"[^>]*cv-key="update"[^>]*>.*?</a>', html, re.S).group(0)
        self.assertIn('class="icon cv-icon-fw"', item)

    def test_breadcrumb_is_a_nav_landmark(self):
        html = self.client.get(reverse("customer-list")).content.decode()
        self.assertIn('<nav aria-label="breadcrumb">', html)


class CardThemeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser("root", "root@example.com", "s3cret-pass")
        Customer.objects.bulk_create(Customer(name=f"Customer {i:02}", revenue=i * 10) for i in range(15))

    def setUp(self):
        self.client.force_login(self.admin)

    def get(self, **params):
        return self.client.get(reverse("customer-card"), params).content.decode()

    def test_cards_render_in_tabler_grid(self):
        html = self.get()
        self.assertIn('class="row row-deck row-cards"', html)
        self.assertEqual(html.count('class="card-footer"'), 12)  # paginate_by
        self.assertEqual(html.count('class="btn-list" cv-card-container="true"'), 12)
        self.assertIn('class="pagination', html)
        self.assertNotIn("fa-solid", html)
        self.assertNotIn("<i class=", html)

    def test_card_action_variants(self):
        html = self.get()
        self.assertIn('class="btn btn-sm btn-primary flex-grow-1"', html)  # primary + flex, labelled: no btn-icon
        self.assertIn('class="btn btn-sm btn-icon btn-ghost-secondary"', html)  # tertiary:icon (the demo's delete)
        open_ = re.search(r'<a\b[^>]*cv-key="detail"[^>]*>.*?</a>', html, re.S).group(0)
        self.assertIn("<svg", open_)  # label mode "both", upstream's card default (#213): icon and text
        self.assertIn("<span>Open</span>", open_)
        self.assertIn('<span class="visually-hidden">Delete</span>', html)  # icon-only keeps a name

    def test_card_follows_upstream_block_names_and_class_keys(self):
        # upstream #243: same block names as crud_views' card, so a cv_card_template works under either theme
        template = Template(
            '{% extends "crud_views/tags/card.html" %}'
            "{% block card_title %}T{% endblock %}{% block card_content %}<p>C</p>{% endblock %}"
            "{% block card_actions %}{% endblock %}"
        )
        page = self.client.get(reverse("customer-card")).context
        customer = Customer.objects.get(name="Customer 03")
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:title": "card-title x-title"}):
            html = template.render(Context({"object": customer, "view": page["view"], "request": page["request"]}))
        self.assertIn('<div class="card">', html)  # card:root without mb-3: the row-deck grid spaces the cards
        self.assertIn('<h3 class="card-title x-title">T</h3>', html)
        self.assertIn("<p>C</p>", html)
        self.assertNotIn("card-footer", html)  # dropping the actions drops the footer with them
        self.assertNotIn("cv-card-container", html)

    def _render_card(self, template):
        page = self.client.get(reverse("customer-card")).context
        customer = Customer.objects.get(name="Customer 03")
        return template.render(Context({"object": customer, "view": page["view"], "request": page["request"]}))

    def test_card_new_blocks_are_empty_by_default(self):
        # upstream #325: card_root and card_header exist and render nothing unless filled
        html = self._render_card(Template('{% extends "crud_views/tags/card.html" %}'))
        self.assertRegex(html, r'<div class="card">\s*<div class="card-body">\s*<h3 class="card-title">')

    def test_card_root_and_header_blocks_render_in_place(self):
        html = self._render_card(get_template("testapp/customer_card_blocks.html").template)
        self.assertRegex(html, r'<div class="card">\s*<i data-root></i>\s*<div class="card-body">')
        self.assertRegex(html, r'<div class="card-body">\s*<i data-head></i>\s*<h3 class="card-title">')

    def test_card_links_carry_their_origin(self):
        html = self.get()
        self.assertIn("/update/?cv_from=card", html)
        self.assertIn("/delete/?cv_from=card", html)

    def test_pagination_is_upstream_with_tabler_chevrons(self):
        # upstream #241: accessible markup and arrows from the icon registry; the theme maps the icons only
        self.assertNotIn("crud_views_tabler", get_template("crud_views/snippets/pagination.html").origin.name)
        html = self.get(page=2)
        nav = re.search(r'<nav aria-label="pagination".*?</nav>', html, re.S).group(0)
        self.assertIn(str(svg("chevron-left")), nav)
        self.assertIn(str(svg("chevron-right")), nav)
        self.assertIn('<li class="page-item active" aria-current="page">', nav)
        self.assertIn('<a class="page-link" aria-disabled="true">', nav)  # page 2 of 2: no next page
        self.assertIn('<span class="visually-hidden">previous</span>', nav)

    def test_order_bar(self):
        html = self.get(order="revenue", dir="desc")
        self.assertIn('id="cv-card-order-form"', html)
        self.assertRegex(html, r'value="desc"\s+class="btn btn-icon active"')
        self.assertIn('<fieldset class="btn-group"', html)
        self.assertRegex(html, r'<button[^>]*value="asc"[^>]*>\s*<svg')
        self.assertLess(html.index("Customer 14"), html.index("Customer 13"))

    def test_empty_state(self):
        html = self.get(name="nothing-matches", submit="Apply Filter")
        self.assertIn('class="empty"', html)
        self.assertIn("No items found.", html)

    @override_settings(LANGUAGE_CODE="de")
    def test_empty_state_is_translated(self):
        # the theme's empty state shares its msgid with crud_views' card list, translated upstream (#246)
        html = self.get(name="nothing-matches", submit="Apply Filter")
        self.assertIn('class="empty"', html)
        self.assertIn("Keine Einträge gefunden.", html)

    def test_delete_from_card_returns_to_cards(self):
        customer = Customer.objects.get(name="Customer 03")
        url = reverse("customer-delete", args=[customer.pk]) + "?cv_from=card"
        response = self.client.post(url, {"confirm": "on", "delete": "Delete"})
        self.assertRedirects(response, reverse("customer-card"), fetch_redirect_response=False)

    def test_headings_follow_crud_views_header_level(self):
        # page title, card titles and the filter heading go through {% cv_heading %} (#251), like the stock templates
        html = self.get(cv_filter="1")
        self.assertRegex(html, r'<h2 class="page-title">')
        self.assertRegex(html, r'<h3 class="card-title">')
        self.assertRegex(html, r'<h3 class="card-title d-flex align-items-center gap-2">')
        from unittest import mock

        from crud_views.lib.settings import crud_views_settings
        # crud_views reads the setting once into crud_views_settings; its own tests patch that object the same way
        with mock.patch.object(crud_views_settings, "header_level", 1):
            html = self.get(cv_filter="1")
        self.assertRegex(html, r'<h1 class="h2 page-title">')
        self.assertRegex(html, r'<h2 class="h3 card-title">')
        self.assertRegex(html, r'<h2 class="h3 card-title d-flex align-items-center gap-2">')

    def test_icon_only_card_action_has_a_crud_views_tooltip(self):
        html = self.get()
        delete = re.search(r'<a\b[^>]*/delete/\?cv_from=card[^>]*>', html).group(0)  # the label_mode="icon" action
        self.assertIn("btn-icon", delete)
        self.assertIn('data-cv-tooltip="card"', delete)
        self.assertNotIn('data-bs-toggle="tooltip"', delete)


class IconCheckTests(TestCase):
    @override_settings(CRUD_VIEWS_ICONS={"detail": "tabler:does-not-exist"})
    def test_unknown_tabler_icon_is_reported(self):
        messages = [m for m in run_checks() if m.id == "crud_views_tabler.W001"]
        self.assertEqual(len(messages), 1)
        self.assertIn("'detail'", messages[0].msg)
        self.assertIn("'tabler:does-not-exist'", messages[0].msg)

    @override_settings(CRUD_VIEWS_ICONS={"detail": "far:eye", "person": "tabler:user"})
    def test_other_library_values_are_not_reported(self):
        self.assertEqual([m.id for m in run_checks() if m.id.startswith("crud_views_tabler.")], [])

    @override_settings(
        CRUD_VIEWS_ICONS={"detail": "tabler:does-not-exist"},
        CRUD_VIEWS_ICON_LIBRARIES={"tabler": {"renderer": "font", "class": "ti ti-{name}"}},
    )
    def test_remapped_tabler_library_is_not_reported(self):
        self.assertEqual([m.id for m in run_checks() if m.id.startswith("crud_views_tabler.")], [])

    @override_settings(CRUD_VIEWS_ICONS={"detail": " tabler:nope "})
    def test_value_with_surrounding_whitespace_is_reported(self):
        messages = [m for m in run_checks() if m.id == "crud_views_tabler.W001"]
        self.assertEqual(len(messages), 1)
        self.assertIn("'nope'", messages[0].msg)


class MessagesParityTests(SimpleTestCase):
    def assert_message_parity(self, plain, themed):
        from html.parser import HTMLParser
        class Hooks(HTMLParser):
            def __init__(self):
                super().__init__()
                self.alerts = 0
                self.buttons = []
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if attrs.get("role") == "alert":
                    self.alerts += 1
                if tag == "button":
                    self.buttons.append(attrs)
        native, crud = Hooks(), Hooks()
        native.feed(plain)
        crud.feed(themed)
        self.assertGreater(native.alerts, 0)
        self.assertEqual(native.alerts, crud.alerts)
        self.assertEqual(len(native.buttons), native.alerts)
        self.assertEqual(len(crud.buttons), crud.alerts)
        for button in native.buttons:
            self.assertEqual(button.get("data-bs-dismiss"), "alert")
            self.assertNotIn("data-cv-alert-dismiss", button)
        for button in crud.buttons:
            self.assertEqual(button.get("data-cv-alert-dismiss"), "")
            self.assertNotIn("data-bs-dismiss", button)
        def normalized(value):
            return re.sub(r">\s+<", "><", re.sub(r"\s+", " ", value)).strip()
        self.assertEqual(normalized(plain.replace('data-bs-dismiss="alert"', 'data-cv-alert-dismiss=""')),
                         normalized(themed))

    def test_parity_rejects_wrong_missing_dual_hooks_and_unrelated_changes(self):
        messages = [Message(constants.INFO, "unchanged body")]
        native = render_to_string("django_tabler/includes/messages.html", {"messages": messages})
        crud = Template("{% load crud_views %}{% cv_messages %}").render(Context({"messages": messages}))
        self.assert_message_parity(native, crud)
        for changed in (
            crud.replace('data-cv-alert-dismiss=""', 'data-cv-alert-dismiss="wrong"'),
            crud.replace('data-cv-alert-dismiss=""', ''),
            crud.replace('data-cv-alert-dismiss=""', 'data-cv-alert-dismiss="" data-bs-dismiss="alert"'),
            crud.replace('role="alert"', 'role="status"'),
            crud.replace('unchanged body', 'changed body'),
        ):
            with self.subTest(changed=changed), self.assertRaises(AssertionError):
                self.assert_message_parity(native, changed)

    def test_plain_include_matches_cv_messages(self):
        messages = [
            Message(constants.DEBUG, "d"),
            Message(constants.INFO, "i"),
            Message(constants.SUCCESS, "s", extra_tags="probe"),
            Message(constants.WARNING, "<b>w</b>"),
            Message(constants.ERROR, "e"),
            Message(35, "custom"),
        ]

        def normalized(html):
            return re.sub(r">\s+<", "><", re.sub(r"\s+", " ", html)).strip()

        plain = render_to_string("django_tabler/includes/messages.html", {"messages": messages})
        themed = Template("{% load crud_views %}{% cv_messages %}").render(Context({"messages": messages}))
        self.assert_message_parity(plain, themed)


class FilterToggleIconTests(SimpleTestCase):
    def test_icon_wrapper_generates_no_box(self):
        # Tabler's .btn-icon .icon has a negative margin that only works on a direct flex child;
        # inside crud_views' wrapper span the icon falls out of the bottom of the button.
        # :not([hidden]) matters: display: contents would otherwise reveal the hidden icon.
        css = (Path(crud_views_tabler.__file__).parent / "static/crud_views_tabler/crud_views_tabler.css").read_text()
        self.assertRegex(css, r"#cv-filter-toggle \[data-cv-filter-icon\]:not\(\[hidden\]\) \{\s*display: contents;")


class HeadingRepeatsTabTests(SimpleTestCase):
    """cv_tabler_heading_repeats_tab: with a bar, a view heading that says the same as the active tab is left out."""

    @staticmethod
    def repeats(header, items, navbar=True):
        from crud_views_tabler.templatetags.crud_views_tabler import cv_tabler_heading_repeats_tab

        context = Context({"view": SimpleNamespace(cv_header=header), "cv_navbar": {"items": items} if navbar else None})
        return cv_tabler_heading_repeats_tab(context)

    def test_heading_equal_to_the_active_tab_repeats(self):
        items = [{"label": "Details", "active": False}, {"label": "Orders", "active": True}]
        self.assertTrue(self.repeats("Orders", items))

    def test_markup_and_whitespace_are_ignored(self):
        self.assertTrue(self.repeats('<span class="x">\n  Orders </span>', [{"label": "Orders", "active": True}]))

    def test_heading_that_says_more_does_not_repeat(self):
        self.assertFalse(self.repeats("Order #1073", [{"label": "Orders", "active": True}]))

    def test_inactive_tab_with_the_same_label_does_not_count(self):
        items = [{"label": "Orders", "active": False}, {"label": "Details", "active": True}]
        self.assertFalse(self.repeats("Orders", items))

    def test_no_active_tab_or_no_bar_never_repeats(self):
        self.assertFalse(self.repeats("Orders", [{"label": "Orders", "active": False}]))
        self.assertFalse(self.repeats("Orders", [{"label": "Orders", "active": True}], navbar=False))


class BareTableTests(SimpleTestCase):
    def test_workflow_no_longer_scrolls_the_whole_content_container(self):
        css = (Path(crud_views_tabler.__file__).parent / "static/crud_views_tabler/crud_views_tabler.css").read_text()
        self.assertNotIn(".page-body > .container-xl:has(> table.table)", css)
        self.assertIn(".cv-typeahead-select-popup", css)
        self.assertIn("--bs-body-bg: var(--tblr-bg-surface)", css)
        self.assertNotRegex(css, r"table\.table \{\s*display: block")

    def test_manage_page_no_longer_scrolls_the_content_container(self):
        # Finding 35: the structured manage page (#366) wraps its tables in .table-responsive; the finding-25 rule is gone
        css = (Path(crud_views_tabler.__file__).parent / "static/crud_views_tabler/crud_views_tabler.css").read_text()
        self.assertNotIn("#cv-ancestor-policy", css)

    def test_manage_page_reads_tabler_secondary_colours(self):
        # Finding 35: upstream's manage.css uses --bs-secondary-* with light fallbacks; Tabler names them --tblr-*
        css = (Path(crud_views_tabler.__file__).parent / "static/crud_views_tabler/crud_views_tabler.css").read_text()
        self.assertRegex(
            css,
            r"\[data-cv-manage\] \{\s*--bs-secondary-color: var\(--tblr-secondary-color\);\s*"
            r"--bs-secondary-text-emphasis: var\(--tblr-secondary-text-emphasis\);",
        )

    def test_object_navbar_pills_look_like_tabs(self):
        # Finding 36: upstream's pills restyled as Tabler underline tabs; Tabler's .nav-link is a flex row, which
        # drops the space between icon and label
        css = (Path(crud_views_tabler.__file__).parent / "static/crud_views_tabler/crud_views_tabler.css").read_text()
        self.assertRegex(css, r"\.cv-tabler-navbar \.nav-link \{\s*gap: \.375rem;")
        self.assertRegex(css, r"\.cv-tabler-navbar \.nav-pills[^{]*\{[^}]*border-bottom")
        self.assertNotIn("--tblr-nav-pills-link-active-color", css)


class ThemeAdoptionTests(TestCase):
    """Native form floor, exact registrations and real action rendering contracts."""
    @classmethod
    def setUpTestData(cls):
        cls.actor = get_user_model().objects.create_superuser("adoption", "adoption@example.invalid", None)
        cls.customer = Customer.objects.create(name="Adoption")

    def setUp(self):
        self.client.force_login(self.actor)

    def controls(self, markup):
        from html.parser import HTMLParser
        class Controls(HTMLParser):
            def __init__(self):
                super().__init__()
                self.rows = []
                self.current = None
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag in ("button", "a"):
                    self.current = {"tag": tag, "attrs": attrs, "paths": [], "text": "", "hidden": False}
                elif self.current is not None and tag == "path" and attrs.get("stroke") != "none":
                    self.current["paths"].append(attrs.get("d"))
                elif self.current is not None and tag == "span" and "visually-hidden" in attrs.get("class", ""):
                    self.current["hidden"] = True
            def handle_data(self, data):
                if self.current is not None:
                    self.current["text"] += data
            def handle_endtag(self, tag):
                if tag in ("button", "a") and self.current is not None:
                    self.rows.append(self.current)
                    self.current = None
        parser = Controls()
        parser.feed(str(markup))
        return parser.rows

    def render_actions(self, mode=None, owner_mode=None, kind_mode=None, destination="absent", tag="button"):
        from crispy_forms.bootstrap import FormActions
        from crispy_forms.helper import FormHelper
        from crispy_forms.layout import Layout
        from crispy_forms.utils import render_crispy_form
        from crud_views.lib.crispy.buttons import Button, Submit
        from crud_views.lib.views.list import ListViewFilterFormHelper
        from crud_views.lib.view import CrudView
        class Owner(CrudView):
            cv_abstract = True
            cv_form_actions_label_mode = ({key: owner_mode for key in
                ("submit", "delete", "cancel", "filter-submit", "filter-reset")} if owner_mode else {}) | (
                {"cancel": kind_mode} if kind_mode else {})
        owner = Owner()
        form = ProbeForm(initial={"x": "initial"})
        form.cv_view = owner
        helper = FormHelper()
        helper.form_tag = False
        kwargs = {} if destination == "absent" else {"data_cv_cancel_url": None if destination == "none" else ""}
        helper.layout = Layout("x", FormActions(Submit("save", "Save"), Submit("delete", "Delete", slot="form:delete"),
                                               Button("cancel", "Cancel", tag=tag, **kwargs)))
        filtered = ProbeForm(initial={"x": "initial"})
        filtered.helper = ListViewFilterFormHelper(view=owner, request=RequestFactory().get("/"))
        filtered.helper.layout = Layout("x")
        with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={} if mode is None else {"form": mode}):
            markup = render_crispy_form(form, helper) + render_crispy_form(filtered, filtered.helper)
        return self.controls(markup), str(markup)

    def test_registered_floor_exact_maps_and_native_action_modes(self):
        from crud_views.lib.view.label_mode import default_label_mode
        with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={}):
            self.assertEqual(default_label_mode("form"), "both")
        self.assertEqual({name: TABLER_ICONS[name] for name in ("save", "cancel", "filter-reset")},
                         {"save": "tabler:check", "cancel": "tabler:arrow-left", "filter-reset": "tabler:filter-x"})
        self.assertEqual({name: TABLER_BUTTON_CLASSES[name] for name in
                          ("form:actions", "form:filter-actions", "alert:dismissible", "alert:close")},
                         {"form:actions": "d-flex flex-wrap gap-2", "form:filter-actions": "d-flex flex-wrap gap-1",
                          "alert:dismissible": "alert-dismissible fade show", "alert:close": "btn-close"})
        for mode in ("both", "icon", "label"):
            rows, markup = self.render_actions(mode)
            self.assertEqual(len(rows), 5)
            self.assertNotIn("fa-solid", markup)
            for row, name in zip(rows, ("check", "trash", "arrow-left", "filter", "filter-x"), strict=True):
                self.assertEqual(row["paths"], [] if mode == "label" else ICONS[name])
                self.assertTrue(row["text"].strip())
                self.assertEqual(row["hidden"], mode == "icon")
            self.assertEqual(rows[-1]["attrs"]["type"], "reset")
            self.assertTrue(rows[-1]["attrs"]["value"])
        rows, _ = self.render_actions("label", "icon", "both")
        self.assertTrue(rows[0]["hidden"])
        self.assertFalse(rows[2]["hidden"])
        self.assertEqual(rows[2]["paths"], ICONS["arrow-left"])
        self.assertEqual(self.render_actions()[0][0]["paths"], ICONS["check"])

    def test_missing_each_new_mapping_fails_native_render_assertion(self):
        from crud_views.lib import icons
        mappings = (("save", 0, "check"), ("cancel", 2, "arrow-left"), ("filter-reset", 4, "filter-x"))
        for name, position, glyph in mappings:
            with self.subTest(name=name), mock.patch.dict(icons._THEME_ICONS), override_settings(CRUD_VIEWS_ICONS={}):
                icons._THEME_ICONS.pop(name)
                icons.reset_icon_cache()
                rows, _ = self.render_actions("both")
                with self.assertRaises(AssertionError):
                    self.assertEqual(rows[position]["paths"], ICONS[glyph])

    def test_cancel_absent_none_empty_all_modes_and_requested_tags(self):
        for destination in ("absent", "none", "empty"):
            for tag in ("button", "a"):
                for mode in ("both", "icon", "label"):
                    with self.subTest(destination=destination, tag=tag, mode=mode):
                        rows, _ = self.render_actions(mode, destination=destination, tag=tag)
                        cancel = rows[2]
                        self.assertEqual(cancel["tag"], "button")
                        self.assertEqual(cancel["attrs"]["type"], "button")
                        self.assertNotIn("href", cancel["attrs"])
                        self.assertEqual("data-cv-cancel-url" in cancel["attrs"], destination == "empty")
                        self.assertEqual(cancel["attrs"].get("data-cv-cancel-url"),
                                         "" if destination == "empty" else None)
                        self.assertEqual(cancel["text"].strip(), "Cancel")
                        self.assertEqual(cancel["paths"], [] if mode == "label" else ICONS["arrow-left"])

    def test_real_create_update_delete_and_filter_pages_have_native_controls(self):
        for name, args in (("customer-create", []), ("customer-update", [self.customer.pk]),
                           ("customer-delete", [self.customer.pk]), ("customer-list", [])):
            with self.subTest(name=name):
                response = self.client.get(reverse(name, args=args))
                self.assertEqual(response.status_code, 200)
                markup = response.content.decode()
                self.assertNotIn("fa-solid", markup)
                self.assertNotIn("fa-regular", markup)
                glyph = "filter" if name == "customer-list" else "trash" if name == "customer-delete" else "check"
                self.assertTrue(any(row["paths"] == ICONS[glyph] for row in self.controls(markup)))


class WorkflowBadgeTests(SimpleTestCase):
    def badge(self, colour="success"):
        from django.db.models import TextChoices
        from crud_views_workflow.lib.mixins import WorkflowModelMixin

        class States(TextChoices):
            DONE = "done", '<Done "now"> {{ untouched }}'

        class Item(WorkflowModelMixin):
            STATE_CHOICES = States
            STATE_BADGES = {"done": colour}

        return Item().get_state_badge("done")

    def test_badge_uses_current_upstream_source(self):
        import crud_views_workflow.lib.mixins as mixins
        upstream = Path(os.environ.get("CV_WORKFLOW_UPSTREAM_SRC", Path(__file__).resolve().parents[3] /
                                      "django-crud-views/src")).resolve()
        self.assertEqual(Path(mixins.__file__).resolve(), upstream / "crud_views_workflow/lib/mixins.py")
        self.assertEqual(Path(get_template("crud_views_workflow/badge.html").origin.name).resolve(),
                         upstream / "crud_views_workflow/templates/crud_views_workflow/badge.html")

    def test_all_state_colours_are_light_badges(self):
        from crud_views_workflow.lib.enums import BadgeEnum
        for colour in BadgeEnum:
            with self.subTest(colour=colour):
                html = self.badge(colour)
                self.assertIn(f'class="badge bg-{colour}-lt"', html)
                self.assertIn('&lt;Done &quot;now&quot;&gt; {{ untouched }}', html)
                self.assertNotIn("<Done", html)

    def test_history_table_matches_the_theme_list_table(self):
        self.assertEqual(get_button_classes()["workflow:history-table"], "table table-vcenter")

    def test_project_classes_override_theme_including_disabled_values(self):
        for value in ("", None, 'custom" onmouseover="bad'):
            with self.subTest(value=value), override_settings(CRUD_VIEWS_BUTTON_CLASSES={"workflow:badge-success": value}):
                html = self.badge()
                expected = 'custom&quot; onmouseover=&quot;bad' if value else ""
                self.assertIn(f'class="{expected}"', html)
                self.assertNotIn(' onmouseover="', html)

    def test_optional_workflow_and_ready_orders_in_isolated_processes(self):
        script = '''
import sys
from django.conf import settings
from tests.crud_views_tabler import settings as test_settings
values = {key: getattr(test_settings, key) for key in dir(test_settings) if key.isupper()}
apps = list(values["INSTALLED_APPS"])
apps.remove("crud_views_workflow")
if sys.argv[1] != "absent":
    apps.insert(apps.index("crud_views_tabler") + (sys.argv[1] == "after"), "crud_views_workflow")
values["INSTALLED_APPS"] = apps
settings.configure(**values)
import django
django.setup()
from crud_views.lib.button_classes import get_button_classes, _THEME_BUTTON_CLASSES
from django.core.checks import run_checks
classes = get_button_classes()
if sys.argv[1] == "absent":
    assert not any(key.startswith("workflow:") for key in _THEME_BUTTON_CLASSES)
    assert not any(key.startswith("workflow:") for key in classes)
else:
    assert classes["workflow:badge-success"] == "badge bg-success-lt"
    from django.test import override_settings
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"workflow:badge-success": "project"}):
        assert get_button_classes()["workflow:badge-success"] == "project"
assert not any(check.id == "crud_views.W362" for check in run_checks())
'''
        for order in ("absent", "before", "after"):
            with self.subTest(order=order):
                result = subprocess.run([sys.executable, "-c", script, order], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class WorkflowMarkup(HTMLParser):
    """Retain raw ancestry, including nested forms that browser parsers would repair."""

    def __init__(self, markup):
        super().__init__()
        self.nodes = []
        self.stack = []
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        node = SimpleNamespace(tag=tag, attrs=dict(attrs), parents=tuple(self.stack))
        self.nodes.append(node)
        if tag not in {"input", "br", "hr", "img", "meta", "link", "wbr"}:
            self.stack.append(node)

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1].tag == tag:
            self.stack.pop()

    def select(self, tag):
        return [node for node in self.nodes if node.tag == tag]


class WorkflowPresentationTests(SimpleTestCase):
    def render_workflow(self, choices=True, history=True, invalid=False, modal=False, settings_classes=None):
        from django.contrib.auth.models import AnonymousUser
        from crud_views.lib.view import CrudView
        from crud_views_workflow.lib.enums import WorkflowComment
        from crud_views_workflow.lib.forms import WorkflowForm

        class Owner(CrudView):
            cv_abstract = True

            def get_cancel_button_context(self, **kwargs):
                return {"cv_url": None}

        request = RequestFactory().get("/workflow/", headers={"X-Cv-Modal": "true"} if modal else {})
        request.user = AnonymousUser()
        owner = Owner()
        owner.request = request
        # WorkflowForm.clean() asks the view's object for business blockers (upstream #322); this one has none
        owner.object = SimpleNamespace(workflow_check_transition=lambda name, *, user: None)
        form = WorkflowForm(owner, data={"transition": "finish", "comment": ""} if invalid else None,
                            choices=[("finish", '<Finish "now">')] if choices else [],
                            transition_comments={"finish": WorkflowComment.REQUIRED})
        if invalid:
            self.assertFalse(form.is_valid())
            form.add_error(None, '<Invalid "workflow">')
        rows = [dict(transition_label="<Finish>", user=SimpleNamespace(get_full_name=lambda: "<Actor>"),
                     state_old_badge=WorkflowBadgeTests().badge(), state_new_badge=WorkflowBadgeTests().badge(),
                     comment="<script>bad</script>")] if history else []
        context = {"form": form, "has_workflow_choices": choices, "object": SimpleNamespace(workflow_data=rows)}
        template = "crud_views/view_custom_form.content.html" if modal else "crud_views_workflow/view_workflow.content.html"
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES=settings_classes or {}):
            markup = render_to_string(template, context, request=request)
        return markup, WorkflowMarkup(markup)

    def test_actual_template_and_pack_origins(self):
        theme = Path(crud_views_tabler.__file__).resolve().parent
        self.assertEqual(Path(get_template("crud_views/snippets/form_frame.html").origin.name),
                         theme / "templates/crud_views/snippets/form_frame.html")
        import crud_views_workflow
        upstream = Path(crud_views_workflow.__file__).resolve().parent
        for leaf in ("action", "history", "content"):
            name = f"crud_views_workflow/view_workflow.{leaf}.html"
            self.assertEqual(Path(get_template(name).origin.name), upstream / "templates" / name)
        import django_tabler
        self.assertEqual(Path(get_template("crispy_tabler/field.html").origin.name),
                         Path(django_tabler.__file__).resolve().parent / "templates/crispy_tabler/field.html")

    def test_action_frame_history_order_and_error_ownership(self):
        for invalid in (False, True):
            with self.subTest(invalid=invalid):
                markup, tree = self.render_workflow(invalid=invalid)
                self.assertEqual(len(tree.select("form")), 1)
                form = tree.select("form")[0]
                self.assertEqual(form.attrs, {"class": "cv-form", "method": "post", "novalidate": None})
                self.assertEqual(form.parents[-1].attrs["class"], "card-body")
                self.assertEqual(form.parents[-2].attrs["class"], "card")
                headings = tree.select("h5")
                self.assertEqual(headings[-1].parents, form.parents)
                table = tree.select("table")[0]
                wrapper = table.parents[-1]
                self.assertEqual(wrapper.attrs["class"], "table-responsive")
                self.assertEqual([node.tag for node in tree.nodes if node.parents and node.parents[-1] is wrapper], ["table"])
                self.assertNotIn(wrapper, form.parents)
                self.assertNotIn(wrapper, headings[0].parents)
                self.assertLess(tree.nodes.index(table), tree.nodes.index(form))
                tokens = [node for node in tree.select("input") if node.attrs.get("name") == "csrfmiddlewaretoken"]
                self.assertEqual(len(tokens), 1)
                self.assertIn(form, tokens[0].parents)
                submits = [node for node in tree.nodes if node.attrs.get("type") == "submit"]
                self.assertEqual(len(submits), 1)
                self.assertIn(form, submits[0].parents)
                self.assertNotIn("<script>", markup)
                self.assertIn("&lt;Finish &quot;now&quot;&gt;", markup)
                if invalid:
                    self.assertIn("Comment is required for this transition", markup)
                    self.assertIn("&lt;Invalid &quot;workflow&quot;&gt;", markup)
                    errors = [node for node in tree.nodes if "invalid-feedback" in node.attrs.get("class", "")]
                    self.assertTrue(errors)
                    self.assertTrue(all(form in node.parents for node in errors))
                self.assertFalse(tree.stack)

    def test_empty_actions_and_history_are_independent(self):
        for history in (False, True):
            markup, tree = self.render_workflow(choices=False, history=history)
            self.assertIn('class="card-body"', markup)
            self.assertIn("There are no workflow steps available from the current state.", markup)
            self.assertNotIn("Workflow Action", markup)
            self.assertFalse(tree.select("form"))
            self.assertNotIn("csrfmiddlewaretoken", markup)
            self.assertEqual(len(tree.select("table")), int(history))
        markup, tree = self.render_workflow(history=False)
        self.assertNotIn("Workflow History", markup)
        self.assertFalse(tree.select("table"))
        self.assertEqual(len(tree.select("form")), 1)

    def test_history_wrapper_and_table_classes_are_independent(self):
        for wrapper_class in ("table-responsive", "custom-wrap", "", None):
            for table_class in ("table", "custom-table", "", None):
                markup, tree = self.render_workflow(settings_classes={"workflow:history-wrapper": wrapper_class,
                                                                     "workflow:history-table": table_class})
                table = tree.select("table")[0]
                self.assertEqual(table.attrs["class"], table_class or "")
                self.assertEqual(table.parents[-1].attrs["class"], wrapper_class or "")
                self.assertEqual(len(tree.select("th")), 6)

    def test_supported_modal_keeps_the_actual_frame_bare(self):
        for choices in (False, True):
            markup, tree = self.render_workflow(choices=choices, modal=True)
            self.assertNotIn('class="card"', markup)
            self.assertNotIn('class="card-body"', markup)
            self.assertNotIn("Workflow History", markup)
            self.assertEqual(len(tree.select("form")), 1)
            self.assertFalse(tree.stack)
