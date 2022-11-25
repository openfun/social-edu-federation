"""Tests for the project's `user` pipeline steps."""
import pytest
from social_core.pipeline import DEFAULT_AUTH_PIPELINE

from social_edu_federation.pipeline import DEFAULT_EDU_FED_AUTH_PIPELINE
from social_edu_federation.pipeline.user import create_user


def test_original_default_pipeline_has_create_user_step():
    """Asserts we don't try to replace a nonexistent step."""
    # If this fails, social_edu_federation.pipeline.__init__ must be fixed
    assert "social_core.pipeline.user.create_user" in DEFAULT_AUTH_PIPELINE


def test_social_edu_federation_step_list():
    """Asserts our step is in our default pipeline."""
    # If this fails, social_edu_federation.pipeline.__init__ must be fixed
    assert (
        "social_edu_federation.pipeline.user.create_user"
        in DEFAULT_EDU_FED_AUTH_PIPELINE
    )


@pytest.fixture(name="backend_strategy")
def backend_strategy_fixture():
    """Fixture to create empty classes for not tested objects."""

    class MockedStrategy:
        """Fake strategy"""

    class MockedBackend:
        """Fake authentication backend"""

    return MockedBackend(), MockedStrategy()


@pytest.mark.parametrize(
    "details,expected_details",
    [
        pytest.param(
            {
                "fullname": "displayName",
                "first_name": "givenName",
                "last_name": "surname",
                "username": "mail",
                "email": "mail",
                "roles": ["eduPersonAffiliation"],
            },
            {
                "fullname": "displayName",
                "first_name": "givenName",
                "last_name": "surname",
                "username": "mail",
                "email": "mail",
                "roles": ["eduPersonAffiliation"],
            },
            id="all_data",
        ),
        pytest.param(
            {
                "fullname": "displayName",
                "last_name": "surname",
                "username": "mail",
                "email": "mail",
                "roles": ["eduPersonAffiliation"],
            },
            {
                "fullname": "displayName",
                "first_name": "",
                "last_name": "displayName",
                "username": "mail",
                "email": "mail",
                "roles": ["eduPersonAffiliation"],
            },
            id="first name missing",
        ),
        pytest.param(
            {
                "fullname": "displayName",
                "first_name": "givenName",
                "username": "mail",
                "email": "mail",
                "roles": ["eduPersonAffiliation"],
            },
            {
                "fullname": "displayName",
                "first_name": "",
                "last_name": "displayName",
                "username": "mail",
                "email": "mail",
                "roles": ["eduPersonAffiliation"],
            },
            id="last name missing",
        ),
        pytest.param(
            {
                "first_name": "givenName",
                "last_name": "surname",
                "username": "mail",
                "email": "mail",
                "roles": ["eduPersonAffiliation"],
            },
            {
                "first_name": "givenName",
                "last_name": "surname",
                "username": "mail",
                "email": "mail",
                "roles": ["eduPersonAffiliation"],
            },
            id="full name missing",
        ),
    ],
)
def test_create_user(details, expected_details, backend_strategy, mocker):
    """Asserts our `create_user` step filters data properly."""
    backend, strategy = backend_strategy

    social_create_user_mock = mocker.patch(
        "social_edu_federation.pipeline.user.social_create_user"
    )
    social_create_user_mock.return_value = True

    create_user(backend, details, strategy, 42, some_kwargs=18)

    social_create_user_mock.assert_called_once_with(
        backend,
        expected_details,
        strategy,
        42,
        some_kwargs=18,
    )


def test_create_user_not_enough_data(backend_strategy, mocker):
    """Asserts our `create_user` step quits if not enough data are provided."""
    backend, strategy = backend_strategy

    social_create_user_mock = mocker.patch(
        "social_edu_federation.pipeline.user.social_create_user"
    )

    details = {
        "username": "mail",
        "email": "mail",
        "roles": ["eduPersonAffiliation"],
    }

    create_user(backend, details, strategy, 42, some_kwargs=18)

    assert social_create_user_mock.call_count == 0
