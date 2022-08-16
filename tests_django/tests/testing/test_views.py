"""Tests for the social_edu_federation Django integration testing views"""
import urllib.parse

from django.contrib.auth import get_user as auth_get_user
from django.core.cache import caches
from django.urls import reverse

import pytest

from social_edu_federation.django.testing.views import (
    FederationMetadataFromLocalFileView,
)


def test_idp_metadata_view(client):
    """Asserts EduFedMetadataView returns valid metadata."""
    response = client.get(reverse("social_edu_federation_django_testing:idp_metadata"))

    assert response.status_code == 200
    assert b"md:EntityDescriptor" in response.content


def test_idp_metadata_view_with_port_override(client, settings):
    """Asserts EduFedMetadataView returns valid metadata."""
    settings.SOCIAL_AUTH_SAML_FER_IDP_FAKER_DOCKER_PORT = 8060

    response = client.get(
        reverse("social_edu_federation_django_testing:idp_metadata"),
        SERVER_PORT=8000,
    )

    assert response.status_code == 200
    assert b"md:EntityDescriptor" in response.content
    assert b"http://testserver:8060/saml/idp/sso/" in response.content


def test_full_login_process(backend_settings, client, live_server, settings):
    """Asserts the nominal login process works."""
    settings.SOCIAL_AUTH_SAML_FER_FEDERATION_SAML_METADATA_URL = (
        f'{live_server}{reverse("social_edu_federation_django_testing:idp_metadata")}'
    )
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        },
    }

    # Force cache list reloading
    del caches.settings

    # 1/ Select Idp in the provider list
    response = client.get(
        reverse("saml_fer_idp_list"),
    )
    assert response.status_code == 200
    assert (
        f'action="{reverse("social:begin", args=("saml_fer",))}"'.encode("utf-8")
        in response.content
    )
    assert b"local-accepting-idp" in response.content

    response = client.get(
        f'{reverse("social:begin", args=("saml_fer",))}?idp=local-accepting-idp',
    )
    assert response.status_code == 302
    assert response["Location"].startswith(f"{live_server}/saml/idp/sso/?SAMLRequest=")

    # 2/ Follow the redirection to the SSO
    user_login_url = response["Location"]
    # We need to enforce domain/port for live server as it is hardcoded in test client
    parsed_url = urllib.parse.urlparse(user_login_url)
    live_server_name, live_server_port = parsed_url.netloc.split(":")
    response = client.get(
        user_login_url,
        SERVER_NAME=live_server_name,
        SERVER_PORT=live_server_port,
    )

    # 3/ Fill form and post
    form = response.context["user_description_form"]
    assert (
        form.initial["acs_url"]
        == f'http://testserver{reverse("social:complete", args=("saml_fer",))}'
    )
    data = form.initial
    data["surname"] = "Doe"
    data["given_name"] = "John"

    response = client.post(
        user_login_url,
        data=data,
        SERVER_NAME=live_server_name,
        SERVER_PORT=live_server_port,
    )
    assert "user_description_form" not in response.context

    # 3/ Fetch the fake SSO response and POST the data to our endpoint
    assert (
        response.context["acs_url"]
        == f'http://testserver{reverse("social:complete", args=("saml_fer",))}'
    )
    response = client.post(
        response.context["acs_url"],
        data={
            "RelayState": response.context["saml_relay_state"],
            "SAMLResponse": response.context["auth_response"],
        },
    )
    assert response.status_code == 302
    assert response["Location"] == "/"

    # Assert the user is authenticated
    user = auth_get_user(client)
    assert user.is_authenticated


def test_metadata_from_local_file_view_requires_file_name():
    """Simple test to assert the view requires a `file_path` keyword argument."""
    with pytest.raises(
        RuntimeError,
        match=(
            "FederationMetadataFromLocalFileView `as_view` "
            "must be called with `file_path` keyword argument"
        ),
    ):
        FederationMetadataFromLocalFileView.as_view()(None)
