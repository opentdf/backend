# Tiltfile for development of OpenTDF backend
# reference https://docs.tilt.dev/api.html
# extensions https://github.com/tilt-dev/tilt-extensions
# helm remote usage https://github.com/tilt-dev/tilt-extensions/tree/master/helm_remote#additional-parameters

load("ext://helm_remote", "helm_remote")
load("ext://helm_resource", "helm_resource")
load("ext://secret", "secret_from_dict", "secret_yaml_generic")
load("ext://min_tilt_version", "min_tilt_version")

min_tilt_version("0.25")

ALPINE_VERSION = os.environ.get("ALPINE_VERSION", "3.15")
PY_VERSION = os.environ.get("PY_VERSION", "3.10")
KEYCLOAK_BASE_VERSION = str(
    local('cut -d- -f1 < "{}"'.format("containers/keycloak-protocol-mapper/VERSION"))
).strip()

CONTAINER_REGISTRY = os.environ.get("CONTAINER_REGISTRY", "ghcr.io")

def from_dotenv(path, key):
    # Read a variable from a `.env` file
    return str(local('. "{}" && echo "${}"'.format(path, key))).strip()


config.define_string_list("to-run", args=True)
config.define_string_list("to-edit")
cfg = config.parse()

to_edit = cfg.get("to-edit", [])

groups = {
    "integration-test": [
        "keycloakx",
        "keycloak-bootstrap",
        "ingress-nginx-controller",
        "ingress-nginx-admission-create",
        "ingress-nginx-admission-patch",
        "opentdf-attributes",
        "opentdf-entitlement-pdp",
        "opentdf-entitlement-store",
        "opentdf-entitlements",
        "opentdf-kas",
        "opentdf-abacus",
        "opentdf-postgresql",
        "opentdf-xtest",
        "opentdf-abacus"
    ],
}

resources = []

isIntegrationTest = False
isPKItest = False

for arg in cfg.get("to-run", []):
    if arg == "integration-test":
        isIntegrationTest = True
    if arg in groups:
        resources += groups[arg]
    #else:
    #    if arg == "pki-test":
    #        isPKItest = False
        # also support specifying individual services instead of groups, e.g. `tilt up a b d`
    #    resources.append(arg)

config.set_enabled_resources(resources)

#                                                      .
#                                                    .o8
#   .oooo.o  .ooooo.   .ooooo.  oooo d8b  .ooooo.  .o888oo  .oooo.o
#  d88(  "8 d88' `88b d88' `"Y8 `888""8P d88' `88b   888   d88(  "8
#  `"Y88b.  888ooo888 888        888     888ooo888   888   `"Y88b.
#  o.  )88b 888    .o 888   .o8  888     888    .o   888 . o.  )88b
#  8""888P' `Y8bod8P' `Y8bod8P' d888b    `Y8bod8P'   "888" 8""888P'

local("./scripts/genkeys-if-needed")

if isPKItest:
    local("./tests/integration/pki-test/gen-keycloak-certs.sh")

all_secrets = {
    v: from_dotenv("./certs/.env", v)
    for v in [
        "CA_CERTIFICATE",
        "ATTR_AUTHORITY_CERTIFICATE",
        "KAS_CERTIFICATE",
        "KAS_EC_SECP256R1_CERTIFICATE",
        "KAS_EC_SECP256R1_PRIVATE_KEY",
        "KAS_PRIVATE_KEY",
    ]
}

if not os.path.exists(
    "./containers/keycloak-protocol-mapper/keycloak/quarkus/container/Dockerfile"
):
    local("make keycloak-repo-clone", dir="./containers/keycloak-protocol-mapper")

all_secrets["POSTGRES_PASSWORD"] = "myPostgresPassword"
all_secrets["OIDC_CLIENT_SECRET"] = "myclientsecret"
all_secrets["ca-cert.pem"] = all_secrets["CA_CERTIFICATE"]
all_secrets["opaPolicyPullSecret"] = os.environ.get("CR_PAT")


def only_secrets_named(*items):
    return {k: all_secrets[k] for k in items}


k8s_yaml(
    secret_from_dict(
        "attributes-secrets",
        inputs=only_secrets_named("OIDC_CLIENT_SECRET", "POSTGRES_PASSWORD"),
    )
)
k8s_yaml(
    secret_from_dict(
        "keycloak-bootstrap-secrets",
        inputs=only_secrets_named("OIDC_CLIENT_SECRET"),
    )
)
k8s_yaml(
        secret_from_dict(
            "entitlement-store-secrets",
            inputs=only_secrets_named("POSTGRES_PASSWORD"),
        )
    )
k8s_yaml(
    secret_from_dict(
        "opentdf-entitlement-pdp-secret",
        inputs=only_secrets_named(
            "opaPolicyPullSecret",
        ),
    )
)
k8s_yaml(
    secret_from_dict(
        "postgres-password",
        inputs=only_secrets_named("POSTGRES_PASSWORD"),
    )
)
k8s_yaml(
    secret_from_dict(
        "entitlements-secrets",
        inputs={
            "OIDC_CLIENT_SECRET": all_secrets["OIDC_CLIENT_SECRET"],
            "POSTGRES_PASSWORD": all_secrets["POSTGRES_PASSWORD"],
        },
    )
)
k8s_yaml(
    secret_from_dict(
        "kas-secrets",
        inputs=only_secrets_named(
            "ATTR_AUTHORITY_CERTIFICATE",
            "KAS_EC_SECP256R1_CERTIFICATE",
            "KAS_CERTIFICATE",
            "KAS_EC_SECP256R1_PRIVATE_KEY",
            "KAS_PRIVATE_KEY",
            "ca-cert.pem",
        ),
    )
)

#   o8o
#   `"'
#  oooo  ooo. .oo.  .oo.    .oooo.    .oooooooo  .ooooo.   .oooo.o
#  `888  `888P"Y88bP"Y88b  `P  )88b  888' `88b  d88' `88b d88(  "8
#   888   888   888   888   .oP"888  888   888  888ooo888 `"Y88b.
#   888   888   888   888  d8(  888  `88bod8P'  888    .o o.  )88b
#  o888o o888o o888o o888o `Y888""8o `8oooooo.  `Y8bod8P' 8""888P'
#                                    d"     YD
#                                    "Y88888P'
#

if "opentdf-abacus" in to_edit:
    docker_build("opentdf/abacus", "../frontend")

if "opentdf-abacus-client-web" in to_edit:
    docker_build(
        "opentdf/abacus",
        "../frontend",
        dockerfile="../frontend/DockerfileTests"
    )

docker_build(
    CONTAINER_REGISTRY + "/opentdf/python-base",
    context="containers/python_base",
    build_args={
        "ALPINE_VERSION": ALPINE_VERSION,
        "CONTAINER_REGISTRY": CONTAINER_REGISTRY,
        "PY_VERSION": PY_VERSION,
    },
)

docker_build(
    CONTAINER_REGISTRY + "/opentdf/keycloak-multiarch-base",
    "./containers/keycloak-protocol-mapper/keycloak/quarkus/container",
    build_args={
        "CONTAINER_REGISTRY": CONTAINER_REGISTRY,
    },
)

docker_build(
    CONTAINER_REGISTRY + "/opentdf/keycloak",
    context="./containers/keycloak-protocol-mapper",
    build_args={
        "CONTAINER_REGISTRY": CONTAINER_REGISTRY,
        "KEYCLOAK_BASE_IMAGE": CONTAINER_REGISTRY + "/opentdf/keycloak-multiarch-base",
        "KEYCLOAK_BASE_VERSION": KEYCLOAK_BASE_VERSION,
        "MAVEN_VERSION": "3.8.4",
        "JDK_VERSION": "11",
    },
)

docker_build(
    CONTAINER_REGISTRY + "/opentdf/entitlement-pdp",
    context="./containers/entitlement-pdp",
)

docker_build(
    CONTAINER_REGISTRY + "/opentdf/kas",
    build_args={
        "ALPINE_VERSION": ALPINE_VERSION,
        "CONTAINER_REGISTRY": CONTAINER_REGISTRY,
        "PY_VERSION": PY_VERSION,
        "PYTHON_BASE_IMAGE_SELECTOR": "",
    },
    context="containers/kas",
    live_update=[
        sync("./containers/kas", "/app"),
        run(
            "cd /app && pip install -r requirements.txt",
            trigger="./containers/kas/requirements.txt",
        ),
    ],
)

for microservice in ["attributes", "entitlements", "entitlement_store"]:
    image_name = CONTAINER_REGISTRY + "/opentdf/" + microservice
    docker_build(
        image_name,
        build_args={
            "ALPINE_VERSION": ALPINE_VERSION,
            "CONTAINER_REGISTRY": CONTAINER_REGISTRY,
            "PY_VERSION": PY_VERSION,
            "PYTHON_BASE_IMAGE_SELECTOR": "",
        },
        container_args=["--reload"],
        context="containers",
        dockerfile="./containers/" + microservice + "/Dockerfile",
        live_update=[
            sync("./containers/python_base", "/app/python_base"),
            sync("./containers/" + microservice, "/app/" + microservice),
            run(
                "cd /app/ && pip install -r requirements.txt",
                trigger="./containers/" + microservice + "/requirements.txt",
            ),
        ],
    )
postgres_helm_values = "tests/integration/backend-postgresql-values.yaml"
keycloak_helm_values = "tests/integration/backend-keycloak-values.yaml"

# Override Keycloak chart values for PKI
#if isPKItest:
#    keycloak_helm_values = "tests/integration/keycloak-pki-values.yaml"

helm_remote(
    "keycloakx",
    version="1.3.2",
    repo_url="https://codecentric.github.io/helm-charts",
    values=[keycloak_helm_values],
)

if "opentdf-abacus" in to_edit or "opentdf-abacus-client-web" in to_edit:
    k8s_yaml("tests/integration/frontend-local.yaml")
else:
    helm_resource(
        "opentdf-abacus",
        "oci://ghcr.io/opentdf/charts/abacus",
        flags=[
            "--version",
            "0.0.0-sha-d198639",
        ],
        labels="Frontend",
        resource_deps=["keycloak-bootstrap"],
    )

helm_remote(
    "postgresql",
    repo_url="https://charts.bitnami.com/bitnami",
    release_name="opentdf",
    version="10.16.2",
    values=[postgres_helm_values],
)

#                                           o8o
#                                           `"'
#   .oooo.o  .ooooo.  oooo d8b oooo    ooo oooo   .ooooo.   .ooooo.   .oooo.o
#  d88(  "8 d88' `88b `888""8P  `88.  .8'  `888  d88' `"Y8 d88' `88b d88(  "8
#  `"Y88b.  888ooo888  888       `88..8'    888  888       888ooo888 `"Y88b.
#  o.  )88b 888    .o  888        `888'     888  888   .o8 888    .o o.  )88b
#  8""888P' `Y8bod8P' d888b        `8'     o888o `Y8bod8P' `Y8bod8P' 8""888P'
#
# usage https://docs.tilt.dev/helm.html#helm-options

k8s_yaml(
    helm(
        "charts/attributes",
        "opentdf-attributes",
        set=[
            "image.name=" + CONTAINER_REGISTRY + "/opentdf/attributes",
            "secretRef.name=postgres-password",
        ],
        values=["tests/integration/backend-attributes-values.yaml"],
    )
)

k8s_yaml(
    helm(
        "charts/entitlement-pdp",
        "opentdf-entitlement-pdp",
        set= [
            "image.name=" + CONTAINER_REGISTRY + "/opentdf/entitlement-pdp",
            "createPolicySecret=false",
            "opaConfig.policy.useStaticPolicy=true",
        ],
        values=["tests/integration/backend-entitlement-pdp-values.yaml"],
    )
)

k8s_yaml(
    helm(
        "charts/entitlement-store",
        "opentdf-entitlement-store",
        set=[
            "image.name=" + CONTAINER_REGISTRY + "/opentdf/entitlement_store",
            "secretRef.name=postgres-password",
        ],
        values=["tests/integration/backend-entitlement-store-values.yaml"],
    )
)

k8s_yaml(
    helm(
        "charts/entitlements",
        "opentdf-entitlements",
        set=[
            "image.name=" + CONTAINER_REGISTRY + "/opentdf/entitlements",
            "secretRef.name=postgres-password",
        ],
        values=["tests/integration/backend-entitlements-values.yaml"],
    )
)

k8s_yaml(
    helm(
        "charts/kas",
        "opentdf-kas",
        set= [
            "image.name=" + CONTAINER_REGISTRY + "/opentdf/kas",
            "secretRef.name=kas-secrets",
            "certFileSecretName=kas-secrets",
        ],
        values=["tests/integration/backend-kas-values.yaml"],
    )
)

k8s_yaml(
    helm(
        "charts/keycloak_bootstrap",
        "keycloak-bootstrap",
        set=["image.name=" + CONTAINER_REGISTRY + "/opentdf/keycloak-bootstrap"],
        values=["tests/integration/backend-keycloak-bootstrap-values.yaml"],
    )
)

k8s_yaml("tests/integration/ingress-class.yaml")

# TODO this service requires actual S3 secrets
# TODO or use https://github.com/localstack/localstack
# k8s_yaml(
#     secret_from_dict(
#         "tdf-storage-secrets",
#         inputs={
#             "AWS_SECRET_ACCESS_KEY": "mySecretAccessKey",
#             "AWS_ACCESS_KEY_ID": "myAccessKeyId",
#         },
#     )
# )
# docker_build(
#     CONTAINER_REGISTRY + "/opentdf/storage",
#     context="containers/storage",
#     build_args={
#         "ALPINE_VERSION": ALPINE_VERSION,
#         "CONTAINER_REGISTRY": CONTAINER_REGISTRY,
#         "PY_VERSION": PY_VERSION,
#         "PYTHON_BASE_IMAGE_SELECTOR": "",
#     },
# )
# k8s_yaml(helm('charts/storage', 'storage', values=['deployments/docker-desktop/storage-values.yaml']))

k8s_resource(
    "opentdf-attributes",
    resource_deps=["opentdf-postgresql"],
    labels=["Backend"]
)
k8s_resource(
    "opentdf-entitlement-pdp",
    resource_deps=["opentdf-entitlement-store"],
    labels=["Backend"]
)
k8s_resource(
    "opentdf-entitlement-store",
    resource_deps=["opentdf-postgresql"],
    labels=["Backend"]
)
k8s_resource(
    "opentdf-entitlements",
    resource_deps=["opentdf-postgresql"],
    labels=["Backend"]
)
k8s_resource(
    "opentdf-kas",
    resource_deps=["opentdf-attributes"],
    labels=["Backend"]
)

#     o8o
#     `"'
#    oooo  ooo. .oo.    .oooooooo oooo d8b  .ooooo.   .oooo.o  .oooo.o
#    `888  `888P"Y88b  888' `88b  `888""8P d88' `88b d88(  "8 d88(  "8
#     888   888   888  888   888   888     888ooo888 `"Y88b.  `"Y88b.
#     888   888   888  `88bod8P'   888     888    .o o.  )88b o.  )88b
#    o888o o888o o888o `8oooooo.  d888b    `Y8bod8P' 8""888P' 8""888P'
#                      d"     YD
#                      "Y88888P'
#
# TODO should integrate with a service mesh and stop deploying our own ingress
# We need to have big headers for the huge bearer tokens we pass around
# https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/configmap/

helm_remote(
    "ingress-nginx",
    repo_url="https://kubernetes.github.io/ingress-nginx",
    set=["controller.config.large-client-header-buffers=20 32k"],
    version="4.0.16",
)

k8s_resource("ingress-nginx-controller", port_forwards="65432:80")
k8s_resource("ingress-nginx-controller", port_forwards="4567:443")

#     .o8                               .                .
#    "888                             .o8              .o8
#     888oooo.   .ooooo.   .ooooo.  .o888oo  .oooo.o .o888oo oooo d8b  .oooo.   oo.ooooo.
#     d88' `88b d88' `88b d88' `88b   888   d88(  "8   888   `888""8P `P  )88b   888' `88b
#     888   888 888   888 888   888   888   `"Y88b.    888    888      .oP"888   888   888
#     888   888 888   888 888   888   888 . o.  )88b   888 .  888     d8(  888   888   888
#     `Y8bod8P' `Y8bod8P' `Y8bod8P'   "888" 8""888P'   "888" d888b    `Y888""8o  888bod8P'
#                                                                                888
#                                                                               o888o
#

docker_build(
    "ghcr.io/opentdf/keycloak-bootstrap",
    "./containers/keycloak-bootstrap",
    build_args={"ALPINE_VERSION": ALPINE_VERSION, "PY_VERSION": PY_VERSION},
)

k8s_resource(
    "keycloakx",
    links=[link("http://localhost:65432/auth/", "Keycloak admin console")],
    labels=["Third-party"]
)

k8s_resource(
    "keycloak-bootstrap",
    resource_deps=["keycloakx", "opentdf-entitlements", "opentdf-attributes"],
    labels="Utility"
)

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

k8s_yaml("tests/integration/xtest.yaml")

k8s_resource(
    "opentdf-xtest",
    resource_deps=["keycloak-bootstrap", "keycloakx", "opentdf-entitlement-pdp", "opentdf-kas"],
)

#if isPKItest:
#    local_resource(
#        "pki-test",
#        "python3 tests/integration/pki-test/client_pki_test.py",
#        resource_deps=["keycloak-bootstrap", "keycloakx", "opentdf-kas", "opentdf-entitlement-pdp"],
#    )

# The Postgres chart by default does not remove its Persistent Volume Claims: https://github.com/bitnami/charts/tree/master/bitnami/postgresql#uninstalling-the-chart
# This means `tilt down && tilt up` will leave behind old PGSQL databases and volumes, causing weirdness.
# Doing a `tilt down && kubectl delete pvc --all` will solve this
# Tried to automate that teardown postcommand here with Tilt, and it works for everything but `tilt ci` which keeps
# waiting for the no-op `apply_cmd` to stream logs as a K8S resource.
# I have not figured out a clean way to run `down commands` with tilt
# k8s_custom_deploy("Manual PVC Delete On Teardown", 'echo ""', "kubectl delete pvc --all", "")
