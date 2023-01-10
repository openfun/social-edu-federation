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
        "logo": (
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgd"
            "z34AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAApgAAAKYB3X3/OAAAABl0RVh0"
            "U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAANCSURBVEiJtZZPbBtFFMZ"
            "/M7ubXdtdb1xSFyeilBapySVU8h8OoFaooFSqiihIVIpQBKci6KEg9Q6H9kovIH"
            "oCIVQJJCKE1ENFjnAgcaSGC6rEnxBwA04Tx43t2FnvDAfjkNibxgHxnWb2e/u99"
            "2bee7tCa00YFsffekFY+nUzFtjW0LrvjRXrCDIAaPLlW0nHL0SsZtVoaF98mLrx"
            "3pdhOqLtYPHChahZcYYO7KvPFxvRl5XPp1sN3adWiD1ZAqD6XYK1b/dvE5IWryT"
            "t2udLFedwc1+9kLp+vbbpoDh+6TklxBeAi9TL0taeWpdmZzQDry0AcO+jQ12Ryo"
            "hqqoYoo8RDwJrU+qXkjWtfi8Xxt58BdQuwQs9qC/afLwCw8tnQbqYAPsgxE1S6F"
            "3EAIXux2oQFKm0ihMsOF71dHYx+f3NND68ghCu1YIoePPQN1pGRABkJ6Bus96Cu"
            "tRZMydTl+TvuiRW1m3n0eDl0vRPcEysqdXn+jsQPsrHMquGeXEaY4Yk4wxWcY5V"
            "/9scqOMOVUFthatyTy8QyqwZ+kDURKoMWxNKr2EeqVKcTNOajqKoBgOE28U4tdQ"
            "l5p5bwCw7BWquaZSzAPlwjlithJtp3pTImSqQRrb2Z8PHGigD4RZuNX6JYj6wj7"
            "O4TFLbCO/Mn/m8R+h6rYSUb3ekokRY6f/YukArN979jcW+V/S8g0eT/N3VN3kTq"
            "WbQ428m9/8k0P/1aIhF36PccEl6EhOcAUCrXKZXXWS3XKd2vc/TRBG9O5ELC17M"
            "mWubD2nKhUKZa26Ba2+D3P+4/MNCFwg59oWVeYhkzgN/JDR8deKBoD7Y+ljEjGZ"
            "0sosXVTvbc6RHirr2reNy1OXd6pJsQ+gqjk8VWFYmHrwBzW/n+uMPFiRwHB2I7i"
            "h8ciHFxIkd/3Omk5tCDV1t+2nNu5sxxpDFNx+huNhVT3/zMDz8usXC3ddaHBj1G"
            "Hj/As08fwTS7Kt1HBTmyN29vdwAw+/wbwLVOJ3uAD1wi/dUH7Qei66PfyuRj4Ik"
            "9is+hglfbkbfR3cnZm7chlUWLdwmprtCohX4HUtlOcQjLYCu+fzGJH2QRKvP3UN"
            "z8bWk1qMxjGTOMThZ3kvgLI5AzFfo379UAAAAASUVORK5CYII="
        ),
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
            "logo": "",
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

    assert identity_providers["centre-hospitalier-universitaire-de-limoges"] == {
        "edu_fed_data": {
            "display_name": "Centre Hospitalier Universitaire de Limoges\n",
            "organization_display_name": "CHU de Limoges",
            "organization_name": "CHU de Limoges",
            "logo": (
                "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9h"
                "AAAACXBIWXMAAC4jAAAuIwF4pT92AAAB6klEQVR42qWTTWsTURSG+zcEF+78BYJrce"
                "Han+BCQdqFYKxiUwtupFBoIzSpkeajWAsuGjNJtaHVNGmatMVmhphEk6YSaWWSfuSj"
                "mqaTzDxORtQEi0Z94YXL4Z7n3HM4twfoafPQXzhIW2KHasdlGuox3egHQC1XUDKbaJ"
                "rKk/WrrGw50OpV1Oqn7gAlkxn5/EW0RgP32hViH9wcxSxUpy6hNZXfAgzt95rYOXWW"
                "5v4BaXlRb6PEZ38fhzOXuwOoB3qC6ynK+yxS7hnFfADlYwS1XvljCyzmq4ysF1GaGs"
                "WbZgKDF3i3fJvGzpuuhkjfwjanbSns0h43TJOE7z/g4ZiFOcGD4PUaF/2CD7/PZ5xf"
                "zr3oBAibFYYiMqm9I85NiUzYJlAUhXAozJ1b/Ty227k3YMbpcBhJbqfr1xlomsZu7Q"
                "vXFuYZtVpJp9LMTE8zMjzM2uoqg3cHsIyO8TaRwOVwdgIq9Tq9rwNcfzXP9mGVSDqF"
                "bXwcURSJRaMGfCkYJL6xgVWPFwqFTkCuXOLMpJX+ZWM7kWWZZDJJJpNBkiTEeJytXM"
                "6o/t2qqv4EqHqFRwkRafcbudV/rVYjm83imZ01Bun1PMcnCEa85darOOkftCufzxPV"
                "W1iJRAxQaClEQ9/UExfpX/XfgK9hJqAg9gc+TgAAAABJRU5ErkJggg=="
            ),
        },
        "entityId": "http://auth.chu-limoges.fr/adfs/services/trust",
        "name": "centre-hospitalier-universitaire-de-limoges",
        "singleLogoutService": {
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            "url": "https://auth.chu-limoges.fr/adfs/ls/",
        },
        "singleSignOnService": {
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            "url": "https://auth.chu-limoges.fr/adfs/ls/",
        },
        "x509cert": (
            "MIIC4jCCAcqgAwIBAgIQVvZQS8VqPZBDOtoSFpZqCDANBgkqhkiG9w0BAQsFADAt"
            "MSswKQYDVQQDEyJBREZTIFNpZ25pbmcgLSBhdXRoLmNodS1saW1vZ2VzLmZyMB4X"
            "DTIxMDQxMjEzMDA1MFoXDTIyMDQxMjEzMDA1MFowLTErMCkGA1UEAxMiQURGUyBT"
            "aWduaW5nIC0gYXV0aC5jaHUtbGltb2dlcy5mcjCCASIwDQYJKoZIhvcNAQEBBQAD"
            "ggEPADCCAQoCggEBAJaaXamgmPnMIhthb9Y/1KJPx5W4VMoAyUvaNGWdP+FdRejU"
            "AagNL2FZhryuap0N5q/XFy6iZWoor4/YZo4lm1OCjb+ck2USG6WmTqqyJtBkECB2"
            "wWjpkRfqVm65Aabez1jwNFXeJcTx7UslSSQXeHYBDBSr5swSuk5VZKJpCdQAodFh"
            "O4S4Qs3YKiGDx9FOYIhLWxvhIuqmr3sOEUF84pxZxUVTb2D1U5LzRUxX9LBuUbk/"
            "PsLviQYJEkRs72sajDAzvwwrP0Iv2ewz12vCbrwkUAIyDkmIn39wqN01anvQ3eK5"
            "gaV3HRy2G/h2lFC6kC0LrblCVtj6BFuWOjKLboMCAwEAATANBgkqhkiG9w0BAQsF"
            "AAOCAQEABcGrSH24Grn5CBm6XCPPsHM/bHQpjv4OJKHhoRgIYzw0f7X2h87jQMs3"
            "87KOEEqEuzp9jDmtep8SnITUMFvJ4SJqX58VOrbnkt/MsfdnXXSh4Bh7U08S5Jvv"
            "4vlzYKe1W+Dudsrj7+/EJiorUdo5/Mdb5BVEEatqBcXEv6990rv8ilNxgBakbJrp"
            "zohfpxuiGRo/4cnKfe5okZ3bOQ+VWNc95n+5b/Jp+0Wu17B49Y+hgB19t1cbnsqK"
            "nl2YHnY9XQCqq5Au4GhmDWYuessD3vviQrux+t/IBbYEw8s7KugEAmX3W+FjO5MV"
            "rMN4tw3LLMDGO89uGyVEHNeR8LNXSQ=="
        ),
    }
