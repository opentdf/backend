# Tiltfile for development of OpenTDF backend
# reference https://docs.tilt.dev/api.html
# extensions https://github.com/tilt-dev/tilt-extensions

load("ext://min_tilt_version", "min_tilt_version")

min_tilt_version("0.30")

CONTAINER_REGISTRY = os.environ.get("CONTAINER_REGISTRY", "ghcr.io")
OIDC_CLIENT_SECRET = "myclientsecret"


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

# We re-run the bootstrapper here, with additive values specific to the integration tests
# Because Tilt Must Do Things Its Own Non-Normative Way, we must rebuild the bootstrap
# image again here, so Tilt knows about it.
# TODO we really should use a local image registry, explicit SHA tags, and stop relying on Tilt's
# slightly fragile image caching automagic - it obscures things and breaks more often than it helps.
docker_build(
    CONTAINER_REGISTRY + "/opentdf/xtest-keycloak-bootstrap",
    "./containers/keycloak-bootstrap",
    build_args={
        "CONTAINER_REGISTRY": CONTAINER_REGISTRY,
    },
)

# Possibly The Stupidest Thing About Tilt is that despite sitting *directly on top* of the K8S
# control plane, which would allow it to inspect, interrogate, and observe literally every workload
# in the cluster, it is singularly unable to do anything with a resource it didn't actually create.
# Sits on top of one of the most powerful workload management APIs in human history, says, "nope can't use it,
# not mine, can't trust it."
# So, we have to do nonsense like this, where we shell out to run a single, basic `kubectl` command to check a YAML propery.
# This will wait for a named K8S job (that we know exists, and K8S knows exists, but Tilt doesn't) to have a success status,
# before continuing.
local_resource(
    "wait-for-bootstrap",
    cmd=[
        "tests/integration/wait-for-ready.sh",
        "job/keycloak-bootstrap",
        "15m",
        "default",
    ],
)

k8s_yaml(
    helm(
        "charts/keycloak-bootstrap",
        "xtest-keycloak-bootstrap",
        values=["./tests/integration/backend-keycloak-bootstrap-values.xtest.yaml"],
        set=[
            "secrets.oidcClientSecret=%s" % OIDC_CLIENT_SECRET,
            "global.opentdf.common.oidcInternalHost=http://keycloak-http",
            "global.opentdf.common.oidcUrlPath=auth",
            "image.repo=" + CONTAINER_REGISTRY + "/opentdf/xtest-keycloak-bootstrap",
        ],
    )
)

# TODO why is this needed? Just to convince Tilt that something is there, because it can't just check
# the K8S control plane like everyone else?
k8s_resource(
    "xtest-keycloak-bootstrap",
    labels="xtest",
    resource_deps=["wait-for-bootstrap"],
)

k8s_yaml("tests/integration/xtest.yaml")

k8s_resource(
    "opentdf-xtest", resource_deps=["xtest-keycloak-bootstrap"], labels="xtest"
)
