"""
SAML FER backend tests.

Highly inspired from
    https://github.com/python-social-auth/
    social-core/blob/master/social_core/tests/backends/test_saml.py
but using pytest instead of inherit from the base test case class.
Using the social-core base test class would have lead to a massive copy past of code
and would not have been more maintainable.
These fixtures also add more flexibility in tests by generating the SAML response.
"""
from urllib.parse import parse_qs, urlparse

from httpretty import HTTPretty
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from onelogin.saml2.xml_utils import OneLogin_Saml2_XML
import pytest
import requests
from social_core.backends.utils import load_backends, user_backends_data
from social_core.exceptions import AuthMissingParameter
from social_core.tests.models import (
    TestAssociation,
    TestCode,
    TestNonce,
    TestStorage,
    TestUserSocialAuth,
    User,
)
from social_core.tests.strategy import TestStrategy
from social_core.utils import module_member, url_add_parameters

from social_edu_federation.backends.saml_fer import FERSAMLIdentityProvider
from social_edu_federation.testing.saml_tools import (
    generate_auth_response,
    generate_idp_federation_metadata,
)
from social_edu_federation.testing.settings import saml_fer_settings


# Following lines allows same test as social_core.tests.backends.test_saml.py
BACKEND_PATH = "social_edu_federation.backends.saml_fer.FERSAMLAuth"
RAW_COMPLETE_URL = "/complete/{0}"


def extract_query_from_url(url) -> dict:
    """
    Extract a query dict from `url`.

    Turns `domain.com/path/?query_1=toto&query_2=tutu` into
    a dict `{'query_1': 'toto', 'query_2': 'tutu'}`
    """
    return {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}


@pytest.fixture(name="backend_settings")
def backend_settings_fixture():
    """Fixture providing the backend settings"""
    # Use the default testing settings only for now
    return saml_fer_settings


@pytest.fixture(name="base_backend")
def base_backend_fixture(backend_settings):
    """Pytest fixture corresponding to social_core's `BaseBackendTest` setup and tear down."""

    # setup
    HTTPretty.enable(allow_net_connect=False)
    backend_class = module_member(BACKEND_PATH)
    strategy = TestStrategy(TestStorage)
    backend = backend_class(strategy, redirect_uri="")
    complete_url = strategy.build_absolute_uri(RAW_COMPLETE_URL.format(backend.name))
    backends = (
        BACKEND_PATH,
        "social_core.tests.backends.test_broken.BrokenBackendAuth",
    )
    strategy.set_settings(
        {"SOCIAL_AUTH_AUTHENTICATION_BACKENDS": backends, **backend_settings}
    )

    # Force backends loading to trash PSA cache
    load_backends(backends, force_load=True)
    User.reset_cache()
    TestUserSocialAuth.reset_cache()
    TestNonce.reset_cache()
    TestAssociation.reset_cache()
    TestCode.reset_cache()

    yield strategy, backend, complete_url

    # tearDown
    HTTPretty.disable()
    HTTPretty.reset()
    User.reset_cache()
    TestUserSocialAuth.reset_cache()
    TestNonce.reset_cache()
    TestAssociation.reset_cache()
    TestCode.reset_cache()


@pytest.fixture(name="do_start")
def do_start_fixture():
    """Pytest fixture corresponding to social_core's `BaseBackendTest.do_start` method."""

    def _do_start(strategy, backend, username="student_name"):
        start_url = backend.start().url
        # If the SAML Identity Provider recognizes the user, we will
        # be redirected back to:
        return_url = backend.redirect_uri

        # Generate SAML response using SAML request
        query_values = extract_query_from_url(start_url)
        saml_request = query_values["SAMLRequest"]
        saml_relay_state = query_values["RelayState"]
        readable_saml_request = OneLogin_Saml2_Utils.decode_base64_and_inflate(
            saml_request,
        )
        saml_request = OneLogin_Saml2_XML.to_etree(readable_saml_request)
        saml_acs_url = saml_request.get("AssertionConsumerServiceURL")
        request_id = saml_request.get("ID")

        auth_response = OneLogin_Saml2_Utils.b64encode(
            generate_auth_response(request_id, saml_acs_url, email=username)
        )

        response_url = url_add_parameters(
            saml_acs_url,
            {"RelayState": saml_relay_state, "SAMLResponse": auth_response},
        )

        HTTPretty.register_uri(
            HTTPretty.GET, start_url, status=301, location=response_url
        )
        HTTPretty.register_uri(
            HTTPretty.GET, return_url, status=200, body="welcome to return page"
        )

        response = requests.get(start_url)
        assert response.url.startswith(return_url)
        assert response.text == "welcome to return page"
        query_values = extract_query_from_url(response.url)
        assert " " not in query_values["SAMLResponse"]
        strategy.set_request_data(query_values, backend)
        return backend.complete()

    return _do_start


@pytest.fixture(name="do_login")
def do_login_fixture(do_start):
    """Pytest fixture corresponding to social_core's `BaseBackendTest.do_login` method."""

    def _do_login(strategy, backend, expected_username="student_name@edu.fed"):
        user = do_start(strategy, backend, username=expected_username)
        username = expected_username

        assert user.username == username
        assert strategy.session_get("username") == username
        assert strategy.get_user(user.id) == user
        assert backend.get_user(user.id) == user

        user_backends = user_backends_data(
            user,
            strategy.get_setting("SOCIAL_AUTH_AUTHENTICATION_BACKENDS"),
            strategy.storage,
        )

        assert len(list(user_backends.keys())) == 3
        assert "associated" in user_backends
        assert "not_associated" in user_backends
        assert "backends" in user_backends
        assert len(user_backends["associated"]) == 1
        assert len(user_backends["not_associated"]) == 1
        assert len(user_backends["backends"]) == 2

        return user

    return _do_login


def test_metadata_generation(base_backend):
    """Test that we can generate the metadata without error"""
    _strategy, backend, _complete_url = base_backend

    xml, errors = backend.generate_metadata_xml()
    assert len(errors) == 0
    assert xml.decode()[0] == "<"


def test_login_no_idp(base_backend, do_start):
    """Logging in without an idp param should raise AuthMissingParameter"""
    strategy, backend, _complete_url = base_backend

    with pytest.raises(AuthMissingParameter):
        do_start(strategy, backend)


def test_login(backend_settings, base_backend, do_login):
    """Test that we can authenticate with a SAML IdP (TestShib)"""
    strategy, backend, _complete_url = base_backend

    # Mock the federation metadata URL
    HTTPretty.register_uri(
        HTTPretty.GET,
        backend_settings["SOCIAL_AUTH_SAML_FER_FEDERATION_SAML_METADATA_URL"],
        status=200,
        body=generate_idp_federation_metadata(),
    )

    # pretend we've started with a URL like /login/saml/?idp=testshib:
    strategy.set_request_data({"idp": "edu-local-idp"}, backend)
    do_login(strategy, backend)


# Following lines are more specific tests
def test_idp_default_settings():
    """Asserts the default IdP attributes are the ones expected."""
    idp = FERSAMLIdentityProvider("idp-name")
    assert idp.conf == {
        "attr_user_permanent_id": "urn:oid:1.3.6.1.4.1.5923.1.1.1.6",  # eduPersonPrincipalName
        "attr_full_name": "urn:oid:2.16.840.1.113730.3.1.241",  # displayName
        "attr_first_name": "urn:oid:2.5.4.42",  # givenName
        "attr_last_name": "urn:oid:2.5.4.4",  # sn
        "attr_username": "urn:oid:0.9.2342.19200300.100.1.3",  # mail
        "attr_email": "urn:oid:0.9.2342.19200300.100.1.3",  # mail
        "attr_role": "urn:oid:1.3.6.1.4.1.5923.1.1.1.1",  # eduPersonAffiliation
    }


def test_idp_overridden_setting():
    """Asserts we can override IdP attributes."""
    idp = FERSAMLIdentityProvider("idp-name", attr_username="whatever")
    assert idp.conf["attr_username"] == "whatever"


def test_sp_get_user_details():
    """Asserts the Service Provider parse the response attributes as expected."""
    idp = FERSAMLIdentityProvider("idp-name")
    details = idp.get_user_details(
        {
            "urn:oid:1.3.6.1.4.1.5923.1.1.1.6": "eduPersonPrincipalName",
            "urn:oid:2.16.840.1.113730.3.1.241": "displayName",
            "urn:oid:2.5.4.42": "givenName",
            "urn:oid:2.5.4.4": "surname",
            "urn:oid:0.9.2342.19200300.100.1.3": "mail",
            "urn:oid:1.3.6.1.4.1.5923.1.1.1.1": "eduPersonAffiliation",
        }
    )

    assert details == {
        "fullname": "displayName",
        "first_name": "givenName",
        "last_name": "surname",
        "username": "mail",
        "email": "mail",
        "role": "eduPersonAffiliation",
    }
