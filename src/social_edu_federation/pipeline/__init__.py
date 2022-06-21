"""
Project's own pipeline module.

This also provide a default pipeline to use, based on the original
`DEFAULT_AUTH_PIPELINE` but replacing the `create_user` step with our own.
"""

from social_core.pipeline import DEFAULT_AUTH_PIPELINE


DEFAULT_EDU_FED_AUTH_PIPELINE = tuple(
    step
    if step != "social_core.pipeline.user.create_user"
    else "social_edu_federation.pipeline.user.create_user"
    for step in DEFAULT_AUTH_PIPELINE
)
