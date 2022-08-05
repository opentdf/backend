# Tiltfile for development of OpenTDF backend
# reference https://docs.tilt.dev/api.html
# extensions https://github.com/tilt-dev/tilt-extensions
# helm remote usage https://github.com/tilt-dev/tilt-extensions/tree/master/helm_remote#additional-parameters

load("ext://helm_remote", "helm_remote")
load("ext://helm_resource", "helm_resource", "helm_repo")
load("ext://secret", "secret_from_dict", "secret_yaml_generic")
load("ext://min_tilt_version", "min_tilt_version")

min_tilt_version("0.30")

ALPINE_VERSION = os.environ.get("ALPINE_VERSION", "3.15")
PY_VERSION = os.environ.get("PY_VERSION", "3.10")
KEYCLOAK_BASE_VERSION = str(
    local('cut -d- -f1 < "{}"'.format("containers/keycloak-protocol-mapper/VERSION"))
).strip()

CONTAINER_REGISTRY = os.environ.get("CONTAINER_REGISTRY", "ghcr.io")
POSTGRES_PASSWORD = "myPostgresPassword"
OIDC_CLIENT_SECRET = "myclientsecret"
opaPolicyPullSecret = os.environ.get("CR_PAT")


def from_dotenv(path, key):
    # Read a variable from a `.env` file
    return str(local('. "{}" && echo "${}"'.format(path, key))).strip()


#                                                      .
#                                                    .o8
#   .oooo.o  .ooooo.   .ooooo.  oooo d8b  .ooooo.  .o888oo  .oooo.o
#  d88(  "8 d88' `88b d88' `"Y8 `888""8P d88' `88b   888   d88(  "8
#  `"Y88b.  888ooo888 888        888     888ooo888   888   `"Y88b.
#  o.  )88b 888    .o 888   .o8  888     888    .o   888 . o.  )88b
#  8""888P' `Y8bod8P' `Y8bod8P' d888b    `Y8bod8P'   "888" 8""888P'

# Override kas secrets using genkeys-if-needed and provide as chart overrides.
local("./scripts/genkeys-if-needed")

# TODO drop this if we move PKI out
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
    CONTAINER_REGISTRY + "/opentdf/keycloak",
    context="./containers/keycloak-protocol-mapper",
    build_args={
        "CONTAINER_REGISTRY": CONTAINER_REGISTRY,
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
    CONTAINER_REGISTRY + "/opentdf/entity-resolution",
    context="./containers/entity-resolution",
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

# TODO not sure why this needs to be installed separately, but
# our ingress config won't work without it.
k8s_yaml("tests/integration/ingress-class.yaml")

#                                           o8o
#                                           `"'
#   .oooo.o  .ooooo.  oooo d8b oooo    ooo oooo   .ooooo.   .ooooo.   .oooo.o
#  d88(  "8 d88' `88b `888""8P  `88.  .8'  `888  d88' `"Y8 d88' `88b d88(  "8
#  `"Y88b.  888ooo888  888       `88..8'    888  888       888ooo888 `"Y88b.
#  o.  )88b 888    .o  888        `888'     888  888   .o8 888    .o o.  )88b
#  8""888P' `Y8bod8P' d888b        `8'     o888o `Y8bod8P' `Y8bod8P' 8""888P'
#
# usage https://docs.tilt.dev/helm.html#helm-options


# Unfortunately, due to how Tilt (doesn't) work with Helm (a common refrain),
# `helm upgrade --dependency-update` doesn't solve the issue like it does with plain Helm.
# So, do it out of band as a shellout.
local_resource(
    "helm-dep-update",
    "helm dependency update",
    dir="./charts/backend",
)
helm_resource(
    name="backend",
    chart="./charts/backend",
    image_deps=[
        CONTAINER_REGISTRY + "/opentdf/keycloak-bootstrap",
        CONTAINER_REGISTRY + "/opentdf/keycloak",
        CONTAINER_REGISTRY + "/opentdf/attributes",
        CONTAINER_REGISTRY + "/opentdf/entitlements",
        CONTAINER_REGISTRY + "/opentdf/entitlement_store",
        CONTAINER_REGISTRY + "/opentdf/entitlement-pdp",
        CONTAINER_REGISTRY + "/opentdf/entity-resolution",
        CONTAINER_REGISTRY + "/opentdf/kas",
    ],
    image_keys=[
        ("keycloak-bootstrap.image.repo", "keycloak-bootstrap.image.tag"),
        ("keycloak.image.repository", "keycloak.image.tag"),
        ("attributes.image.repo", "attributes.image.tag"),
        ("entitlements.image.repo", "entitlements.image.tag"),
        ("entitlement_store.image.repo", "entitlement_store.image.tag"),
        ("entitlement-pdp.image.repo", "entitlement-pdp.image.tag"),
        ("entitlement-resolution.image.repo", "entitlement-resolution.image.tag"),
        ("kas.image.repo", "kas.image.tag"),
    ],
    flags=[
        "--dependency-update",
        "-f",
        "./tests/integration/backend-pki-values.yaml",  # TODO drop this if we move PKI out
        "--set",
        "entity-resolution.secret.keycloak.clientSecret=123-456",
        "--set",
        "secrets.opaPolicyPullSecret=%s" % opaPolicyPullSecret,
        "--set",
        "secrets.oidcClientSecret=%s" % OIDC_CLIENT_SECRET,
        "--set",
        "secrets.postgres.dbPassword=%s" % POSTGRES_PASSWORD,
        "--set",
        "kas.envConfig.attrAuthorityCert=%s"
        % all_secrets["ATTR_AUTHORITY_CERTIFICATE"],
        "--set",
        "kas.envConfig.ecCert=%s" % all_secrets["KAS_EC_SECP256R1_CERTIFICATE"],
        "--set",
        "kas.envConfig.cert=%s" % all_secrets["KAS_CERTIFICATE"],
        "--set",
        "kas.envConfig.ecPrivKey=%s" % all_secrets["KAS_EC_SECP256R1_PRIVATE_KEY"],
        "--set",
        "kas.envConfig.privKey=%s" % all_secrets["KAS_PRIVATE_KEY"],
    ],
    labels="opentdf",
    resource_deps=["helm-dep-update", "ingress-nginx-controller"],
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
