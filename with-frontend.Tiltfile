load("ext://helm_resource", "helm_resource", "helm_repo")
load("./common.Tiltfile", "backend", "dict_to_helm_set_list")

EXTERNAL_URL = "http://localhost:65432"
FRONTEND_IMAGE_TAG = "main"
FRONTEND_CHART_TAG = "0.0.0-sha-93bb332"

ingress_enable = {
    ("%s.ingress.enabled" % s): "true"
    for s in ["attributes", "entitlements", "kas", "keycloak"]
}
backend(set=ingress_enable)

overrides = {
    "attributes.serverUrl": "%s/api/attributes" % EXTERNAL_URL,
    "entitlements.serverUrl": "%s/api/entitlements" % EXTERNAL_URL,
    "image.tag": FRONTEND_IMAGE_TAG,
    "oidc.serverUrl": "%s/auth/" % EXTERNAL_URL,
}

helm_resource(
    "opentdf-abacus",
    "oci://ghcr.io/opentdf/charts/abacus",
    flags=[
        "--version",
        FRONTEND_CHART_TAG,
        "-f",
        "./tests/integration/backend-with-frontend-values-abacus.yaml",
    ]
    + dict_to_helm_set_list(overrides),
    labels="frontend",
    resource_deps=["backend"],
)
