SECRET_KEY = "test-only-not-secret"
ROOT_URLCONF = "tests.crispy_tabler.urls"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_tabler",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    },
]

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

CRISPY_TEMPLATE_PACK = "crispy_tabler"
CRISPY_ALLOWED_TEMPLATE_PACKS = ("crispy_tabler",)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
