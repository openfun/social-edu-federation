"""Project base authentication views."""
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import resolve_url
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView

from social_core.utils import slugify
from social_django.utils import load_backend, load_strategy
from social_django.views import NAMESPACE

from social_edu_federation.django.metadata_store import CachedMetadataStore


class InvalidGeneratedMetadataException(Exception):
    """Specific exception raise when generated metadata are not valid"""


class SocialBackendViewMixin:
    """
    Mixin to add backend management.
    This allows to write one view for several Python Social Auth backends.
    """

    backend_name = None  # must be passed in the view init arguments

    def __init__(self, **kwargs):
        """Checks the view is properly initialized."""
        super().__init__(**kwargs)

        if self.backend_name is None:
            raise RuntimeError(
                f"{self.__class__.__name__} `as_view` must be called "
                f"with `backend_name` keyword argument"
            )


class EduFedMetadataView(SocialBackendViewMixin, View):
    """Generates the service provider metadata to provide to the identity providers."""

    def get(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        """Displays the generated metadata for the specified backend."""
        complete_url = reverse(
            f"{NAMESPACE}:complete",
            args=(self.backend_name,),
        )
        saml_backend = load_backend(
            load_strategy(request),
            self.backend_name,
            redirect_uri=complete_url,
        )
        metadata, errors = saml_backend.generate_metadata_xml()

        if errors:
            # Django will return an HttpResponseServerError
            raise InvalidGeneratedMetadataException()  # no security need to hide errors

        return HttpResponse(content=metadata, content_type="text/xml")


class EduFedIdpChoiceView(SocialBackendViewMixin, TemplateView):
    """
    Display the list of all available Renater's Identity providers.
    """

    template_name = "social_edu_federation/available_idps_list.html"
    template_extends = "social_edu_federation/base.html"
    # Enforce the use of the `CachedMetadataStore` because we want to use the cache.
    metadata_store_class = CachedMetadataStore

    def __init__(self, **kwargs):
        """Customize the cookie name to separate concern between backends."""
        super().__init__(**kwargs)
        cleaned_backend_name = slugify(self.backend_name).replace("-", "_")
        self.recent_use_cookie_name = f"_latest_idps_{cleaned_backend_name}"

    def get_idp_list(self):
        """
        Returns the cached list of identity providers

        Returns a list like:
        ```
        [
            {
                'name': 'idp-university-1',
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
                'edu_fed_data' : {
                    'display_name': 'IdP University 1',
                    'organization_name': 'Organization',
                    'organization_display_name': 'Organization displayable name',
                }
            },
            ...
        ]
        ```
        """
        strategy = load_strategy(self.request)
        backend = load_backend(strategy, self.backend_name, redirect_uri=None)
        metadata_store = self.metadata_store_class(backend)

        idp_list = metadata_store.get("SamlFerIdpAPIView.get_idp_choices")
        if idp_list is None:
            all_idps = metadata_store.get(metadata_store.parsed_metadata_key)
            if all_idps is None:
                all_idps = metadata_store.refresh_cache_entries()
            idp_list = list(all_idps.values())
            metadata_store.set("SamlFerIdpAPIView.get_idp_choices", idp_list)

        return idp_list

    def get_context_data(self, **kwargs):
        """
        Returns the context values:
         - List of all available Identity Providers
         - Last selected IdPs according to the cookie
        """
        context = super().get_context_data(**kwargs)
        context["template_extends"] = self.template_extends
        context["social_django_backend_begin_url"] = reverse(
            f"{NAMESPACE}:begin",
            args=(self.backend_name,),
        )

        available_idps = self.get_idp_list()

        latest_selected_idps_str = self.request.COOKIES.get(
            self.recent_use_cookie_name,
            None,
        )
        if latest_selected_idps_str:
            # Populate the latest selected IdP list
            latest_selected_idps = latest_selected_idps_str.split("+")
            latest_selected_idps_dict = [
                idp_data
                for idp_data in available_idps
                if idp_data["name"] in latest_selected_idps
            ]
            context["latest_selected_idps"] = latest_selected_idps_dict
        else:
            context["latest_selected_idps"] = None
        context["available_idps"] = available_idps
        context["recent_use_cookie_name"] = self.recent_use_cookie_name
        return context

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        """Redirect already logged-in user to the main page."""
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(resolve_url(settings.LOGIN_REDIRECT_URL))
        return super().dispatch(request, *args, **kwargs)
