"""Tests for the social_edu_federation Django integration views"""
from django.urls import reverse

import pytest
from social_django.utils import load_backend, load_strategy

from social_edu_federation.backends.saml_fer import FERSAMLAuth
from social_edu_federation.django.metadata_store import CachedMetadataStore
from social_edu_federation.django.views import (
    EduFedIdpChoiceView,
    EduFedMetadataView,
    InvalidGeneratedMetadataException,
)
from social_edu_federation.parser import FederationMetadataParser


def test_metadata_view(backend_settings, client):
    """Asserts EduFedMetadataView returns valid metadata."""
    response = client.get(reverse("saml_fer_metadata"))

    assert response.status_code == 200
    assert b"md:EntityDescriptor" in response.content
    assert (
        b'<md:AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST" '
        b'Location="http://testserver/complete/saml_fer/" '
        b'index="1"/>'
    ) in response.content

    assert (
        b'<md:OrganizationName xml:lang="en-US">edu-fed</md:OrganizationName>'
    ) in response.content

    assert (
        b'<md:OrganizationDisplayName xml:lang="en-US">'
        b"France Universit&#233; Num&#233;rique"
        b"</md:OrganizationDisplayName>"
    ) in response.content

    assert (
        b'<md:OrganizationURL xml:lang="en-US">edu-fed.example.com</md:OrganizationURL>'
    ) in response.content


def test_metadata_view_with_errors(client, mocker):
    """Asserts EduFedMetadataView manage metadata generation errors."""
    generate_metadata_mock = mocker.patch.object(FERSAMLAuth, "generate_metadata_xml")
    generate_metadata_mock.return_value = ("metadata", ["expired_xml"])

    with pytest.raises(InvalidGeneratedMetadataException):
        client.get(reverse("saml_fer_metadata"))


def expected_idp_button(idp_name, idp_display_name):
    """Helper to generate the expected HTML for a link to IdP in `EduFedIdpChoiceView`."""
    return (
        "<button "
        'class="btn-idp-link" '
        'type="submit" '
        'name="idp" '
        f'value="{idp_name}" '
        f"onclick=\"storeRecentIdpCookie('{idp_name}')\">"
        f"{idp_display_name}"
        "</button>"
    ).encode("utf-8")


def expected_latest_idp_button(idp_name):
    """
    Helper to generate the expected HTML for a link to IdP
    stored in cookies as latest used in `EduFedIdpChoiceView`.

    We only test the beginning of the button because the rest
    is complex to generate and matters not as we only want to assert
    the presence of the button.
    """
    return (
        '<button class="btn-idp-link recently-used-idp" type="submit" name="idp" '
        f'value="{idp_name}">'
    ).encode("utf-8")


def test_idp_choice_view(default_loc_mem_cache, client, mocker, settings):
    """Asserts EduFedIdpChoiceView properly displays the available IdP list."""
    settings.SOCIAL_AUTH_SAML_FER_FEDERATION_SAML_METADATA_URL = (
        "https://domain.test/metadata/"
    )

    get_metadata_mock = mocker.patch.object(FederationMetadataParser, "get_metadata")
    get_metadata_mock.return_value = b"been called"
    parse_metadata_mock = mocker.patch.object(
        FederationMetadataParser, "parse_federation_metadata"
    )
    parse_metadata_mock.return_value = {
        "some-idp": {
            "name": "some-idp",
            "edu_fed_data": {"display_name": "Some IdP display name"},
        },
        "other-idp": {
            "name": "other-idp",
            "edu_fed_data": {"display_name": "Some other IdP display name"},
        },
    }

    response = client.get(reverse("saml_fer_idp_list"))

    assert response.status_code == 200

    get_metadata_mock.assert_called_once_with(
        "https://domain.test/metadata/", timeout=10
    )
    parse_metadata_mock.assert_called_once_with(b"been called")

    assert (
        b'<form action="/login/saml_fer/" method="get" autocomplete="off">'
        in response.content
    )
    assert expected_idp_button("some-idp", "Some IdP display name") in response.content
    assert (
        expected_idp_button("other-idp", "Some other IdP display name")
        in response.content
    )

    # Assert the cache works
    get_metadata_mock.reset_mock()
    parse_metadata_mock.reset_mock()

    response = client.get(reverse("saml_fer_idp_list"))

    assert response.status_code == 200

    assert not get_metadata_mock.called
    assert not parse_metadata_mock.called

    # Check IdP presence again
    assert (
        b'<form action="/login/saml_fer/" method="get" autocomplete="off">'
        in response.content
    )
    assert expected_idp_button("some-idp", "Some IdP display name") in response.content
    assert (
        expected_idp_button("other-idp", "Some other IdP display name")
        in response.content
    )


def test_idp_choice_view_metadata_store_cache_used(
    default_loc_mem_cache,
    client,
    mocker,
):
    """Asserts EduFedIdpChoiceView properly displays the available IdP list."""
    get_metadata_mock = mocker.patch.object(FederationMetadataParser, "get_metadata")
    get_metadata_mock.return_value = b"been called"
    parse_metadata_mock = mocker.patch.object(
        FederationMetadataParser, "parse_federation_metadata"
    )
    parse_metadata_mock.return_value = {
        "some-idp": {
            "name": "some-idp",
            "edu_fed_data": {"display_name": "Some IdP display name"},
        },
        "other-idp": {
            "name": "other-idp",
            "edu_fed_data": {"display_name": "Some other IdP display name"},
        },
    }

    # Preload the metadata store cache
    strategy = load_strategy()
    backend = load_backend(strategy, "saml_fer", redirect_uri=None)
    metadata_store = CachedMetadataStore(backend)
    metadata_store.refresh_cache_entries()

    get_metadata_mock.reset_mock()
    parse_metadata_mock.reset_mock()

    response = client.get(reverse("saml_fer_idp_list"))

    assert response.status_code == 200

    assert not get_metadata_mock.called
    assert not parse_metadata_mock.called

    # Check IdP presence again
    assert (
        b'<form action="/login/saml_fer/" method="get" autocomplete="off">'
        in response.content
    )
    assert expected_idp_button("some-idp", "Some IdP display name") in response.content
    assert (
        expected_idp_button("other-idp", "Some other IdP display name")
        in response.content
    )


def test_idp_choice_view_with_cookie(default_loc_mem_cache, client, mocker):
    """Assert the recently used IdP is displayed properly."""
    mocker.patch.object(FederationMetadataParser, "get_metadata")
    parse_metadata_mock = mocker.patch.object(
        FederationMetadataParser, "parse_federation_metadata"
    )
    parse_metadata_mock.return_value = {
        "some-idp": {
            "name": "some-idp",
            "edu_fed_data": {"display_name": "Some IdP display name"},
        },
        "other-idp": {
            "name": "other-idp",
            "edu_fed_data": {"display_name": "Some other IdP display name"},
        },
    }

    client.cookies.load({"_latest_idps_saml_fer": "other-idp"})

    response = client.get(
        reverse("saml_fer_idp_list"),
    )
    # `recently-used-idp` is in JS + 1 button
    assert b"recently-used-idp" in response.content

    assert expected_idp_button("some-idp", "Some IdP display name") in response.content
    assert expected_latest_idp_button("other-idp") in response.content


def test_idp_choice_view_with_two_cookies(default_loc_mem_cache, client, mocker):
    """Assert the two recently used IdP are displayed properly."""
    mocker.patch.object(FederationMetadataParser, "get_metadata")
    parse_metadata_mock = mocker.patch.object(
        FederationMetadataParser, "parse_federation_metadata"
    )
    parse_metadata_mock.return_value = {
        "some-idp": {
            "name": "some-idp",
            "edu_fed_data": {"display_name": "Some IdP display name"},
        },
        "other-idp": {
            "name": "other-idp",
            "edu_fed_data": {"display_name": "Some other IdP display name"},
        },
    }

    client.cookies.load(
        {"_latest_idps_saml_fer": "some-idp+other-idp"},
    )

    response = client.get(reverse("saml_fer_idp_list"))
    assert b"recently-used-idp" in response.content

    assert expected_latest_idp_button("some-idp") in response.content
    assert expected_latest_idp_button("other-idp") in response.content


def test_idp_choice_view_with_non_existing_cookie(
    default_loc_mem_cache,
    client,
    mocker,
):
    """Asserts the cookie containing an IdP which does not exist anymore does nothing."""
    mocker.patch.object(FederationMetadataParser, "get_metadata")
    parse_metadata_mock = mocker.patch.object(
        FederationMetadataParser, "parse_federation_metadata"
    )
    parse_metadata_mock.return_value = {
        "some-idp": {
            "name": "some-idp",
            "edu_fed_data": {"display_name": "Some IdP display name"},
        },
        "other-idp": {
            "name": "other-idp",
            "edu_fed_data": {"display_name": "Some other IdP display name"},
        },
    }

    client.cookies.load(
        {"_latest_idps_saml_fer": "0th-identity-provider"},  # missing IdP
    )
    response = client.get(reverse("saml_fer_idp_list"))

    assert expected_idp_button("some-idp", "Some IdP display name") in response.content
    assert (
        expected_idp_button("other-idp", "Some other IdP display name")
        in response.content
    )


def test_idp_choice_view_real_world_example(
    default_loc_mem_cache,
    client,
    live_server,
    settings,
):
    """Asserts EduFedIdpChoiceView properly displays the available IdP list."""
    settings.SOCIAL_AUTH_SAML_FER_FEDERATION_SAML_METADATA_URL = (
        f'{live_server}{reverse("real_world_metadata")}'
    )

    response = client.get(reverse("saml_fer_idp_list"))

    assert response.status_code == 200

    assert (
        b'<form action="/login/saml_fer/" method="get" autocomplete="off">'
        in response.content
    )

    # check random IdP presence
    assert (
        expected_idp_button("idp-test-jamssn", "Idp test jams.sn") in response.content
    )


def test_idp_choice_redirects_already_logged_in_users(client, django_user_model):
    """Asserts an already authenticated user is redirected to the home page"""
    username = "morty"
    password = "iammorty"
    django_user_model.objects.create_user(username=username, password=password)
    client.login(username=username, password=password)
    response = client.get(reverse("saml_fer_idp_list"))
    assert response.status_code == 302
    assert response["Location"] == "/"


def test_views_require_backend_name():
    """Simple test to assert the view use raises and error if the backend name is not provided."""
    with pytest.raises(
        RuntimeError,
        match=(
            "EduFedMetadataView `as_view` must be "
            "called with `backend_name` keyword argument"
        ),
    ):
        EduFedMetadataView.as_view()(None)

    with pytest.raises(
        RuntimeError,
        match=(
            "EduFedIdpChoiceView `as_view` must be "
            "called with `backend_name` keyword argument"
        ),
    ):
        EduFedIdpChoiceView.as_view()(None)
