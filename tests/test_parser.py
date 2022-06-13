"""Test module for the SAML metadata parser."""
import pytest

from social_edu_federation.parser import FederationMetadataParser
from social_edu_federation.testing.saml_tools import (
    format_mdui_display_name,
    generate_idp_federation_metadata,
    generate_idp_metadata,
)

from .utils import get_resource_filename


def test_idp_no_display_name():
    """Assert the parser uses `entityId` when no display name provided in metadata."""
    idp_metadata = generate_idp_metadata(
        ui_info_display_names="",
    )
    fed_metadata = generate_idp_federation_metadata(
        entity_descriptor_list=[idp_metadata]
    )

    identity_providers = FederationMetadataParser.parse_federation_metadata(
        fed_metadata
    )

    assert len(identity_providers) == 1
    assert "httpeduexamplecomadfsservicestrust" in identity_providers

    idp_config = identity_providers["httpeduexamplecomadfsservicestrust"]

    assert idp_config["entityId"] == "http://edu.example.com/adfs/services/trust"
    assert idp_config["name"] == "httpeduexamplecomadfsservicestrust"
    assert idp_config["singleSignOnService"] == {
        "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
        "url": "http://edu.example.com/adfs/sso/",
    }
    assert "singleLogoutService" not in idp_config
    assert idp_config["edu_fed_data"] == {
        "display_name": "http://edu.example.com/adfs/services/trust",
        "organization_display_name": "OrganizationDName",
        "organization_name": "OrganizationName",
    }
    assert idp_config["x509cert"].startswith(
        "MIIFdjCCA14CAQAwDQYJKoZIhvcNAQENBQAwgYAxCzAJ"
    )


@pytest.mark.parametrize(
    "language_code",
    [None, "en", "cz"],
)
def test_idp_other_display_name(language_code):
    """Assert the parser uses any display name when not available in French."""
    idp_metadata = generate_idp_metadata(
        ui_info_display_names=format_mdui_display_name(
            "Some name", language_code=language_code
        ),
    )
    fed_metadata = generate_idp_federation_metadata(
        entity_descriptor_list=[idp_metadata]
    )

    identity_providers = FederationMetadataParser.parse_federation_metadata(
        fed_metadata
    )

    assert len(identity_providers) == 1
    assert "some-name" in identity_providers

    idp_config = identity_providers["some-name"]

    assert idp_config["name"] == "some-name"
    assert idp_config["edu_fed_data"]["display_name"] == "Some name"


def test_idp_fr_display_name():
    """Assert the French display is always preferred."""
    idp_metadata = generate_idp_metadata(
        ui_info_display_names=[
            format_mdui_display_name("English name", language_code="en"),
            format_mdui_display_name("Nom français", language_code="fr"),
        ],
    )
    fed_metadata = generate_idp_federation_metadata(
        entity_descriptor_list=[idp_metadata]
    )

    identity_providers = FederationMetadataParser.parse_federation_metadata(
        fed_metadata
    )

    assert len(identity_providers) == 1
    assert "nom-francais" in identity_providers

    idp_config = identity_providers["nom-francais"]

    assert idp_config["name"] == "nom-francais"
    assert idp_config["edu_fed_data"]["display_name"] == "Nom français"


def test_renater_idps_metadata():
    """Asserts a real world example is parsed without error."""
    with open(get_resource_filename("real-world-metadata.xml"), "rb") as metadata_fd:
        metadata = metadata_fd.read()

    identity_providers = FederationMetadataParser.parse_federation_metadata(metadata)

    assert len(identity_providers) == 308
    assert identity_providers["idp-de-test-mathrice-plm-team-bdx-novembre-2016"] == {
        "edu_fed_data": {
            "display_name": "idp de test\nmathrice-plm-team-bdx-novembre-2016\n",
            "organization_display_name": "",
            "organization_name": "",
        },
        "entityId": "http://idp-pre.math.cnrs.fr/idp/shibboleth",
        "name": "idp-de-test-mathrice-plm-team-bdx-novembre-2016",
        "singleLogoutService": {
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            "url": "http://idp-pre.math.cnrs.fr/idp/profile/SAML2/Redirect/SLO",
        },
        "singleSignOnService": {
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            "url": "http://idp-pre.math.cnrs.fr/idp/profile/SAML2/Redirect/SSO",
        },
        "x509cert": (
            "MIIDOzCCAiOgAwIBAgIUJmM6xYA63wKPLiNKcG6DI+KfMYYwDQYJKoZIhvcNAQEL"
            "BQAwHzEdMBsGA1UEAwwUaWRwLXByZS5tYXRoLmNucnMuZnIwHhcNMTYxMTE2MTUx"
            "MjAzWhcNMzYxMTE2MTUxMjAzWjAfMR0wGwYDVQQDDBRpZHAtcHJlLm1hdGguY25y"
            "cy5mcjCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAJxkDb8nmhvbe5Sz"
            "dckIfcDbIleveOMaBNGCPmpmzYuv+ItPX8C3L5Ryb6WYYRcv6js4q7LemiJ0OkpS"
            "nD9uNFz+VWpGAgoS11StA7UGXfiMOJkA4mSGL5kQDU3r8FWO9JQPRquFX5z1nyrB"
            "8WmDU8tR6Az+4qovFYwBJgqZ3XcLe20jItaUtucXZqbhQMoE4/UnPXzAkuNgfc5R"
            "ux9mwvIrIONPlhm5YohcsK0nAC5MrGQD88z/E94loS3MXM/o00O3uVK970j2LUDE"
            "SYJji60VfWZSo72RpK1KTFZg1MXfZG/mlvpBEnFJelLS0ZtzweAbGrWFwAltm+32"
            "fOjEJuMCAwEAAaNvMG0wHQYDVR0OBBYEFBL4FePINAvCMCJUUat5ZPznB4X8MEwG"
            "A1UdEQRFMEOCFGlkcC1wcmUubWF0aC5jbnJzLmZyhitodHRwczovL2lkcC1wcmUu"
            "bWF0aC5jbnJzLmZyL2lkcC9zaGliYm9sZXRoMA0GCSqGSIb3DQEBCwUAA4IBAQBT"
            "egnWM+/cWP5cEIFC/9dZVJ3ZtryaQaeipfhlGKDZybonifmNZfXyDnfh1X9UlB4j"
            "fWWJY4fJ/ZfJvJ6VTL5kU4b1PPY81QqzsRhhsMe5OLl9f4HZNhUuIxzIuwv+3gtN"
            "fXUxSB+iy5PPkgP7T+/7dRFEPym88CtWh2osT7STx87fhqaksyHAX0zpNs8Zs4cV"
            "ogmPeIhP8FGG8eTOyuLKSVE32jl4OlmQqpmyEABoKz5PVmJD/iRVSpvYu4IrGbo6"
            "DuE8DAZbM+WVzVB27FGSjYnxoAY7H1EClMQ1TGUg6eEP9RkWzjWoEZZyAIpjFHdE"
            "zfif9VATaFW9Mr2e0S/4"
        ),
    }
