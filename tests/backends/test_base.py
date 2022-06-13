"""`social_edu_federation` base backend tests."""
import pytest
from social_core.tests.models import TestStorage
from social_core.tests.strategy import TestStrategy

from social_edu_federation.backends.base import (
    EduFedSAMLAuth,
    EduFedSAMLIdentityProvider,
)
from social_edu_federation.metadata_store import BaseMetadataStore


def test_idp_create_from_config_dict():
    """This is coverage unit test of `create_from_config_dict` method."""
    idp = EduFedSAMLIdentityProvider.create_from_config_dict(
        **{
            "name": "idp-displayable-name",
            "entityId": "http://idp.domain/adfs/services/trust",
            "singleSignOnService": {
                "url": "https://idp.domain/adfs/ls/",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "singleLogoutService": {
                "url": "https://idp.domain/adfs/ls/",
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            # certificate is not validated on creation...
            "x509cert": "MIIC4DCCAcigAwIBAgIQG...CQZXu/agfMc/tY+miyrD0=",
            "edu_fed_data": {
                "display_name": "IdP displayable name",
                "organization_name": "Organization",
                "organization_display_name": "Organization displayable name",
            },
            # Note the following key will not be passed to the configuration
            "key_not_in_edu_fed_data": "missing",
        }
    )

    assert idp.name == "idp-displayable-name"
    assert idp.conf == {
        "entity_id": "http://idp.domain/adfs/services/trust",
        "slo_url": "https://idp.domain/adfs/ls/",
        "url": "https://idp.domain/adfs/ls/",
        "x509cert": "MIIC4DCCAcigAwIBAgIQG...CQZXu/agfMc/tY+miyrD0=",
        "x509certMulti": None,
        "edu_fed_display_name": "IdP displayable name",
        "edu_fed_organization_display_name": "Organization displayable name",
        "edu_fed_organization_name": "Organization",
    }
    # Make it explicit:
    assert "key_not_in_edu_fed_data" not in idp.conf


def test_sp_federation_metadata_url():
    """This is coverage unit test of `get_federation_metadata_url` method."""
    strategy = TestStrategy(TestStorage)
    backend = EduFedSAMLAuth(strategy)
    strategy.set_settings(
        {
            "SOCIAL_AUTH_BASE_EDU_FED_BACKEND_FEDERATION_SAML_METADATA_URL": "easy_to_find"
        }
    )
    assert backend.get_federation_metadata_url() == "easy_to_find"


def test_sp_get_idp(mocker):
    """This is coverage unit test of `get_idp` method."""
    strategy = TestStrategy(TestStorage)
    backend = EduFedSAMLAuth(strategy)
    store_get_idp_mock = mocker.patch.object(BaseMetadataStore, "get_idp")
    store_get_idp_mock.return_value = True
    assert backend.get_idp("some-idp")
    store_get_idp_mock.assert_called_once_with("some-idp")


def test_sp_get_idp_fail_module_does_not_exists():
    """This is coverage unit test of `get_idp` method with setting change."""
    strategy = TestStrategy(TestStorage)
    backend = EduFedSAMLAuth(strategy)
    strategy.set_settings(
        {
            "SOCIAL_AUTH_BASE_EDU_FED_BACKEND_FEDERATION_SAML_METADATA_STORE": (
                "does.not.exist"
            ),
        }
    )
    with pytest.raises(ModuleNotFoundError):
        backend.get_idp("some-idp")


def test_sp_get_idp_fail_class_does_not_exists():
    """This is coverage unit test of `get_idp` method with setting change."""
    strategy = TestStrategy(TestStorage)
    backend = EduFedSAMLAuth(strategy)
    strategy.set_settings(
        {
            "SOCIAL_AUTH_BASE_EDU_FED_BACKEND_FEDERATION_SAML_METADATA_STORE": (
                "social_edu_federation.metadata_store.ClassDoesNotExit"
            ),
        }
    )
    with pytest.raises(ImportError):
        backend.get_idp("some-idp")
