from importlib.metadata import version

import crud_views_tabler
import django_tabler


def test_versions_match_distribution():
    assert version("django-crud-views-tabler") == crud_views_tabler.__version__ == django_tabler.__version__ == "0.1.0"
