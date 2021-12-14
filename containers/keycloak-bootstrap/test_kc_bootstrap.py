"""Test Keycloak bootstrap."""

import pytest
import keycloak_bootstrap
from unittest.mock import MagicMock, patch


def test_noop():
    assert True


@patch("keycloak_bootstrap.KeycloakAdmin")
def test_main(kc_admin_mock):
    """Test main."""
    rc = keycloak_bootstrap.kc_bootstrap()
    assert rc is True
