from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = "test-only-not-secret"
ROOT_URLCONF = "tests.crud_views_tabler.urls"
ALLOWED_HOSTS = ["testserver"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "crispy_forms",
    "django_tables2",
    "django_filters",
    "django_tabler",
    # The Tabler theme overrides crud_views templates, so it must come before crud_views.
    "crud_views_tabler",
    "crud_views.apps.CrudViewsConfig",
    "tests.crud_views_tabler.testapp",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

STATIC_URL = "static/"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard:index"
LOGOUT_REDIRECT_URL = "login"

CRISPY_ALLOWED_TEMPLATE_PACKS = ("crispy_tabler",)
CRISPY_TEMPLATE_PACK = "crispy_tabler"
CRUD_VIEWS_EXTENDS = "crud_views_tabler/page.html"
DJANGO_TABLES2_TEMPLATE = "crud_views/table/bootstrap5.html"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
