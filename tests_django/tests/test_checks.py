"""Tests for the Django checks"""

from django.core.checks import Warning as ChecksWarning

from social_edu_federation.django.checks import metadata_store_check


def test_metadata_store_check(settings):
    """Asserts the Django checks return the proper warning when no datastore is defined"""
    settings.AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)
    assert not metadata_store_check([])  # empty list

    settings.AUTHENTICATION_BACKENDS = (
        "social_edu_federation.backends.saml_fer.FERSAMLAuth",
        "django.contrib.auth.backends.ModelBackend",
    )
    assert metadata_store_check([]) == [
        ChecksWarning(
            "The default metadata store is not overridden.",
            hint=(
                "You should consider adding "
                "a `SOCIAL_AUTH_SAML_FER_FEDERATION_SAML_METADATA_STORE` setting "
                "for `social_edu_federation.backends.saml_fer.FERSAMLAuth` backend use."
            ),
            obj="social_edu_federation.metadata_store.BaseMetadataStore",
            id="social_edu_federation.W001",
        )
    ]

    settings.SOCIAL_AUTH_SAML_FER_FEDERATION_SAML_METADATA_STORE = (
        "defined.module.Store"
    )
    assert not metadata_store_check([])  # empty list
