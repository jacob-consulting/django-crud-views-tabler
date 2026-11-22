"""Bulk selection (django-crud-views #392) under the Tabler theme: toolbar and checkboxes with the resolved bulk:*
classes, the select column inside the table card, the review page in the page shell, result messages in the shell's
message alerts. Ported from the AdminLTE theme's tests/crud_views_adminlte/test_bulk.py."""

import re
from pathlib import Path

import crud_views
import lxml.html
import pytest
from crud_views.lib.button_classes import get_button_class
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

import crud_views_tabler
from tests.crud_views_tabler.testapp.models import Customer

pytestmark = pytest.mark.django_db

MESSAGE = "main .alert"  # the theme page renders crud_views' own cv_messages alerts (crud_views/tags/alert.html)


@pytest.fixture
def admin_client(client):
    user = get_user_model().objects.create_superuser("admin", "admin@example.com", "admin")
    client.force_login(user)
    return client


@pytest.fixture
def customers():
    return [
        Customer.objects.create(name="Ursula Le Guin", country="US"),
        Customer.objects.create(name="Stanisław Lem", country="PL"),
        Customer.objects.create(name="Anonymous", country=""),
    ]


def page(response):
    assert response.status_code == 200
    return lxml.html.fromstring(response.content.decode())


def text(element):
    return " ".join(element.text_content().split())


def css(slot):
    """The resolved bulk:<slot> classes as a CSS class selector."""
    return "".join(f".{c}" for c in get_button_class("bulk", slot).split())


def test_bulk_toolbar(admin_client, customers):
    doc = page(admin_client.get(reverse("bulk_customer-list")))
    (main,) = doc.cssselect("main")
    (toolbar,) = main.cssselect(f"form[data-cv-bulk]{css('toolbar')}")
    assert toolbar.get("method") == "post"
    form_id = toolbar.get("id")
    # select-all and count, hidden until bulk.js reveals them
    (enhanced,) = toolbar.cssselect("[data-cv-bulk-enhanced][hidden]")
    (controls,) = enhanced.cssselect(css("controls"))
    (select_all,) = controls.cssselect(f"label{css('select-all')} input[type=checkbox][data-cv-bulk-all]")
    assert select_all.get("class") == get_button_class("bulk", "checkbox")
    assert controls.cssselect("[data-cv-bulk-count]")
    # one submit button per action, Bootstrap-styled, with icon and label (bulk label mode "both")
    (actions,) = toolbar.cssselect(css("actions"))
    buttons = actions.cssselect("button[data-cv-bulk-action]")
    assert [b.get("data-cv-bulk-action") for b in buttons] == ["clear_country", "set_country"]
    for button in buttons:
        assert "btn" in button.get("class").split()
        assert button.get("formaction")
        assert button.cssselect("svg")  # Tabler icons are inline SVG
    assert text(buttons[0]) == "Clear country"
    # per-row checkboxes in the first column, bound to the toolbar form
    rows = main.cssselect("table tbody tr")
    assert len(rows) == 3
    for row in rows:
        (box,) = row.cssselect("td:first-child input[type=checkbox][data-cv-bulk-item]")
        assert box.get("class") == get_button_class("bulk", "checkbox")
        assert box.get("form") == form_id
        assert box.get("name") == "cv_bulk_ids"
    # the toolbar sits above the table card, outside it
    assert not toolbar.xpath("ancestor::*[contains(@class, 'table-container')]")
    # bulk.js is loaded by the page's {% cv_js %}
    assert any("crud_views/js/bulk.js" in (s.get("src") or "") for s in doc.cssselect("script"))


def test_bulk_card_view(admin_client, customers):
    doc = page(admin_client.get(reverse("bulk_customer-card")))
    (main,) = doc.cssselect("main")
    (toolbar,) = main.cssselect(f"form[data-cv-bulk]{css('toolbar')}")
    assert toolbar.cssselect("[data-cv-bulk-all]")
    (grid,) = main.cssselect(".row.row-deck")
    cells = grid.cssselect(css("card-cell"))
    assert len(cells) == 3
    assert len(grid.cssselect("[data-cv-bulk-item]")) == 3  # one checkbox per card, all inside the theme's grid
    for cell in cells:
        (box,) = cell.cssselect("input[type=checkbox][data-cv-bulk-item]")
        assert box.get("class") == get_button_class("bulk", "card-select")
        assert box.get("form") == toolbar.get("id")
        assert cell.cssselect(".card")  # the card itself, next to its checkbox


def test_bulk_card_cell_fills_its_grid_column(admin_client, customers):
    # Tabler's .row-deck column is a flex row, so a plain block cell shrinks to its card's content
    doc = page(admin_client.get(reverse("bulk_customer-card")))
    cells = doc.cssselect(f".row-deck {css('card-cell')}")
    assert len(cells) == 3  # so the loop cannot pass vacuously
    for cell in cells:
        classes = cell.get("class").split()
        assert {"position-relative", "d-flex", "flex-fill"} <= set(classes)


def test_bulk_prefixed_sort_marks_the_header(admin_client, customers):
    # the bulk ViewSet's table has the prefix "c": ?c-sort=name marks the Name header (aria-sort, sort class)
    doc = page(admin_client.get(reverse("bulk_customer-list") + "?c-sort=name"))
    (th,) = [th for th in doc.cssselect("thead th") if "Name" in th.text_content()]
    assert th.get("aria-sort") == "ascending"
    assert "asc" in th.cssselect("a.table-sort")[0].get("class").split()


def test_bulk_checkboxes_point_at_the_toolbar_form(admin_client, customers):
    for name in ("bulk_customer-list", "bulk_customer-card"):
        doc = page(admin_client.get(reverse(name)))
        boxes = doc.cssselect("input[data-cv-bulk-item]")
        assert len(boxes) == 3
        for box in boxes:
            assert len([f for f in doc.cssselect("form") if f.get("id") == box.get("form")]) == 1, name


def test_bulk_table_inside_tabler_card(admin_client, customers):
    doc = page(admin_client.get(reverse("bulk_customer-list")))
    (card,) = doc.cssselect("main .card.table-container")
    # the select column is part of the table in the card's scroller, so a wide list scrolls there (tracker C9)
    (table,) = card.cssselect(".table-responsive > table")
    (header,) = table.cssselect("thead tr")
    assert text(header.cssselect("th")[0]) == "Select"  # the column header; select-all lives in the toolbar above
    assert not header.cssselect("input")
    rows = table.cssselect("tbody tr")
    assert len(rows) == 3
    for row in rows:
        assert len(row.cssselect("td:first-child input[data-cv-bulk-item]")) == 1


THEME_CARD = Path(crud_views_tabler.__file__).resolve().parent / "templates/crud_views/view_card.content.html"
UPSTREAM_CARD = Path(crud_views.__file__).resolve().parent / "templates/crud_views/view_card.content.html"
TOOLBAR = re.compile(
    r"\{% if view\.cv_bulk_buttons %\}\{% include \"crud_views/snippets/bulk_toolbar\.html\" %\}\{% endif %\}"
)
CARD_CELL = re.compile(
    r"\{% if view\.cv_bulk_buttons %\}<div class=.*?\{% else %\}\{% cv_card object %\}\{% endif %\}", re.S
)


def fragments(path):
    source = path.read_text()
    found = []
    for pattern in (TOOLBAR, CARD_CELL):
        (match,) = pattern.findall(source)  # exactly one of each, or the markup moved
        found.append(" ".join(match.split()))
    return found


def test_card_bulk_markup_is_upstreams():
    """The theme's card grid copies upstream's bulk toolbar include and card cell (tracker note in the template)."""
    assert fragments(THEME_CARD) == fragments(UPSTREAM_CARD)


def test_bulk_card_hides_selection_when_no_action_is_offered(client, customers):
    """Upstream #399: a viewer who may enter no bulk action gets neither the toolbar nor the card checkboxes."""
    viewer = get_user_model().objects.create_user("viewer", password="viewer")
    content_type = ContentType.objects.get_for_model(Customer)
    viewer.user_permissions.add(Permission.objects.get(codename="view_customer", content_type=content_type))
    client.force_login(viewer)
    doc = page(client.get(reverse("bulk_customer-card")))
    assert "Ursula Le Guin" in text(doc.cssselect("main")[0])  # the cards themselves are there
    assert not doc.cssselect("form[data-cv-bulk]")
    assert not doc.cssselect("[data-cv-bulk-item]")


def test_bulk_empty_list(admin_client):
    for name in ("bulk_customer-list", "bulk_customer-card"):
        doc = page(admin_client.get(reverse(name)))
        assert not doc.cssselect("[data-cv-bulk-item]"), name
        assert doc.cssselect("form[data-cv-bulk]"), name  # upstream renders the toolbar for an empty list too
    assert page(admin_client.get(reverse("bulk_customer-card"))).cssselect("main .empty")  # Tabler's empty state


def review(client, action, ids):
    url = reverse(f"bulk_customer-{action}")
    return client.post(url, {"cv_bulk_stage": "review", "cv_bulk_ids": [str(pk) for pk in ids]})


def test_bulk_form_page_renders(admin_client, customers):
    doc = page(review(admin_client, "clear_country", [c.pk for c in customers]))
    (main,) = doc.cssselect("main")
    # in the theme's page: the full action label as the page heading
    (header,) = doc.cssselect(".page-header")
    assert "Clear the country of the selected customers" in text(header)
    (form,) = main.cssselect("form.cv-form")
    assert form.cssselect("input[type=hidden][name=cv_bulk_stage][value=execute]")
    assert len(form.cssselect("input[type=hidden][name=cv_bulk_ids]")) == 2
    assert len(form.cssselect("input[type=hidden][name=cv_bulk_blocked_ids]")) == 1
    # blocked: a Bootstrap warning alert with the name and the reason
    (blocked,) = form.cssselect(".alert.alert-warning")
    assert "1 record will be skipped" in text(blocked)
    assert "Anonymous: No country to clear." in text(blocked)
    # eligible: count and names
    assert "To process: 2" in text(form)
    assert {text(li) for li in form.xpath(".//ul[not(ancestor::div[contains(@class,'alert')])]/li")} == {
        "Ursula Le Guin",
        "Stanisław Lem",
    }
    assert form.cssselect("button[type=submit].btn.btn-primary")


def test_bulk_form_page_all_blocked(admin_client, customers):
    doc = page(review(admin_client, "clear_country", [customers[2].pk]))
    (form,) = doc.cssselect("main form.cv-form")
    assert "None of the selected records can be processed." in text(form)
    assert not form.cssselect("button[type=submit].btn-primary")  # no execution button, only the way back


def test_bulk_form_page_with_input(admin_client, customers):
    doc = page(review(admin_client, "set_country", [customers[0].pk]))
    (form,) = doc.cssselect("main form.cv-form")
    assert form.cssselect("input[name=country].form-control")


def test_bulk_result_message_through_host(admin_client, customers):
    url = reverse("bulk_customer-set_country")
    data = {"cv_bulk_stage": "execute", "cv_bulk_ids": [str(c.pk) for c in customers[:2]], "country": "XX"}
    response = admin_client.post(url, data, follow=True)
    assert response.redirect_chain[-1][0].startswith(reverse("bulk_customer-list"))
    doc = page(response)
    alerts = doc.cssselect(MESSAGE)
    assert [text(a) for a in alerts if "Country set" in text(a)] == ["Country set for 2 customers."]
    (alert,) = alerts
    assert "alert-success" in alert.get("class").split()
    assert alert.cssselect("[data-cv-alert-dismiss]")  # crud_views' dismiss hook, handled by its own script
    assert len(doc.cssselect("main .alert")) == 1  # and the shell's message include is not rendered as well
    assert Customer.objects.filter(country="XX").count() == 2
    # shown once: the next page has no message left
    assert not page(admin_client.get(reverse("bulk_customer-list"))).cssselect(MESSAGE)


def test_bulk_default_message_through_host(admin_client, customers):
    url = reverse("bulk_customer-clear_country")
    data = {"cv_bulk_stage": "execute", "cv_bulk_ids": [str(customers[0].pk)]}
    doc = page(admin_client.post(url, data, follow=True))
    assert [text(a) for a in doc.cssselect(MESSAGE)] == ["1 record processed."]


def test_bulk_empty_selection_warning_through_host(admin_client, customers):
    url = reverse("bulk_customer-clear_country")
    doc = page(admin_client.post(url, {"cv_bulk_stage": "review"}, follow=True))
    (alert,) = doc.cssselect(MESSAGE)
    assert "alert-warning" in alert.get("class").split()
