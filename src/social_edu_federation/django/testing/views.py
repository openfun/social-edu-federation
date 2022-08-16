"""social_edu_federation's Django testing views."""
import uuid

from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from onelogin.saml2.utils import OneLogin_Saml2_Utils
from onelogin.saml2.xml_utils import OneLogin_Saml2_XML
from social_django.views import NAMESPACE

from social_edu_federation.django.testing.forms import SamlFakeIdpUserForm
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
    """
    Local identity provider faking view.

    When accessing via a GET request it displays a form to customize authenticating
    user attributes.
    Then it POST data to generate the SAML response which will be POSTed again on
    the `acs_url` page by the javascript.
    """

    template_name = "testing/fake_saml_idp_sso_login.html"
    template_extends = "social_edu_federation/base.html"

    def get_context_data(self, **kwargs):
        """
        This provides a fake view receiving the SAML authentication request.

        This view prepares an SAML authentication response and POST it
        to the usual Django Social Auth endpoint (`acs_url`).
        """
        context = super().get_context_data(**kwargs)
        context["template_extends"] = self.template_extends

        data_from_get = self.request.GET
        data_from_post = self.request.POST

        saml_request = data_from_get["SAMLRequest"]
        saml_relay_state = data_from_get["RelayState"]

        readable_saml_request = OneLogin_Saml2_Utils.decode_base64_and_inflate(
            saml_request
        )
        saml_request = OneLogin_Saml2_XML.to_etree(readable_saml_request)
        acs_url = saml_request.get("AssertionConsumerServiceURL")
        request_id = saml_request.get("ID")

        if data_from_post:
            user_description_form = SamlFakeIdpUserForm(data=data_from_post)
            if not user_description_form.is_valid():
                context["user_description_form"] = user_description_form
            else:
                context.update(
                    {
                        "acs_url": acs_url,
                        "auth_response": OneLogin_Saml2_Utils.b64encode(
                            generate_auth_response(
                                request_id,
                                acs_url,
                                issuer=self.request.build_absolute_uri(
                                    self.request.path
                                ),
                                **user_description_form.cleaned_data,
                            )
                        ),
                        "saml_relay_state": saml_relay_state,
                    }
                )
        else:
            user_description_form = SamlFakeIdpUserForm(
                initial={
                    "acs_url": acs_url,
                    "request_id": request_id,
                    "saml_relay_state": saml_relay_state,
                    #
                    "user_id": str(uuid.uuid4()),
                    "surname": "Sanchez",
                    "given_name": "Rick",
                    "display_name": "Rick Sanchez",
                    "email": "rsanchez@samltest.id",
                }
            )
            context["user_description_form"] = user_description_form

        return context

    def post(self, request, *args, **kwargs):
        """Allow POST request on this view"""
        return super().get(request, *args, **kwargs)


class SamlFakeIdpMetadataView(View):
    """Local identity provider faking metadata view"""

    namespace = NAMESPACE.replace("social", "social_edu_federation_django_testing")
    local_idp_login_view_name = f"{namespace}:idp_sso_login"

    def get(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        """Returns SAML metadata for a fake Renater federation."""

        local_idp_name = "Local accepting IdP"
        sso_location = self.request.build_absolute_uri(
            reverse(self.local_idp_login_view_name)
        )

        # Allow to manually override the port when this is used from inside Docker container
        override_port = getattr(
            settings,
            "SOCIAL_AUTH_SAML_FER_IDP_FAKER_DOCKER_PORT",
            None,
        )
        if override_port:
            sso_location = sso_location.replace(
                f":{self.request.get_port()}/",
                f":{override_port}/",
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
