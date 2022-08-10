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
            "global.opentdf.common.oidcInternalHost=http://keycloak-http",
            "global.opentdf.common.oidcUrlPath=auth",
            "image.repo=" + CONTAINER_REGISTRY + "/opentdf/keycloak-bootstrap",
        ],
    )
)
k8s_resource(
    "xtest-keycloak-bootstrap",
    labels="xtest",
    resource_deps=["backend"],
)

docker_build(
    "opentdf/tests-clients",
    context="./",
    dockerfile="./tests/containers/clients/Dockerfile",
)
k8s_yaml("tests/integration/xtest.yaml")

k8s_resource(
    "opentdf-xtest", resource_deps=["xtest-keycloak-bootstrap"], labels="xtest"
)
