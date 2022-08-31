load("./common.Tiltfile", "backend")

EXTERNAL_URL = "http://localhost:65432"
FRONTEND_DIR = "../frontend"
CONTAINER_REGISTRY = os.environ.get("CONTAINER_REGISTRY", "ghcr.io")

ingress_enable = {
    ("%s.ingress.enabled" % s): "true"
    for s in ["attributes", "entitlements", "kas", "keycloak"]
}

backend(set=ingress_enable)

docker_build(
    CONTAINER_REGISTRY + "/opentdf/abacus",
    FRONTEND_DIR,
    dockerfile=FRONTEND_DIR + "/Dockerfile",
)
EXTERNAL_URL = "http://localhost:65432"
k8s_yaml(
    helm(
        FRONTEND_DIR + "/charts/abacus",
        "abacus",
        set=[
            "attributes.serverUrl=%s/api/attributes" % EXTERNAL_URL,
            "entitlements.serverUrl=%s/api/entitlements" % EXTERNAL_URL,
            "oidc.serverUrl=%s/auth/" % EXTERNAL_URL,
        ],
        values=["./tests/integration/frontend-local.yaml"],
    )
)
k8s_resource("abacus")