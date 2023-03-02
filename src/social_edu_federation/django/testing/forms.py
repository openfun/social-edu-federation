"""Forms for the social_edu_federation testing views"""
from django import forms

from social_edu_federation.defaults import EduPersonAffiliationEnum


class SamlFakeIdpUserForm(forms.Form):
    """User attributes form, allows to customize SAML Auth Response."""

    user_id = forms.CharField(label="User ID")
    surname = forms.CharField(label="First name")
    given_name = forms.CharField(label="Last name")
    display_name = forms.CharField(label="Full name")
    email = forms.CharField(label="Email")
    edu_person_affiliation = forms.MultipleChoiceField(
        choices=EduPersonAffiliationEnum.get_choices(),
        label="eduPersonAffiliation",
        required=False,
    )
