"""Django test project URLs"""
import os

from django.urls import include, path

from social_edu_federation.django import views as social_edu_federation_views
from social_edu_federation.django.testing import views as testing_views

from . import views


# URLs used in tests
urlpatterns = [
    path("", include("social_django.urls", namespace="social")),
    path(
        "saml/fer/metadata/",
        social_edu_federation_views.EduFedMetadataView.as_view(backend_name="saml_fer"),
        name="saml_fer_metadata",
    ),
    path(
        "saml/fer/idps/list/",
        social_edu_federation_views.EduFedIdpChoiceView.as_view(
            backend_name="saml_fer"
        ),
        name="saml_fer_idp_list",
    ),
    # Like a mock but providing a more realistic test
    path(
        "remote/fer/metadata/",
        testing_views.FederationMetadataFromLocalFileView.as_view(
            file_path=os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "tests",
                    "resources",
                    "real-world-metadata.xml",
                )
            ),
        ),
        name="real_world_metadata",
    ),
    # Testing views tests
    path("", include("social_edu_federation.django.testing.urls")),
]

# URLs used in local django project
urlpatterns += [
    path("", views.IndexView.as_view(), name="index"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
]
