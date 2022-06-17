"""social_edu_federation's Django testing views."""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.views.generic import RedirectView, TemplateView


class IndexView(TemplateView):
    """
    Index page displaying whether the user is logged in or not.
    """

    template_name = "tests_django/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = (
            self.request.user if self.request.user.is_authenticated else None
        )
        return context


class LogoutView(RedirectView):
    """
    Log out the user and redirect to the main page.
    """

    pattern_name = settings.LOGIN_REDIRECT_URL

    def get(self, request, *args, **kwargs):
        """Logout the user then redirect to the home page."""
        auth_logout(request)
        messages.success(request, "You have been successfully logged out")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Logout (and should?) be done via POST."""
        return self.get(request, *args, **kwargs)
