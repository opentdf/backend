# Tiltfile for development of OpenTDF backend
# reference https://docs.tilt.dev/api.html
# extensions https://github.com/tilt-dev/tilt-extensions

load("./common.Tiltfile", "backend")

backend(extra_helm_parameters=["-f", "./tests/integration/backend-xtest-values.yaml"])


#    db    db d888888b d88888b .d8888. d888888b
#    `8b  d8' `~~88~~' 88'     88'  YP `~~88~~'
#     `8bd8'     88    88ooooo `8bo.      88
#     .dPYb.     88    88~~~~~   `Y8b.    88
#    .8P  Y8.    88    88.     db   8D    88
#    YP    YP    YP    Y88888P `8888Y'    YP

docker_build(
    "opentdf/tests-clients",
    context="./",
    dockerfile="./tests/containers/clients/Dockerfile",
    # todo: (PLAT-1650) Force to x86 mode until we have a python built in arch64
    platform="linux/amd64",
)

local_resource(
    "wait-for-bootstrap",
    cmd=[
        "tests/integration/wait-for-ready.sh",
        "job/keycloak-bootstrap",
        "15m",
        "default",
    ],
)

k8s_yaml("tests/integration/xtest.yaml")

k8s_resource(
    "opentdf-xtest", resource_deps=["wait-for-bootstrap"], labels="xtest"
)
