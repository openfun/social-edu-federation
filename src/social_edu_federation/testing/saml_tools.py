"""SAML Metadata and response generators for SAML testing"""
import calendar
from datetime import datetime, timedelta
import uuid

from onelogin.saml2.constants import OneLogin_Saml2_Constants
from onelogin.saml2.metadata import OneLogin_Saml2_Metadata
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from onelogin.saml2.xml_utils import OneLogin_Saml2_XML
from signxml import XMLSigner

from .certificates import get_dev_certificate, get_dev_private_key


_AUTH_RESPONSE_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<saml2p:Response ID="_885e05fc3bae1925e730e0e9d5c4e1cd"
    InResponseTo="{in_response_to}"
    IssueInstant="2022-05-17T13:00:29.472Z"
    Version="2.0"
    xmlns:saml2p="urn:oasis:names:tc:SAML:2.0:protocol"
>
    <saml2:Issuer xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion">{issuer}</saml2:Issuer>
    <saml2p:Status>
        <saml2p:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/>
    </saml2p:Status>
    <saml2:Assertion ID="_1ee4d12dc0a92300cfb40c8156157708"
        IssueInstant="2022-05-17T13:00:29.472Z" Version="2.0"
        xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    >
        <saml2:Issuer>{issuer}</saml2:Issuer>
        <ds:Signature
            xmlns:ds="http://www.w3.org/2000/09/xmldsig#"
            Id="placeholder"
        ></ds:Signature>
        <saml2:Subject>
            <saml2:NameID
                Format="urn:oasis:names:tc:SAML:2.0:nameid-format:transient"
                NameQualifier="{issuer}"
                SPNameQualifier="edu-fed"
                xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion"
            >
                AAdzZWNyZXQx8FkJgLzpWsL9G4Mauc9xXvhUvdKaxTH8l4KW488QIIcn++
                uJqZodQEnOPyQtB2vU3vNlXDdYkJCbS8q8ZWuGAqceE0Xzgq7ojC1c9jM=
            </saml2:NameID>
            <saml2:SubjectConfirmation Method="urn:oasis:names:tc:SAML:2.0:cm:bearer">
                <saml2:SubjectConfirmationData Address="62.35.89.32"
                    InResponseTo="{in_response_to}"
                    NotOnOrAfter="{valid_until}"
                    Recipient="{acs_url}"
                />
            </saml2:SubjectConfirmation>
        </saml2:Subject>
        <saml2:Conditions
            NotBefore="2022-05-17T13:00:29.472Z"
            NotOnOrAfter="{valid_until}"
        >
            <saml2:AudienceRestriction>
                <saml2:Audience>edu-fed</saml2:Audience>
            </saml2:AudienceRestriction>
        </saml2:Conditions>
        <saml2:AuthnStatement
            AuthnInstant="2022-05-17T13:00:26.365Z"
            SessionIndex="_56c3b72bf3594719715df05ef75461f0"
        >
            <saml2:SubjectLocality Address="62.35.89.32"/>
            <saml2:AuthnContext>
                <saml2:AuthnContextClassRef>
                    urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport
                </saml2:AuthnContextClassRef>
            </saml2:AuthnContext>
        </saml2:AuthnStatement>
        <saml2:AttributeStatement>
            <saml2:Attribute
                FriendlyName="eduPersonPrincipalName"
                Name="urn:oid:1.3.6.1.4.1.5923.1.1.1.6"
                NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:uri"
            >
                <saml2:AttributeValue>{user_id}</saml2:AttributeValue>
            </saml2:Attribute>
            <saml2:Attribute
                FriendlyName="sn"
                Name="urn:oid:2.5.4.4"
                NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:uri"
            >
                <saml2:AttributeValue>{surname}</saml2:AttributeValue>
            </saml2:Attribute>
            <saml2:Attribute
                FriendlyName="givenName"
                Name="urn:oid:2.5.4.42"
                NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:uri"
            >
                <saml2:AttributeValue>{given_name}</saml2:AttributeValue>
            </saml2:Attribute>
            <saml2:Attribute
                FriendlyName="displayName"
                Name="urn:oid:2.16.840.1.113730.3.1.241"
                NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:uri"
            >
                <saml2:AttributeValue>{display_name}</saml2:AttributeValue>
            </saml2:Attribute>
            <saml2:Attribute
                FriendlyName="mail"
                Name="urn:oid:0.9.2342.19200300.100.1.3"
                NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:uri"
            >
                <saml2:AttributeValue>{email}</saml2:AttributeValue>
            </saml2:Attribute>
            {edu_person_affiliation_attribute}
        </saml2:AttributeStatement>
    </saml2:Assertion>
</saml2p:Response>
"""


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
                <mdui:Logo height="16" width="16">
                    data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAApgAAAKYB3X3/OAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAANCSURBVEiJtZZPbBtFFMZ/M7ubXdtdb1xSFyeilBapySVU8h8OoFaooFSqiihIVIpQBKci6KEg9Q6H9kovIHoCIVQJJCKE1ENFjnAgcaSGC6rEnxBwA04Tx43t2FnvDAfjkNibxgHxnWb2e/u992bee7tCa00YFsffekFY+nUzFtjW0LrvjRXrCDIAaPLlW0nHL0SsZtVoaF98mLrx3pdhOqLtYPHChahZcYYO7KvPFxvRl5XPp1sN3adWiD1ZAqD6XYK1b/dvE5IWryTt2udLFedwc1+9kLp+vbbpoDh+6TklxBeAi9TL0taeWpdmZzQDry0AcO+jQ12RyohqqoYoo8RDwJrU+qXkjWtfi8Xxt58BdQuwQs9qC/afLwCw8tnQbqYAPsgxE1S6F3EAIXux2oQFKm0ihMsOF71dHYx+f3NND68ghCu1YIoePPQN1pGRABkJ6Bus96CutRZMydTl+TvuiRW1m3n0eDl0vRPcEysqdXn+jsQPsrHMquGeXEaY4Yk4wxWcY5V/9scqOMOVUFthatyTy8QyqwZ+kDURKoMWxNKr2EeqVKcTNOajqKoBgOE28U4tdQl5p5bwCw7BWquaZSzAPlwjlithJtp3pTImSqQRrb2Z8PHGigD4RZuNX6JYj6wj7O4TFLbCO/Mn/m8R+h6rYSUb3ekokRY6f/YukArN979jcW+V/S8g0eT/N3VN3kTqWbQ428m9/8k0P/1aIhF36PccEl6EhOcAUCrXKZXXWS3XKd2vc/TRBG9O5ELC17MmWubD2nKhUKZa26Ba2+D3P+4/MNCFwg59oWVeYhkzgN/JDR8deKBoD7Y+ljEjGZ0sosXVTvbc6RHirr2reNy1OXd6pJsQ+gqjk8VWFYmHrwBzW/n+uMPFiRwHB2I7ih8ciHFxIkd/3Omk5tCDV1t+2nNu5sxxpDFNx+huNhVT3/zMDz8usXC3ddaHBj1GHj/As08fwTS7Kt1HBTmyN29vdwAw+/wbwLVOJ3uAD1wi/dUH7Qei66PfyuRj4Ik9is+hglfbkbfR3cnZm7chlUWLdwmprtCohX4HUtlOcQjLYCu+fzGJH2QRKvP3UNz8bWk1qMxjGTOMThZ3kvgLI5AzFfo379UAAAAASUVORK5CYII=
                </mdui:Logo>
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


def format_edu_person_affiliation_attribute(edu_person_affiliation):
    """Formats the `eduPersonAffiliation` attribute to add in SAML Auth response"""
    if not edu_person_affiliation:
        return ""

    return (
        """
                <saml2:Attribute
                FriendlyName="eduPersonAffiliation"
                Name="urn:oid:1.3.6.1.4.1.5923.1.1.1.1"
                NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:uri"
            >
        """
        + "\n".join(
            f"<saml2:AttributeValue>{attribute}</saml2:AttributeValue>"
            for attribute in edu_person_affiliation
        )
        + """
            </saml2:Attribute>
        """
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


def generate_auth_response(in_response_to, acs_url, **kwargs):
    """Generates an SAML authentication response."""
    edu_person_affiliation = kwargs.get("edu_person_affiliation", [])
    if not isinstance(edu_person_affiliation, (list, tuple)):
        edu_person_affiliation = [edu_person_affiliation]

    response_attributes = {
        "in_response_to": in_response_to,
        "issuer": "http://edu.example.com/adfs/services/trust",
        "entity_id": "http://edu.example.com/adfs/services/trust",
        "acs_url": acs_url,
        "valid_until": OneLogin_Saml2_Utils.parse_time_to_SAML(
            calendar.timegm((datetime.utcnow() + timedelta(days=10)).utctimetuple())
        ),
        "user_id": str(uuid.uuid4()),
        "surname": "Sanchez",
        "given_name": "Rick",
        "display_name": "Rick Sanchez",
        "email": "rsanchez@samltest.id",
        "edu_person_affiliation_attribute": format_edu_person_affiliation_attribute(
            edu_person_affiliation,
        ),
    }
    response_attributes.update(kwargs)

    auth_response = _AUTH_RESPONSE_TEMPLATE.format(**response_attributes)

    # Sign response
    saml_root = OneLogin_Saml2_XML.to_etree(auth_response)
    xml_signer = XMLSigner(c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#")
    signed_saml = xml_signer.sign(
        saml_root,
        key=get_dev_private_key(),
        cert=get_dev_certificate(),
        reference_uri="_1ee4d12dc0a92300cfb40c8156157708",
    )

    return OneLogin_Saml2_XML.to_string(signed_saml).decode("utf-8")
