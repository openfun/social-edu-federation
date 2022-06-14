"""SAML Metadata and response generators for SAML testing"""
import calendar
from datetime import datetime, timedelta

from onelogin.saml2.constants import OneLogin_Saml2_Constants
from onelogin.saml2.metadata import OneLogin_Saml2_Metadata
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from onelogin.saml2.xml_utils import OneLogin_Saml2_XML

from .certificates import get_dev_certificate


_ENTITIES_DESCRIPTOR_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<md:EntitiesDescriptor
    xmlns:ds="http://www.w3.org/2000/09/xmldsig#"
    xmlns:eidas="http://eidas.europa.eu/saml-extensions"
    xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
    xmlns:mdattr="urn:oasis:names:tc:SAML:metadata:attribute"
    xmlns:mdrpi="urn:oasis:names:tc:SAML:metadata:rpi"
    xmlns:mdui="urn:oasis:names:tc:SAML:metadata:ui"
    xmlns:pyff="http://pyff.io/NS"
    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
    xmlns:ser="http://eidas.europa.eu/metadata/servicelist"
    xmlns:shibmd="urn:mace:shibboleth:metadata:1.0"
    xmlns:xrd="http://docs.oasis-open.org/ns/xri/xrd-1.0"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    Name="https://federation.renater.fr/"
    ID="_20220513T084031Z"
    validUntil="{valid_until}"
    cacheDuration="PT10D"
>
    {entity_descriptors}
</md:EntitiesDescriptor>
    """

_ENTITY_DESCRIPTOR_TEMPLATE = """\
<md:EntityDescriptor
    xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
    xmlns:mdui="urn:oasis:names:tc:SAML:metadata:ui"
    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
    entityID="{entity_id}"
>
    <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <md:Extensions>
            <mdui:UIInfo>
                {ui_info_display_names}
                <mdui:Description xml:lang="fr">Some description</mdui:Description>
            </mdui:UIInfo>
        </md:Extensions>
        <md:NameIDFormat>urn:oasis:names:tc:SAML:2.0:nameid-format:transient</md:NameIDFormat>
        <md:SingleSignOnService
            Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
            Location="{sso_location}"
        />
    </md:IDPSSODescriptor>
    <md:Organization>
        {organization_names}
        {organization_display_names}
        <md:OrganizationURL xml:lang="en">https://organization.example.com/</md:OrganizationURL>
    </md:Organization>
    <md:ContactPerson contactType="technical">
        <md:EmailAddress>mailto:technical_contact_person@example.com</md:EmailAddress>
    </md:ContactPerson>
</md:EntityDescriptor>"""


def format_lang_attribute(language_code=None):
    """Formats the language attribute for tags if `language_code` provided."""
    return f'xml:lang="{language_code}"' if language_code else ""


def format_mdui_display_name(display_name, language_code="fr"):
    """Formats the `display_name` for `DisplayName` tag of `UIInfo` block."""
    language_attribute = format_lang_attribute(language_code)
    return f"<mdui:DisplayName {language_attribute}>{display_name}</mdui:DisplayName>"


def format_md_organization_name(name, language_code="fr"):
    """Formats the `name` for `OrganizationName` tag of `Organization` block."""
    language_attribute = format_lang_attribute(language_code)
    return f"<md:OrganizationName {language_attribute}>{name}</md:OrganizationName>"


def format_md_organization_display_name(display_name, language_code="fr"):
    """Formats the `display_name` for `OrganizationDisplayName` tag of `Organization` block."""
    language_attribute = format_lang_attribute(language_code)
    return (
        f"<md:OrganizationDisplayName {language_attribute}>"
        f"{display_name}"
        "</md:OrganizationDisplayName>"
    )


def _add_x509_key_descriptors(metadata, cert) -> str:
    """Highly inspired from OneLogin_Saml2_Metadata.add_x509_key_descriptors"""
    root = OneLogin_Saml2_XML.to_etree(metadata)
    sp_sso_descriptor = next(
        root.iterfind(
            ".//md:IDPSSODescriptor", namespaces=OneLogin_Saml2_Constants.NSMAP
        )
    )
    # pylint:disable=protected-access
    OneLogin_Saml2_Metadata._add_x509_key_descriptors(sp_sso_descriptor, cert, False)
    OneLogin_Saml2_Metadata._add_x509_key_descriptors(sp_sso_descriptor, cert, True)
    # pylint:enable=protected-access
    return OneLogin_Saml2_XML.to_string(root).decode("utf-8")


def generate_idp_metadata(**kwargs):
    """Generates an Entity Descriptor metadata"""
    idp_config = {
        "entity_id": "http://edu.example.com/adfs/services/trust",
        "sso_location": "http://edu.example.com/adfs/sso/",
        "ui_info_display_names": format_mdui_display_name("Edu local IdP"),
        "organization_names": format_md_organization_name("OrganizationName"),
        "organization_display_names": format_md_organization_display_name(
            "OrganizationDName"
        ),
    }

    # Clean eventual arguments
    for key_to_join in (
        "ui_info_display_names",
        "organization_names",
        "organization_display_names",
    ):
        if isinstance(kwargs.get(key_to_join), list):
            kwargs[key_to_join] = "\n".join(kwargs[key_to_join])

    idp_config.update(kwargs)

    metadata = _ENTITY_DESCRIPTOR_TEMPLATE.format(**idp_config)

    return _add_x509_key_descriptors(metadata, get_dev_certificate())


def generate_idp_federation_metadata(entity_descriptor_list=None, **kwargs):
    """Generates a look alike Renater Metadata"""
    entity_descriptor_list = entity_descriptor_list or [generate_idp_metadata()]
    joined_entity_descriptors = "\n".join(entity_descriptor_list)

    metadata_config = {
        "valid_until": OneLogin_Saml2_Utils.parse_time_to_SAML(
            calendar.timegm((datetime.utcnow() + timedelta(days=10)).utctimetuple())
        ),
    }
    metadata_config.update(kwargs)

    entities_descriptor_xml = _ENTITIES_DESCRIPTOR_TEMPLATE.format(
        entity_descriptors=joined_entity_descriptors,
        **metadata_config,
    )

    return entities_descriptor_xml