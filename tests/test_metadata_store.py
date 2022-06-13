"""Metadata store tests, already tested in full process so this is only unit testing."""
from social_edu_federation.metadata_store import BaseMetadataStore
from social_edu_federation.parser import FederationMetadataParser


class MagicClass:
    """Mocking class to replace IdP real object"""

    def __init__(self, **kwargs):
        """Store all provided `kwargs` as attributes"""
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def create_from_config_dict(cls, **kwargs):
        """Creation method called by the metadata store."""
        return cls(**kwargs)


class MockedBackend:
    """Fake backend for test purpose only"""

    edu_fed_saml_idp_class = MagicClass

    def get_federation_metadata_url(self):
        """Boilerplate to return a fixed URL"""
        return "https://domain.test/metadata/"


def test_fetch_remote_metadata(mocker):
    """Tests `fetch_remote_metadata` method."""
    store = BaseMetadataStore(MockedBackend())

    get_metadata_mock = mocker.patch.object(FederationMetadataParser, "get_metadata")
    get_metadata_mock.return_value = b"been called"

    assert store.fetch_remote_metadata() == b"been called"

    get_metadata_mock.assert_called_once_with(
        "https://domain.test/metadata/", timeout=10
    )


def test_get_idp(mocker):
    """Tests `get_idp` method."""
    store = BaseMetadataStore(MockedBackend())

    get_metadata_mock = mocker.patch.object(FederationMetadataParser, "get_metadata")
    get_metadata_mock.return_value = b"been called"
    parse_metadata_mock = mocker.patch.object(
        FederationMetadataParser, "parse_federation_metadata"
    )
    parse_metadata_mock.return_value = {
        "some-idp": {
            "key1": "value1",
            "key2": "value2",
        },
        "other-idp": {
            "key3": "value3",
        },
    }

    magic_instance = store.get_idp("some-idp")

    get_metadata_mock.assert_called_once_with(
        "https://domain.test/metadata/", timeout=10
    )
    parse_metadata_mock.assert_called_once_with(b"been called")

    assert magic_instance.key1 == "value1"
    assert magic_instance.key2 == "value2"
    assert not hasattr(magic_instance, "key3")
