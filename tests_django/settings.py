"""
Django test project settings.

These are the default settings to run the tests, but we also want to allow developers to
run this as a standalone server.

For the standalone mode you may:
 - use the Makefile's `run_django` command: `make run_django`
 - or manually set the `DJANGO_ENVIRONMENT` to `development`:
   `DJANGO_ENVIRONMENT=development python tests_django/manage.py runserver 0.0.0.0:8071`
"""
import os

from django.core.management.utils import get_random_secret_key


TEST_MODE = "test"
DEV_MODE = "development"
MODE = os.environ.get("DJANGO_ENVIRONMENT", "test")
AVAILABLE_MODES = (TEST_MODE, DEV_MODE)

assert MODE in (
    TEST_MODE,
    DEV_MODE,
), f"DJANGO_ENVIRONMENT variable must be in {AVAILABLE_MODES}"


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEBUG = True
USE_TZ = True


# In development/stand alone mode when need a "real" database
# to be able to run migrations eventually
_DEFAULT_DB_NAME = ":memory:"
if MODE == DEV_MODE:
    _DEFAULT_DB_NAME = os.path.join(os.path.dirname(__file__), "local.db")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": _DEFAULT_DB_NAME,
        "TEST_NAME": ":memory:",
    }
}

ROOT_URLCONF = "tests_django.urls"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "social_django",
    # project apps
    "social_edu_federation.django.apps.PythonSocialEduFedAuthConfig",
]

SITE_ID = 1

MIDDLEWARE = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
)

AUTHENTICATION_BACKENDS = (
    "social_edu_federation.backends.saml_fer.FERSAMLAuth",
    "django.contrib.auth.backends.ModelBackend",
)

template_extra_directories = []
# In standalone mode we want to have the index page template available
if MODE == DEV_MODE:
    template_extra_directories = [
        os.path.join(os.path.dirname(__file__), "templates"),
    ]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": template_extra_directories,
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
            ]
        },
    }
]


SECRET_KEY = get_random_secret_key()

STATIC_URL = "static/"
LOGIN_REDIRECT_URL = "index"

# In standalone mode we want to use the default FER backend settings
# and use a local IdP (the testing IdP provided by `social_edu_federation.django.testing`)
if MODE == DEV_MODE:
    from social_edu_federation.testing.settings import saml_fer_settings

    for setting_name, setting_value in saml_fer_settings.items():
        locals()[setting_name] = setting_value

    SOCIAL_AUTH_SAML_FER_FEDERATION_SAML_METADATA_URL = (
        "http://127.0.0.1:8071/saml/idp/metadata/"
    )
