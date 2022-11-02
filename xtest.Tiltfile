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
if "NPM_TOKEN" in os.environ:
    AUTH_TOKEN=os.getenv("NPM_TOKEN")

local_resource(
    "opentdf-xtest",
    "tests/containers/clients/run-test.sh",
    resource_deps=["xtest-keycloak-bootstrap"],
    labels="xtest"
)

