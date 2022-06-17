"""
Metadata store module

The purpose of the store is to fetch remotely the metadata and make an
identity provider object available for the SAML backend.

The store is a convenient way to add framework "specific" cache to the
metadata.
"""
from .parser import FederationMetadataParser


class BaseMetadataStore:
    """
    Base implementation of a metadata store for authentication backends.

    Its purpose is to allow the retrieval of Identity Provider configuration
    from the remote Federation Metadata.
    """

    def __init__(self, backend):
        """
        Provided a backend, the store has access to all required methods.

        The backend must have:
        - `get_federation_metadata_url` method
        - `edu_fed_saml_idp_class` attribute

        See `social_edu_federation.backends.base.EduFedSAMLAuth`.
        """
        self.backend = backend

    def fetch_remote_metadata(self) -> bytes:
        """
        Fetches the Renater Metadata remotely.

        This basic implementation does not provide any cache.
        """
        return FederationMetadataParser.get_metadata(
            self.backend.get_federation_metadata_url(),
            timeout=10,
        )

    def refresh_cache_entries(self):
        """
        Entry point for metadata store with cache management.

        Not implemented nor used here, but needs to be implemented in frameworks integration
        to easily refresh the cache.
        See:
         - `social_edu_federation.django.metadata_store.CachedMetadataStore` for the implementation
         - `social_edu_federation.django.management.prefetch_saml_fer_metadata` for its use
        """
        raise NotImplementedError()

    def get_idp(self, idp_name):
        """Given the name of an IdP, get an SAMLIdentityProvider instance from federation."""
        xml_metadata = self.fetch_remote_metadata()
        idp_configuration = FederationMetadataParser.parse_federation_metadata(
            xml_metadata
        )[idp_name]
        return self.backend.edu_fed_saml_idp_class.create_from_config_dict(
            **idp_configuration
        )
