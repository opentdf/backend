"""Abstract rewrap plugin runner test."""

import pytest

from pprint import pprint

from tdf3_kas_core.abstractions import AbstractRewrapPlugin

from .rewrap_plugin_runner_v2 import RewrapPluginRunnerV2

ATTRIBUTES = {
    "https://acme.com/attr/IntellectualProperty": {
        "rule": "hierarchy",
        "order": ["TradeSecret", "Proprietary", "BusinessSensitive", "Open"],
    },
    "https://acme.mil/attr/AcmeRestrictions": {"rule": "allOf"},
}


@pytest.fixture
def plugins():
    """Generate a list of dummy plugins."""
    yield [AbstractRewrapPlugin(), AbstractRewrapPlugin()]


@pytest.fixture
def req(policy, claims, key_access_remote, context):
    """Generate a req object."""
    yield {
        "policy": policy,
        "claims": claims,
        "keyAccess": key_access_remote,
        "context": context,
    }


# ========= TESTS ==========================================


def test_plugin_runner_constructor_empty():
    """Test the constructor."""
    actual = RewrapPluginRunnerV2()
    assert isinstance(actual, RewrapPluginRunnerV2)


def test_plugin_runner_constructor_with_plugins(plugins):
    """Test the constructor."""
    actual = RewrapPluginRunnerV2(plugins)
    assert isinstance(actual, RewrapPluginRunnerV2)


def test_plugin_runner_update_no_plugins(policy, claims, key_access_remote, context):
    """Test the update function."""
    pr = RewrapPluginRunnerV2()
    actual = pr.update(policy, claims, key_access_remote, context)
    assert actual[0] == policy
    res = actual[1]
    assert "entityWrappedKey" not in res
    assert res["metadata"] == {}


def test_plugin_runner_update_simple_plugin(
        plugins, policy, claims, key_access_remote, context
):
    """Test the update function."""

    class test_plugin(AbstractRewrapPlugin):
        """Mock plugin."""

        def update(self, req, res):
            """Return known values."""
            print("ping")
            print(req)
            print(res)
            res["entityWrappedKey"] = "this expected string"
            res["metadata"] = {"contract": "stuff"}
            return req, res

        def fetch_attributes(self, namespaces):
            """Return known values."""
            print("ping")
            print(namespaces)
            res = ATTRIBUTES
            return res

    plugins.append(test_plugin())
    print(plugins)

    pr = RewrapPluginRunnerV2(plugins)
    pprint(pr)
    actual = pr.update(policy, claims, key_access_remote, context)
    pprint(actual)
    assert actual[0] == policy
    res = actual[1]
    assert res["entityWrappedKey"] == "this expected string"
    assert res["metadata"] == {"contract": "stuff"}

    actual = pr.fetch_attributes(
        [
            "https://acme.com/attr/IntellectualProperty",
            "https://acme.mil/attr/AcmeRestrictions",
        ]
    )
    assert actual == ATTRIBUTES
