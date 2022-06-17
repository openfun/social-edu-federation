"""`social_edu_federation`'s Django testing URLs. Do not use in production."""

from django.urls import path

from .views import SamlFakeIdpMetadataView, SamlFakeIdpSsoLocationView


app_name = "social_edu_federation_django_testing"


urlpatterns = [
    # SAML
    path("saml/idp/sso/", SamlFakeIdpSsoLocationView.as_view(), name="idp_sso_login"),
    path("saml/idp/metadata/", SamlFakeIdpMetadataView.as_view(), name="idp_metadata"),
]
