"""Pytest common fixtures for the Django integration tests"""

from copy import deepcopy

from django.core.cache import caches

import pytest

from social_edu_federation.testing.settings import saml_fer_settings


@pytest.fixture(name="backend_settings")
def backend_settings_fixture(settings):
    """Fixture providing the `saml_fer` backend settings"""
    for key, value in saml_fer_settings.items():
        setattr(settings, key, value)


@pytest.fixture(name="default_loc_mem_cache")
def default_loc_mem_cache_fixture(settings):
    """
    Pytest fixture to override cache settings and use a `LocMemCache` as default cache.

    We need to store the original value because we want to
    set it again before reloading the initial values of the
    cache module at the end.
    """
    # We need to store the original value because we want to
    # set it again before reloading the cache module at the end.
    cache_initial_value = deepcopy(settings.CACHES)

    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "social_edu_federation.tests_django.tests.fixtures",
        },
    }

    # Force cache list reloading
    del caches.settings

    yield

    caches["default"].clear()

    settings.CACHES = cache_initial_value

    # Force cache list reloading
    del caches.settings
