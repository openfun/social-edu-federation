"""Module containing the base class for the project's backends."""

from social_core.backends.saml import SAMLAuth, SAMLIdentityProvider
from social_core.utils import module_member


class EduFedSAMLIdentityProvider(SAMLIdentityProvider):
    """
    Wrapper around configuration for a SAML Identity provider.

    This is the base class to all the SAMLIdentityProvider defined
    in `social_edu_federation`.

    For now it only provides a class method to easily instantiate
    new objects from the metadata parsed dict.
    """

    @classmethod
    def create_from_config_dict(cls, **kwargs):
        """
        Makes the conversion from the dictionary fetch by python3-saml
        to an object usable by Python Social Auth.

        Parameters
        ----------
        kwargs : dict
            The identity provider we want to convert. Looks like:
            ```
            {
                'name': 'idp-displayable-name',
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
                'edu_fed_data': {
                    'display_name': 'IdP displayable name',
                    'organization_name': 'Organization',
                    'organization_display_name': 'Organization displayable name',
                },
            }
            ```

        Returns
        -------
        Type[cls]
            The object for Python Social Auth, like:
            ```
            returned_object = EduFedSAMLIdentityProvider.create_from_config_dict(**data)
            assert type(returned_object) == EduFedSAMLIdentityProvider
            assert returned_object.name == 'idp-displayable-name'
            assert returned_object.entity_id == 'http://idp.domain/adfs/services/trust'
            assert returned_object.url == 'https://idp.domain/adfs/ls/'
            assert returned_object.slo_url == 'https://idp.domain/adfs/ls/'
            assert returned_object.x509cert == 'MIIC4DCCAcigAwIBAgIQG...CQZXu/agfMc/tY+miyrD0='
            assert returned_object.conf['edu_fed_display_name'] == 'IdP displayable name'
            assert returned_object.conf['edu_fed_organization_name'] == 'Organization'
            ...
            ```
        """
        edu_fed_parameters = kwargs.get("edu_fed_data", {})

        return cls(
            kwargs["name"],
            entity_id=kwargs["entityId"],
            url=kwargs.get("singleSignOnService", {}).get("url"),
            slo_url=kwargs.get("singleLogoutService", {}).get("url"),
            x509cert=kwargs.get("x509cert"),
            x509certMulti=kwargs.get("x509certMulti"),
            #
            # Also store our own data in the class `conf` attribute
            # edu_fed_display_name = edu_fed_parameters["display_name"]
            # edu_fed_organization_display_name = edu_fed_parameters["organization_display_name"]
            **{f"edu_fed_{key}": val for key, val in edu_fed_parameters.items()},
        )


class EduFedSAMLAuth(SAMLAuth):
    """
    This is the base class to all the SAMLAuth defined
    in `social_edu_federation`.
    """

    # name must be overriden after (making it long to be painful for settings if forgotten)
    name = "base_edu_fed_backend"
    edu_fed_saml_idp_class = EduFedSAMLIdentityProvider

    def get_federation_metadata_url(self):
        """Boilerplate to the federation's metadata URL provided by settings."""
        return self.setting("FEDERATION_SAML_METADATA_URL", None)

    def get_metadata_store(self):
        """Retrieves the metadata store according to configuration."""
        metadata_store_path = self.setting(
            "FEDERATION_SAML_METADATA_STORE",
            "social_edu_federation.metadata_store.BaseMetadataStore",
        )
        try:
            metadata_store_class = module_member(metadata_store_path)
        except AttributeError as exception:
            # Reraise exception as an ImportError
            raise ImportError(exception) from exception
        return metadata_store_class(self)

    def get_idp(self, idp_name):
        """
        Given the name of an IdP, get an SAMLIdentityProvider instance.

        See https://python-social-auth.readthedocs.io/en/latest/backends/saml.html#advanced-usage
            Override this method if you wish to use some other method for configuring the available
            identity providers, such as fetching them at runtime from another server, or using a
            list of providers from a Shibboleth federation.

        This replaces the following setting:

        ```
        SOCIAL_AUTH_SAML_ENABLED_IDPS = {
            "testshib": {
                "entity_id": "https://idp.testshib.org/idp/shibboleth",
                "url": "https://idp.testshib.org/idp/profile/SAML2/Redirect/SSO",
                "x509cert": "MIIEDjCCAvagAwI...+ev0peYzxFyF5sQA==",
            }
        }
        ```

        This method is only a boilerplate to the cached configurations.
        """
        metadata_store = self.get_metadata_store()

        return metadata_store.get_idp(idp_name)
