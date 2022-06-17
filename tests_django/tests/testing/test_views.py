"""Tests for the social_edu_federation Django integration testing views"""
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
    response = client.get(
        f'{reverse("social:begin", args=("saml_fer",))}?idp=local-accepting-idp',
        follow=True,
    )

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
