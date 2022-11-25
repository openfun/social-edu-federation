"""Metadata store tests, already tested in full process so this is only unit testing."""
from copy import deepcopy
import datetime
import re

from django.core.cache import InvalidCacheBackendError, cache as default_cache, caches
from django.utils import timezone

import pytest
from social_django.utils import load_backend, load_strategy

from social_edu_federation.backends.saml_fer import FERSAMLIdentityProvider
from social_edu_federation.django.metadata_store import CachedMetadataStore
from social_edu_federation.parser import FederationMetadataParser


class MagicClass:
    """Mocking class to replace IdP real object"""

    def __init__(self, **kwargs):
        """Store all provided `kwargs` as attributes"""
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def create_from_config_dict(cls, **kwargs):
        """Creation method called by the metadata store."""
        return cls(**kwargs)


class MockedBackend:
    """Fake backend for test purpose only"""

    edu_fed_saml_idp_class = MagicClass
    name = "mocked-backend"

    def __init__(self, cache_name=None):
        self.cache_name = cache_name

    def get_federation_metadata_url(self):
        """Boilerplate to return a fixed URL"""
        return "https://domain.test/metadata/"

    def setting(self, name, default_value=None):  # pylint: disable=unused-argument
        """
        Defines a dummy method to return the cache name,
        we assert this is the only setting used.
        """
        assert name == "DJANGO_CACHE"
        return self.cache_name


@pytest.fixture(name="cache_settings")
def cache_settings_fixture(settings):
    """
    Pytest fixture to override cache settings.

    We need to store the original value because we want to
    set it again before reloading the initial values of the
    cache module at the end.
    """
    cache_initial_value = deepcopy(settings.CACHES)

    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "renater_cache_entry_tests",
        },
        # add another named cache to test cache change works
        "some_cache_name": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "renater_cache_entry_tests.some_cache_name",
        },
    }

    # Force cache list reloading
    del caches.settings

    yield

    default_cache.clear()

    settings.CACHES = cache_initial_value

    # Force cache list reloading
    del caches.settings


def test_fetch_remote_metadata(cache_settings, mocker):
    """Tests `fetch_remote_metadata` method."""
    store = CachedMetadataStore(MockedBackend())

    get_metadata_mock = mocker.patch.object(FederationMetadataParser, "get_metadata")
    get_metadata_mock.return_value = b"been called"

    assert store.fetch_remote_metadata() == b"been called"

    get_metadata_mock.assert_called_once_with(
        "https://domain.test/metadata/", timeout=10
    )

    # Now call it again, metadata are not cached
    get_metadata_mock.reset_mock()

    assert store.fetch_remote_metadata() == b"been called"

    assert get_metadata_mock.called


@pytest.mark.parametrize(
    "cache_name",
    [
        pytest.param(
            None,
            id="use-default-cache",
        ),
        pytest.param(
            "some_cache_name",
            id="use-named-cache",
        ),
    ],
)
def test_get_idp(cache_name, cache_settings, freezer, mocker):
    """
    Tests `get_idp` method with different values for cache name setting (not defined and defined).
    """
    now = timezone.now()
    store = CachedMetadataStore(MockedBackend(cache_name=cache_name))

    get_metadata_mock = mocker.patch.object(FederationMetadataParser, "get_metadata")
    get_metadata_mock.return_value = b"been called"
    parse_metadata_mock = mocker.patch.object(
        FederationMetadataParser, "parse_federation_metadata"
    )
    parse_metadata_mock.return_value = {
        "some-idp": {
            "key1": "value1",
            "key2": "value2",
        },
        "other-idp": {
            "key3": "value3",
        },
    }

    magic_instance = store.get_idp("some-idp")

    get_metadata_mock.assert_called_once_with(
        "https://domain.test/metadata/", timeout=10
    )
    parse_metadata_mock.assert_called_once_with(b"been called")

    assert magic_instance.key1 == "value1"
    assert magic_instance.key2 == "value2"
    assert not hasattr(magic_instance, "key3")

    cache_to_test = default_cache if cache_name is None else caches[cache_name]
    assert cache_to_test.get("edu_federation:mocked-backend:some-idp") == {
        "key1": "value1",
        "key2": "value2",
    }
    assert cache_to_test.get("edu_federation:mocked-backend:other-idp") == {
        "key3": "value3",
    }
    assert cache_to_test.get("edu_federation:mocked-backend:all_idps") == {
        "other-idp": {"key3": "value3"},
        "some-idp": {"key1": "value1", "key2": "value2"},
    }

    # Now call it again and assert cache is used
    get_metadata_mock.reset_mock()
    parse_metadata_mock.reset_mock()

    magic_instance_again = store.get_idp("some-idp")

    assert magic_instance_again.key1 == "value1"
    assert magic_instance_again.key2 == "value2"
    assert not hasattr(magic_instance_again, "key3")

    assert not get_metadata_mock.called
    assert not parse_metadata_mock.called

    # Move after the cache expiration
    freezer.move_to(now + datetime.timedelta(hours=24, minutes=1, seconds=1))

    assert cache_to_test.get("edu_federation:mocked-backend:some-idp") is None
    assert cache_to_test.get("edu_federation:mocked-backend:other-idp") is None
    assert cache_to_test.get("edu_federation:mocked-backend:all_idps") is None

    magic_instance_refreshed = store.get_idp("some-idp")

    assert magic_instance_refreshed.key1 == "value1"
    assert magic_instance_refreshed.key2 == "value2"
    assert not hasattr(magic_instance_refreshed, "key3")

    get_metadata_mock.assert_called_once_with(
        "https://domain.test/metadata/", timeout=10
    )
    parse_metadata_mock.assert_called_once_with(b"been called")


def test_get_idp_named_cache_does_not_exist(settings):
    """Tests `get_idp` method when the setting for cache is not a valid one."""
    with pytest.raises(
        InvalidCacheBackendError,
        match=re.escape("'invalid' does not exist in ['default']"),
    ):
        CachedMetadataStore(MockedBackend(cache_name="invalid"))


def test_saml_fer_backend_integration(cache_settings, mocker, settings):
    """
    Tests the metadata store with a real backend (`FERSAMLAuth`),
    without cache name setting (`DJANGO_CACHE`) defined.
    """
    settings.AUTHENTICATION_BACKENDS = (
        "social_edu_federation.backends.saml_fer.FERSAMLAuth",
    )
    settings.SOCIAL_AUTH_SAML_FER_FEDERATION_SAML_METADATA_URL = (
        "https://domain.test/metadata/"
    )

    strategy = load_strategy()
    backend = load_backend(strategy, "saml_fer", None)

    store = CachedMetadataStore(backend)

    get_metadata_mock = mocker.patch.object(FederationMetadataParser, "get_metadata")
    get_metadata_mock.return_value = b"been called"
    parse_metadata_mock = mocker.patch.object(
        FederationMetadataParser, "parse_federation_metadata"
    )
    parse_metadata_mock.return_value = {
        "some-idp": {
            "name": "some-idp",
            "entityId": "http://some-idp/",
            "singleSignOnService": {
                "url": "http://some-idp/ls/",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "singleLogoutService": {
                "url": "http://some-idp/slo/",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            # certificate is not validated on creation...
            "x509cert": "MIIC4DCCAcigAwIBAgIQG...CQZXu/agfMc/tY+miyrD0=",
            "edu_fed_data": {
                "display_name": "Some IdP",
            },
        },
        "other-idp": {
            "name": "other-idp",
            "entityId": "http://other-idp/",
            "singleSignOnService": {
                "url": "http://other-idp/ls/",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "singleLogoutService": {
                "url": "http://other-idp/slo/",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            # certificate is not validated on creation...
            "x509cert": "MIIC4DCCAcigAwIBAgIQG...CQZXu/agfMc/tY+miyrD0=",
            "edu_fed_data": {
                "display_name": "Other IdP",
            },
        },
    }

    idp_configuration = store.get_idp("some-idp")
    assert isinstance(idp_configuration, FERSAMLIdentityProvider)

    get_metadata_mock.assert_called_once_with(
        "https://domain.test/metadata/", timeout=10
    )
    parse_metadata_mock.assert_called_once_with(b"been called")

    assert idp_configuration.name == "some-idp"
    assert idp_configuration.conf == {
        "attr_email": "urn:oid:0.9.2342.19200300.100.1.3",
        "attr_first_name": "urn:oid:2.5.4.42",
        "attr_full_name": "urn:oid:2.16.840.1.113730.3.1.241",
        "attr_last_name": "urn:oid:2.5.4.4",
        "attr_roles": "urn:oid:1.3.6.1.4.1.5923.1.1.1.1",
        "attr_user_permanent_id": "urn:oid:1.3.6.1.4.1.5923.1.1.1.6",
        "attr_username": "urn:oid:0.9.2342.19200300.100.1.3",
        #
        "entity_id": "http://some-idp/",
        "slo_url": "http://some-idp/slo/",
        "url": "http://some-idp/ls/",
        "x509cert": "MIIC4DCCAcigAwIBAgIQG...CQZXu/agfMc/tY+miyrD0=",
        "x509certMulti": None,
        "edu_fed_display_name": "Some IdP",
    }
