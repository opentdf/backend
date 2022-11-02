# Tiltfile for development of OpenTDF backend
# reference https://docs.tilt.dev/api.html
# extensions https://github.com/tilt-dev/tilt-extensions

load("./common.Tiltfile", "backend", "CONTAINER_REGISTRY", "OIDC_CLIENT_SECRET")

backend()

k8s_yaml(
    helm(
        "charts/keycloak-bootstrap",
        "xtest-keycloak-bootstrap",
        values=["./tests/integration/backend-keycloak-bootstrap-values.xtest.yaml"],
        set=[
            "secrets.oidcClientSecret=%s" % OIDC_CLIENT_SECRET,
            "image.repo=" + CONTAINER_REGISTRY + "/opentdf/keycloak-bootstrap",
        ],
    )
)
k8s_resource(
    "xtest-keycloak-bootstrap",
    labels="xtest",
    resource_deps=["backend"],
)

# if running locally, export your GH PAT as CR_PAT
AUTH_TOKEN = os.getenv("CR_PAT", "")
if "NODE_AUTH_TOKEN" in os.environ:
    AUTH_TOKEN=os.getenv("NODE_AUTH_TOKEN")

docker_build(
    "opentdf/tests-clients",
    context="./",
    dockerfile="./tests/containers/clients/Dockerfile",
    build_args={"NPM_TOKEN":AUTH_TOKEN}
)
k8s_yaml("tests/integration/xtest.yaml")

k8s_resource(
    "opentdf-xtest", labels="xtest"
)
