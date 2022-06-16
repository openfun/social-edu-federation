"""Configuration module for the social_edu_federation Django integration."""
from django.apps import AppConfig
from django.core import checks as django_checks
from django.core.checks import Tags

from . import checks


class PythonSocialEduFedAuthConfig(AppConfig):
    """App configuration for social_edu_federation Django integration"""

    # Explicitly set default auto field type to avoid migrations in Django 3.2+
    default_auto_field = "django.db.models.AutoField"
    # Full Python path to the application eg. 'django.contrib.admin'.
    name = "social_edu_federation.django"
    # Last component of the Python path to the application eg. 'admin'.
    label = "social_edu_federation_django"
    # Human-readable name for the application eg. "Admin".
    verbose_name = "Python Social Education Federation Auth"

    def ready(self):
        django_checks.register(checks.metadata_store_check, Tags.caches)
