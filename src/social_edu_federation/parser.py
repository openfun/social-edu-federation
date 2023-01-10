"""
Tools to parse Renater Federation Metadata XML.

This module is partially typed to ease the readability, since
it's not always obvious to know which object is manipulated.
"""

from typing import Dict

from onelogin.saml2.constants import OneLogin_Saml2_Constants
from onelogin.saml2.idp_metadata_parser import OneLogin_Saml2_IdPMetadataParser
from onelogin.saml2.xml_utils import OneLogin_Saml2_XML
from onelogin.saml2.xmlparser import tostring
from social_core.utils import slugify


# Enforce some namespace definitions for python3-saml
# - Add mdui from SAML V2.0 Metadata Extensions for Login and Discovery
OneLogin_Saml2_Constants.NSMAP["mdui"] = "urn:oasis:names:tc:SAML:metadata:ui"
# - Add saml2p support (not adding it makes random results)
#   This is not really a namespace recommended, still we must allow its use.
#   For instance it may be used by Google or https://samltest.id
OneLogin_Saml2_Constants.NSMAP["saml2"] = OneLogin_Saml2_Constants.NS_SAML
OneLogin_Saml2_Constants.NSMAP["saml2p"] = OneLogin_Saml2_Constants.NS_SAMLP


class FederationMetadataParser(OneLogin_Saml2_IdPMetadataParser):
    """
    Extension for the python3-saml metadata parser, we keep the same logic
    using class methods.

    This mainly allows to extract several Identity Providers at once from a
    federation metadata.
    This also extracts more data from the IdP metadata, see
    `extract_data_from_entity_descriptor_node` method.
    """

    idp_name_key = "display_name"

    @classmethod
    def get_xml_node_text(cls, dom, query: str, default: str = ""):
        """
        Extracts the text part of the first node from the `dom` that
        matches the `query`.

        Parameters
        ----------
        dom : lxml.etree.Element
            The parent node.

        query: str
            The xpath query to lookup.

        default: str
            The returned default value.
        """
        nodes = OneLogin_Saml2_XML.query(dom, query)
        if nodes:
            return OneLogin_Saml2_XML.element_text(nodes[0])
        return default

    @classmethod
    def extract_data_from_entity_descriptor_node(
        cls,
        entity_descriptor,
        entity_description: dict,
    ):
        """
        Queries extra metadata for our own needs
        - Requires mdui namespace
        - Query the display name, prefers "fr", but fallback on any
          and finally fallback on the `entity_description`'s Entity ID if none found.

        Parameters
        ----------
        entity_descriptor : lxml.etree.Element
            The entity descriptor node.

        entity_description : dict
            The IdP data automatically parsed by python3-saml
            (`OneLogin_Saml2_IdPMetadataParser.parse` method).

        Returns
        -------
        dict
            A dict containing all the data we need, which are not provided by
            python3-saml.

            ```
            {
                "display_name": "The IdP display name",
                "organization_name": "The IdP's organisation name",
                "organization_display_name": "The IdP's organisation display name"
            }
            ```
        """
        # Query extra metadata for our own needs
        # - Requires mdui namespace added in apps.AccountConfig.ready
        # - Query the display name, prefer "fr", but fallback on any
        #   and fallback on Entity ID if none found.
        extra_data = {}

        display_name_fr = cls.get_xml_node_text(
            entity_descriptor,
            './md:IDPSSODescriptor/md:Extensions/mdui:UIInfo/mdui:DisplayName[@xml:lang="fr"]',
        )
        default_display_name = cls.get_xml_node_text(
            entity_descriptor,
            "./md:IDPSSODescriptor/md:Extensions/mdui:UIInfo/mdui:DisplayName",
        )
        display_name = (
            display_name_fr or default_display_name or entity_description["entityId"]
        )
        # clean multiline name
        extra_data["display_name"] = "\n".join(
            x.strip() for x in display_name.splitlines()
        )
        # - Fetch organization information
        extra_data["organization_name"] = cls.get_xml_node_text(
            entity_descriptor,
            "./md:Organization/md:OrganizationName",
        )
        extra_data["organization_display_name"] = cls.get_xml_node_text(
            entity_descriptor,
            "./md:Organization/md:OrganizationDisplayName",
        )
        extra_data["logo"] = (
            cls.get_xml_node_text(
                entity_descriptor,
                "./md:IDPSSODescriptor/md:Extensions/mdui:UIInfo/mdui:Logo",
            )
            .replace("\n", "")
            .replace(" ", "")
        )

        return extra_data

    @classmethod
    def parse_federation_metadata(cls, xml_content: bytes) -> Dict[str, dict]:
        """
        Parses the Renater federation metadata to extract all Identity Providers.
        As Python Social Auth relies on python3-saml we re-use it here.

        `python3-saml` does not allow to extract all the IdP at once, hence the loop
        with reconversion from `ElementTree` to bytes to be allowed to re-use
        `python3-saml` for each IdP parsing.

        We also need more fields than only the technical ones: we fetch
        the French University name.

        Warning:

        Parameters
        ----------
        xml_content : bytes
            The content of the metadata.

        Returns
        -------
        dict
            This returns a dict of all the `SAMLIdentityProvider`:
            ```
            {
                idp-university-1: {
                    'name': 'idp-university-1',
                    'entityId': 'http://idp.domain/adfs/services/trust',
                    'singleSignOnService': {
                        'url': 'https://idp.domain/adfs/ls/',
                        'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
                    },
                    'singleLogoutService': {
                        'url': 'https://idp.domain/adfs/ls/',
                        'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
                    },
                    'x509cert': 'MIIC4DCCAcigAwIBAgIQG...CQZXu/agfMc/tY+miyrD0=',
                    'edu_fed_data' : {
                        'display_name': 'IdP University 1',
                        'organization_name': 'Organization',
                        'organization_display_name': 'Organization displayable name',
                    }
                }
            }
            ```
        """
        identity_providers = {}

        metadata = OneLogin_Saml2_XML.to_etree(xml_content)

        for entity_descriptor in OneLogin_Saml2_XML.query(
            metadata,
            "//md:EntityDescriptor",
        ):
            # Convert the entity descriptor to string again...
            # Not optimal, but python3-saml only allow to fetch one entity in the metadata.
            entity_descriptor_bytes = tostring(
                entity_descriptor, encoding="utf8", method="xml"
            )
            #
            # Query common IdP metadata
            entity_dict = OneLogin_Saml2_IdPMetadataParser.parse(
                entity_descriptor_bytes
            )["idp"]
            #
            # Query extra metadata for our own needs
            extra_data = cls.extract_data_from_entity_descriptor_node(
                entity_descriptor,
                entity_dict,
            )
            # Add a name to the configuration, will be used to init
            # `FERSAMLIdentityProvider` or equivalent later
            entity_dict["name"] = slugify(extra_data["display_name"])

            entity_dict["edu_fed_data"] = extra_data

            # Store all the necessary data
            identity_providers[str(entity_dict["name"])] = entity_dict

        return identity_providers
