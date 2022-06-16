"""Django checks for the social_edu_federation Django application"""
from django.conf import settings
from django.core.checks import Warning as ChecksWarning
from django.utils.module_loading import import_string

from social_core.utils import setting_name

from social_edu_federation.backends.base import EduFedSAMLAuth


def metadata_store_check(app_configs, **kwargs):  # pylint: disable=unused-argument
    """
    When using Django it is heavily recommended to use the `CachedMetadataStore`
    as it provides cache feature for the metadata and prevent long request for
    the federation's metadata fetch.
    """
    # Make this import locally to prevent application use before all application are ready.
    from social_django.utils import (  # pylint: disable=import-outside-toplevel
        load_strategy,
    )

    strategy = load_strategy()
    errors = []

    for authentication_backend_name in settings.AUTHENTICATION_BACKENDS:
        backend = import_string(authentication_backend_name)
        if (
            issubclass(backend, EduFedSAMLAuth)
            and backend(strategy).setting("FEDERATION_SAML_METADATA_STORE", None)
            is None
        ):
            setting = setting_name(backend.name, "FEDERATION_SAML_METADATA_STORE")
            errors.append(
                ChecksWarning(
                    "The default metadata store is not overridden.",
                    hint=(
                        f"You should consider adding a `{setting}` setting "
                        f"for `{authentication_backend_name}` backend use."
                    ),
                    obj="social_edu_federation.metadata_store.BaseMetadataStore",
                    id="social_edu_federation.W001",
                )
            )

    return errors
