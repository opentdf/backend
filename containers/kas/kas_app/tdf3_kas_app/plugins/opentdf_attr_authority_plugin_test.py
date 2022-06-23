"""Test the OpenTDF attribute authority plugin."""

import pytest

from unittest.mock import patch, Mock

import requests

from tdf3_kas_core.errors import InvalidAttributeError
from tdf3_kas_core.errors import RequestTimeoutError
from .opentdf_attr_authority_plugin import OpenTDFAttrAuthorityPlugin

HOST = "http://localhost:4010"
NAMESPACES = [
    "https://acme.com/attr/IntellectualProperty",
    "https://acme.mil/attr/AcmeRestrictions",
]
ATTRIBUTES = {
    "https://acme.com/attr/IntellectualProperty": {
        "rule": "hierarchy",
        "order": ["TradeSecret", "Proprietary", "BusinessSensitive", "Open"],
    },
    "https://acme.mil/attr/AcmeRestrictions": {"rule": "allOf"},
}


def test_otdf_plugin_constructor():
    actual = OpenTDFAttrAuthorityPlugin(HOST)
    assert isinstance(actual, OpenTDFAttrAuthorityPlugin)  # my kingdom for static typing.
    assert actual._host == HOST


@patch.object(requests, "get", return_value=Mock(status_code=404))
def test_fetch_attributes_404(mock_request):
    actual = OpenTDFAttrAuthorityPlugin(HOST)
    result = actual.fetch_attributes([])
    assert result is None


def mocked_requests_response(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    return MockResponse(ATTRIBUTES, 200)


@patch.object(requests, "get", side_effect=mocked_requests_response)
def test_fetch_attributes_200_stautus(mock_request):
    actual = OpenTDFAttrAuthorityPlugin(HOST)
    attributes = actual.fetch_attributes(NAMESPACES)
    assert attributes == ATTRIBUTES


@patch.object(requests, "get", side_effect=requests.exceptions.ReadTimeout)
def test_fetch_attributes_read_timeout_exception(mock_request):
    actual = OpenTDFAttrAuthorityPlugin(HOST)
    with pytest.raises(RequestTimeoutError):
        actual.fetch_attributes(NAMESPACES)


@patch.object(requests, "get", side_effect=requests.exceptions.ConnectTimeout)
def test_fetch_attributes_connect_timeout_exception(mock_request):
    actual = OpenTDFAttrAuthorityPlugin(HOST)
    with pytest.raises(RequestTimeoutError):
        actual.fetch_attributes(NAMESPACES)


@patch.object(requests, "get", side_effect=requests.exceptions.RequestException)
def test_fetch_attributes_request_exception(mock_request):
    actual = OpenTDFAttrAuthorityPlugin(HOST)
    with pytest.raises(InvalidAttributeError):
        actual.fetch_attributes(NAMESPACES)
