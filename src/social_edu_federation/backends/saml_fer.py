"""
Backend for SAML 2.0 support for RENATER's "Féderation Éducation-Recherche" (FER) federation.

More information on the federation here:
https://services.renater.fr/federation/en/documentation/generale/metadata/index

This FERSAMLIdentityProvider backend uses the following fields as defaults,
so you may use it out of the box.

We use the following fields:
 - urn:oid:2.5.4.4 (sn) aka (surname)
   This represents the user's first name.
 - urn:oid:2.5.4.42 (givenName) aka (gn)
   This represents the user's last name.
 - urn:oid:2.16.840.1.113730.3.1.241 (displayName)
   This represents the user's full name.
 - urn:oid:0.9.2342.19200300.100.1.3 (mail)
   Provides us the user email, we use it as email address and username.
 - urn:oid:1.3.6.1.4.1.5923.1.1.1.1 (eduPersonAffiliation)
   Allows use to try to determine the role (student/professor).
   This is not mandatory.

Fields we do not use:
 - urn:oid:1.3.6.1.4.1.7135.1.2.1.14 (supannEtablissement)

All available fields are available on:
    https://services.renater.fr/documentation/supann/
    supann2021/recommandations/attributs/liste_des_attributs
"""
from .base import EduFedSAMLAuth, EduFedSAMLIdentityProvider


OID_USERID = "urn:oid:1.3.6.1.4.1.5923.1.1.1.6"  # eduPersonPrincipalName
OID_COMMON_NAME = "urn:oid:2.16.840.1.113730.3.1.241"  # displayName
OID_GIVEN_NAME = "urn:oid:2.5.4.42"  # givenName
OID_SURNAME = "urn:oid:2.5.4.4"  # sn
OID_MAIL = "urn:oid:0.9.2342.19200300.100.1.3"  # mail
OID_ROLE = "urn:oid:1.3.6.1.4.1.5923.1.1.1.1"  # eduPersonAffiliation


class FERSAMLIdentityProvider(EduFedSAMLIdentityProvider):
    """RENATER's "Féderation Éducation-Recherche" SAML backend, ready to use."""

    def __init__(self, name, **kwargs):
        """Add default attribute mapping"""
        default_fer_saml_attributes = {
            # Permanent, unique identifier for the user
            "attr_user_permanent_id": OID_USERID,
            # Details 'fullname'
            "attr_full_name": OID_COMMON_NAME,
            # Details 'first_name'
            "attr_first_name": OID_GIVEN_NAME,
            # Details 'last_name'
            "attr_last_name": OID_SURNAME,
            # Details 'username'
            "attr_username": OID_MAIL,
            # Details 'email'
            "attr_email": OID_MAIL,
            # Details 'role', not defined in parent class but make it explicit here
            "attr_role": OID_ROLE,
        }

        super().__init__(name, **{**default_fer_saml_attributes, **kwargs})

    def get_user_details(self, attributes: dict) -> dict:
        """
        Given the SAML attributes extracted from the SSO response, get
        the user data like name.

        We override the default one to add the user's role.

        This returns a dict which is later known in the pipeline as `details`.
        """
        user_details = super().get_user_details(attributes)
        user_details["role"] = self.get_attr(attributes, "attr_role", OID_ROLE)
        return user_details


class FERSAMLAuth(EduFedSAMLAuth):
    """
    Backend that implements SAML 2.0 Service Provider (SP) functionality
    based on Python Social auth SAML Provider.

    This backend allows management for Shibboleth federation which supports
    authentication via +100 partner universities.

    It is dedicated to the "Féderation Éducation-Recherche" federation.
    """

    # Warning: the name is also used to fetch settings
    # ie. settings must be defined using `SOCIAL_AUTH_SAML_FER`
    # prefix instead of original `SOCIAL_AUTH_SAML`
    name = "saml_fer"

    edu_fed_saml_idp_class = FERSAMLIdentityProvider
