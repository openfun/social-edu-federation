"""Defines testing settings for the SAML FER backend authentication."""
from .certificates import get_dev_certificate, get_dev_private_key


saml_fer_settings = {
    "SOCIAL_AUTH_SAML_FER_SECURITY_CONFIG": {
        "authnRequestsSigned": True,
        "signMetadata": True,
        "wantMessagesSigned": False,
        "wantAssertionsSigned": True,
        "wantAssertionsEncrypted": False,
        "rejectDeprecatedAlgorithm": True,
        # allow single label domain as tests use "testserver" as domain
        "allowSingleLabelDomains": True,
    },
    "SOCIAL_AUTH_SAML_FER_SP_ENTITY_ID": "edu-fed",
    "SOCIAL_AUTH_SAML_FER_SP_PRIVATE_KEY": get_dev_private_key(),
    "SOCIAL_AUTH_SAML_FER_SP_PUBLIC_CERT": get_dev_certificate(),
    "SOCIAL_AUTH_SAML_FER_ORG_INFO": {
        "en-US": {
            "name": "edu-fed",
            "displayname": "France Université Numérique",
            "url": "edu-fed.example.com",
        },
    },
    "SOCIAL_AUTH_SAML_FER_TECHNICAL_CONTACT": {
        "givenName": "edu-fed dev team",
        "emailAddress": "edu-fed@example.com",
    },
    "SOCIAL_AUTH_SAML_FER_SUPPORT_CONTACT": {
        "givenName": "edu-fed dev team",
        "emailAddress": "edu-fed@example.com",
    },
    "SOCIAL_AUTH_SAML_FER_FEDERATION_SAML_METADATA_URL": (
        "http://testserver/account/saml/idp/metadata/"
    ),
}
