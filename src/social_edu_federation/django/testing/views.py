"""social_edu_federation's Django testing views."""
from django.http import HttpResponse
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from onelogin.saml2.utils import OneLogin_Saml2_Utils
from onelogin.saml2.xml_utils import OneLogin_Saml2_XML

from social_edu_federation.testing.saml_tools import (
    format_mdui_display_name,
    generate_auth_response,
    generate_idp_federation_metadata,
    generate_idp_metadata,
)


class FederationMetadataFromLocalFileView(View):
    """Convenient view to provide metadata from a local file."""

    file_path = None  # must be passed in the view init arguments

    def __init__(self, **kwargs):
        """Checks the view is properly initialized."""
        super().__init__(**kwargs)

        if self.file_path is None:
            raise RuntimeError(
                f"{self.__class__.__name__} `as_view` must be called "
                f"with `file_path` keyword argument"
            )

    def get(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        """Display the raw metadata"""
        with open(self.file_path, "rb") as metadata_fs:
            metadata = metadata_fs.read()

        return HttpResponse(content=metadata, content_type="text/xml")


class SamlFakeIdpSsoLocationView(TemplateView):
    """Local identity provider faking view"""

    template_name = "testing/fake_saml_idp_sso_login.html"
    template_extends = "social_edu_federation/base.html"

    def get_context_data(self, **kwargs):
        """
        This provides a fake view receiving the SAML authentication request.

        This view prepares an SAML authentication response and POST it
        to the usual marsha endpoint (`acs_url`).
        """
        context = super().get_context_data(**kwargs)

        data = self.request.GET
        saml_request = data["SAMLRequest"]
        saml_relay_state = data["RelayState"]

        readable_saml_request = OneLogin_Saml2_Utils.decode_base64_and_inflate(
            saml_request
        )
        saml_request = OneLogin_Saml2_XML.to_etree(readable_saml_request)
        acs_url = saml_request.get("AssertionConsumerServiceURL")
        request_id = saml_request.get("ID")

        context.update(
            {
                "template_extends": self.template_extends,
                #
                "acs_url": acs_url,
                "auth_response": OneLogin_Saml2_Utils.b64encode(
                    generate_auth_response(
                        request_id,
                        acs_url,
                        issuer=self.request.build_absolute_uri(self.request.path),
                    )
                ),
                "saml_relay_state": saml_relay_state,
            }
        )

        return context


class SamlFakeIdpMetadataView(View):
    """Local identity provider faking metadata view"""

    local_idp_login_view_name = "social_edu_federation_django_testing:idp_sso_login"

    def get(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        """Returns SAML metadata for a fake Renater federation."""

        local_idp_name = "Local accepting IdP"
        sso_location = self.request.build_absolute_uri(
            reverse(self.local_idp_login_view_name)
        )

        entity_descriptor_list = [
            generate_idp_metadata(
                entity_id=sso_location,
                sso_location=sso_location,
                ui_info_display_names=format_mdui_display_name(local_idp_name),
            ),
            # generate some random IdP to populate list (not mandatory)
            *[
                generate_idp_metadata(
                    entity_id=f"http://edu.example.com/adfs/services/trust/{i}/",
                    sso_location=f"http://edu.example.com/adfs/sso/{i}/",
                    ui_info_display_names=format_mdui_display_name(f"Fake IdP {i}"),
                )
                for i in range(1, 5)
            ],
        ]
        return HttpResponse(
            generate_idp_federation_metadata(
                entity_descriptor_list=entity_descriptor_list
            ),
            content_type="text/xml",
        )
