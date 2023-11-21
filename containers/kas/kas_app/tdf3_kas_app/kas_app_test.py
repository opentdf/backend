"""Test the KAS app."""

import pytest
import re

from .kas_app import app


@pytest.fixture(scope="session")
def kas_app_instance():
    print("create kas_app_instance")
    tmp = app("__main__")
    tmp.testing = True
    return tmp


@pytest.fixture(scope="session")
def test_client(kas_app_instance):
    client = kas_app_instance.test_client()
    return client


def test_kas_heartbeat(test_client):
    response = test_client.get("/")
    print(response)
    assert response.status_code == 200
    assert "application/json" in response.apparent_encoding
    json = response.json()
    assert re.match(r"\d+\.\d+\.\d+", json["version"])


def test_kas_public_key(test_client):
    response = test_client.get("/kas_public_key")
    print(response)
    assert response.status_code == 200
    cert = response.content.decode("utf-8")
    assert re.match(r".?-----BEGIN CERTIFICATE-----(.|\s)*", cert)
