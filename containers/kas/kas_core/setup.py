"""Setup.py for the kas_core code."""

from setuptools import setup, find_packages

version = "0.8.7"

setup(
    name="tdf3-kas-core",
    version=version,
    python_requires=">=3.9",
    description="TDF3 KAS Core - Generic KAS for building TDF3 systems",
    author="Virtru",
    author_email="support@virtru.com",
    url="https://github.com/opentdf/backend.git",
    license="UNLICENSED",
    packages=find_packages(),
    package_data={
        "tdf3_kas_core": [
            "api/openapi.yaml",
            "schema/tdf3_rewrap_schema.json",
            "schema/tdf3_upsert_schema.json",
        ],
    },
    zip_safe=False,
    install_requires=[
        "Flask",
        "PyJWT",
        "bitstruct",
        "connexion",
        "cryptography",
        "gunicorn",
        "grpcio",
        "importlib-resources",
        "jsonschema",
        "protobuf",
        "python-json-logger",
        "requests",
        "statsd",
        "wsgicors",
        "attributes @ git+https://github.com/virtru/access-pdp#egg=attributes&subdirectory=clients/python/attributes",
        "accesspdp @ git+https://github.com/virtru/access-pdp#egg=accesspdp&subdirectory=clients/python/accesspdp",
    ],
)
