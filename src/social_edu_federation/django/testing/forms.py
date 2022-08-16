"""Forms for the social_edu_federation testing views"""
from django import forms


class SamlFakeIdpUserForm(forms.Form):
    """User attributes form, allows to customize SAML Auth Response."""

    user_id = forms.CharField(label="User ID")
    surname = forms.CharField(label="First name")
    given_name = forms.CharField(label="Last name")
    display_name = forms.CharField(label="Full name")
    email = forms.CharField(label="Email")
    edu_person_affiliation = forms.ChoiceField(
        choices=(
            (None, ""),
            ("student", "student"),
            ("faculty", "faculty"),
            ("staff", "staff"),
            ("employee", "employee"),
            ("member", "member"),
            ("affiliate", "affiliate"),
            ("alum", "alum"),
            ("library-walk-in", "library-walk-in"),
            ("researcher", "researcher"),
            ("retired", "retired"),
            ("emeritus", "emeritus"),
            ("teacher", "teacher"),
            ("registered-reader", "registered-reader"),
        ),
        label="eduPersonAffiliation",
        required=False,
    )
