"""Test Entitlement bootstrap."""

import pytest
import entitlements_bootstrap
from unittest.mock import MagicMock, patch


def test_noop():
    assert True


@patch("entitlements_bootstrap.KeycloakAdmin")
@patch("entitlements_bootstrap.KeycloakOpenID")
@patch("entitlements_bootstrap.requests.put")
def test_main(kc_admin_mock, kc_oidc_mock, req_mock):
    """Test main."""
    rc = entitlements_bootstrap.entitlements_bootstrap()
    assert rc is True
