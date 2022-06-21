"""Project's own user regarding steps."""
from social_core.pipeline.user import create_user as social_create_user


def create_user(strategy, details, backend, *args, **kwargs):
    """
    Wrapper for `social_core.pipeline.user.create_user` to make
    a choice between the "last name"/"first name" couple or only the
    "full name".

    We expect the fullname to be always provided in SAML response but
    first name and last name may be not. If we are missing one of first/last
    names then we fallback on using the full name as last name.

    This pipeline step *must* replace `social_core.create_user` as we don't
    want to mess with the `details` for now.
    """
    filtered_details = dict(details)

    first_name = details.get("first_name")
    last_name = details.get("last_name")
    full_name = details.get("fullname")
    if not first_name or not last_name:
        if not full_name:
            # Too many data missing, can't continue
            return None
        filtered_details["first_name"] = ""
        filtered_details["last_name"] = full_name

    return social_create_user(strategy, filtered_details, backend, *args, **kwargs)
