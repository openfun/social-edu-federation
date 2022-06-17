"""Metadata store module using Django's default cache"""
import datetime

from django.core.cache import InvalidCacheBackendError, cache as default_cache, caches

from social_core.utils import slugify

from social_edu_federation.metadata_store import BaseMetadataStore
from social_edu_federation.parser import FederationMetadataParser


class CacheEntryMixin:
    """
    Mix-in to turn `BaseMetadataStore` into a cache object to easily
    manage object storage in cache.

    This:
     - adds a namespace to the cached keys,
     - defines a cache duration of one day,
       we add a minute to ensure the refreshing management command
       can pass again.
     -  uses the default defined cache (you may use a Redis cache in production).
    """

    namespace = "edu_fed_saml"
    duration = datetime.timedelta(hours=24, minutes=1).total_seconds()
    cache = default_cache  # Django default cache

    def _namespaced_key(self, key):
        """Returns a key for the cache entry."""
        return f"edu_federation:{self.namespace}:{key}"

    def set_many(self, **kwargs):
        """
        Class method to update keys in cache by batch.

        Note: `RenaterCache` does not provide other "many keys" manipulation.
        This is on purpose, as we don't need this complexity here.
        """
        self.cache.set_many(
            dict((self._namespaced_key(key), value) for key, value in kwargs.items()),
            self.duration,
        )

    def get(self, entry_id):
        """Returns the cache entry value."""
        return self.cache.get(self._namespaced_key(entry_id))

    def set(self, entry_id, value):
        """Store the cache entry value."""
        self.cache.set(self._namespaced_key(entry_id), value, self.duration)


class CachedMetadataStore(CacheEntryMixin, BaseMetadataStore):
    """
    Implementation of a metadata store for authentication backends with cache.

    Its purpose is to allow the retrieval of Identity Provider configuration
    from the remote Federation Metadata without parsing data each time.
    """

    parsed_metadata_key = "all_idps"

    def __init__(self, backend):
        """Add cache specific configuration."""
        super().__init__(backend)
        self._init_cache_settings()

    def _init_cache_settings(self):
        """Add cache management configuration, use a different namespace for each backend."""
        self.namespace = slugify(self.backend.name)
        specified_cache_name = self.backend.setting("DJANGO_CACHE", None)
        if specified_cache_name:
            try:
                self.cache = caches[specified_cache_name]
            except InvalidCacheBackendError as exception:
                raise InvalidCacheBackendError(
                    f"'{specified_cache_name}' does not exist in {list(caches)}"
                ) from exception

    def refresh_cache_entries(self):
        """Refetch the metadata, parse them and store values in cache."""
        xml_metadata = self.fetch_remote_metadata()

        all_idp_dict = FederationMetadataParser.parse_federation_metadata(xml_metadata)

        self.set(self.parsed_metadata_key, all_idp_dict)
        self.set_many(**all_idp_dict)

        return all_idp_dict

    def get_idp(self, idp_name):
        """Given the name of an IdP, get an SAMLIdentityProvider instance from federation."""
        idp_configuration = self.get(idp_name)
        if not idp_configuration:
            all_configurations = self.refresh_cache_entries()
            idp_configuration = all_configurations[idp_name]

        return self.backend.edu_fed_saml_idp_class.create_from_config_dict(
            **idp_configuration
        )
