"""Test module for the prefetch_saml_fer_metadata management command"""
from collections import Counter
from io import StringIO

from django.core.management import CommandError, call_command

import pytest

from social_edu_federation.parser import FederationMetadataParser


def test_command_success(mocker, settings):
    settings.AUTHENTICATION_BACKENDS = (
        "social_edu_federation.backends.saml_fer.FERSAMLAuth",
    )
    settings.SOCIAL_AUTH_SAML_FER_FEDERATION_SAML_METADATA_STORE = (
        "social_edu_federation.django.metadata_store.CachedMetadataStore"
    )
    settings.SOCIAL_AUTH_SAML_FER_FEDERATION_SAML_METADATA_URL = (
        "https://domain.test/metadata/"
    )

    get_metadata_mock = mocker.patch.object(FederationMetadataParser, "get_metadata")
    get_metadata_mock.return_value = b"been called"
    parse_metadata_mock = mocker.patch.object(
        FederationMetadataParser,
        "parse_federation_metadata",
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

    out = StringIO()
    call_command("prefetch_saml_fer_metadata", ["saml_fer"], stdout=out)

    assert "All metadata caches refreshed" in out.getvalue()

    get_metadata_mock.assert_called_once_with(
        "https://domain.test/metadata/",
        timeout=10,
    )
    parse_metadata_mock.assert_called_once_with(b"been called")


def test_command_success_several_backends(mocker, settings):
    settings.AUTHENTICATION_BACKENDS = (
        "social_edu_federation.backends.saml_fer.FERSAMLAuth",
    )
    settings.SOCIAL_AUTH_SAML_FER_FEDERATION_SAML_METADATA_STORE = (
        "social_edu_federation.django.metadata_store.CachedMetadataStore"
    )
    settings.SOCIAL_AUTH_SAML_FER_FEDERATION_SAML_METADATA_URL = (
        "https://domain.test/metadata/"
    )

    get_metadata_mock = mocker.patch.object(FederationMetadataParser, "get_metadata")
    get_metadata_mock.return_value = b"been called"
    parse_metadata_mock = mocker.patch.object(
        FederationMetadataParser,
        "parse_federation_metadata",
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

    out = StringIO()
    # We use the same backend several times... spare the definition of a new backend only
    # for this test.
    call_command(
        "prefetch_saml_fer_metadata", ["saml_fer", "saml_fer"], stdout=out, verbosity=2
    )

    output = Counter(out.getvalue().splitlines())
    assert output["Refreshing metadata for backend 'saml_fer'"] == 2
    assert output["All metadata caches refreshed"] == 1

    assert get_metadata_mock.call_count == 2
    assert parse_metadata_mock.call_count == 2


def test_command_fails_base_metadata_store(settings):
    settings.AUTHENTICATION_BACKENDS = (
        "social_edu_federation.backends.saml_fer.FERSAMLAuth",
    )
    settings.SOCIAL_AUTH_SAML_FER_FEDERATION_SAML_METADATA_STORE = (
        "social_edu_federation.metadata_store.BaseMetadataStore"
    )

    out = StringIO()
    err = StringIO()
    with pytest.raises(CommandError):
        call_command("prefetch_saml_fer_metadata", ["saml_fer"], stdout=out, stderr=err)

    assert "Refreshing metadata for backend 'saml_fer'" in out.getvalue()
    assert "All metadata caches refreshed" not in out.getvalue()
    assert (
        "BaseMetadataStore does not provide way to refresh the metadata cache"
        in err.getvalue()
    )


def test_command_fails_no_backend_provided(settings):
    out = StringIO()
    err = StringIO()
    with pytest.raises(CommandError):
        call_command("prefetch_saml_fer_metadata", stdout=out, stderr=err)


def test_command_fails_for_unknown_reason(mocker, settings):
    settings.AUTHENTICATION_BACKENDS = (
        "social_edu_federation.backends.saml_fer.FERSAMLAuth",
    )
    settings.SOCIAL_AUTH_SAML_FER_FEDERATION_SAML_METADATA_STORE = (
        "social_edu_federation.django.metadata_store.CachedMetadataStore"
    )
    settings.SOCIAL_AUTH_SAML_FER_FEDERATION_SAML_METADATA_URL = (
        "https://domain.test/metadata/"
    )

    mocker.patch.object(
        FederationMetadataParser,
        "get_metadata",
        side_effect=TimeoutError("timed out"),
    )

    out = StringIO()
    err = StringIO()
    with pytest.raises(CommandError):
        call_command("prefetch_saml_fer_metadata", ["saml_fer"], stdout=out, stderr=err)

    assert "Refreshing metadata for backend 'saml_fer'" in out.getvalue()
    assert "All metadata caches refreshed" not in out.getvalue()
    assert (
        "CachedMetadataStore failed to refresh the metadata cache (timed out)"
        in err.getvalue()
    )
