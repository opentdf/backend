load("ext://helm_resource", "helm_resource", "helm_repo")
load("./common.Tiltfile", "backend")

EXTERNAL_URL = "http://localhost:65432"
FRONTEND_IMAGE_TAG = "main"
FRONTEND_CHART_TAG = "0.0.0-sha-93bb332"

backend(extra_helm_parameters=["-f", "./tests/integration/backend-with-frontend.yaml"])

local_resource(
    "wait-for-bootstrap",
    cmd=[
        "tests/integration/wait-for-ready.sh",
        "job/keycloak-bootstrap",
        "15m",
        "default",
    ],
)

helm_resource(
    "opentdf-abacus",
    "oci://ghcr.io/opentdf/charts/abacus",
    flags=[
        "--version",
        FRONTEND_CHART_TAG,
        "-f",
        "./tests/integration/backend-with-frontend-values-abacus.yaml",
        "--set",
        "attributes.serverUrl=%s/api/attributes" % EXTERNAL_URL,
        "--set",
        "entitlements.serverUrl=%s/api/entitlements" % EXTERNAL_URL,
        "--set",
        "image.tag=%s" % FRONTEND_IMAGE_TAG,
        "--set",
        "oidc.serverUrl=%s/auth/" % EXTERNAL_URL,
    ],
    labels="frontend",
    resource_deps=["wait-for-bootstrap"],
)
