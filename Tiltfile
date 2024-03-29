# Tiltfile for development of OpenTDF backend
# reference https://docs.tilt.dev/api.html
# extensions https://github.com/tilt-dev/tilt-extensions
# helm remote usage https://github.com/tilt-dev/tilt-extensions/tree/master/helm_remote#additional-parameters

load("./common.Tiltfile", "backend")

# Ingress host port
INGRESS_HOST_PORT = os.getenv("OPENTDF_INGRESS_HOST_PORT", "65432")

config.define_string("allow-origin")
cfg = config.parse()
host_arg = cfg.get("allow-origin", "http://localhost:3000")

ingress_enable = {
    ("%s.ingress.enabled" % s): "true"
    for s in ["attributes", "entitlements", "kas", "keycloak", "entitlement-store"]
}

openapi_enable = {
    ("%s.openapiUrl" % s): "/openapi"
    for s in [
        "attributes",
        "entitlements",
        "entitlement-store",
        "kas/kas_core/tdf3_kas_core/api/",
    ]
}

server_root = {
    ("%s.serverRootPath" % s): ("/api/%s" % s)
    for s in ["attributes", "entitlements", "entitlement-store"]
}

cors_origins = {
    ("%s.serverCorsOrigins" % s): host_arg for s in ["attributes", "entitlements"]
}


backend(
    # if not CI then run in developer mode, see env var https://docs.github.com/en/actions/learn-github-actions/variables#default-environment-variables
    devmode=os.getenv("CI") != "true",
    external_port=INGRESS_HOST_PORT,
    set=dict(
        ingress_enable.items()
        + openapi_enable.items()
        + server_root.items()
        + cors_origins.items()
        + [
            (
                "kas.auth.http://localhost:65432/auth/realms/tdf.discoveryBaseUrl",
                "http://keycloak-http/auth/realms/tdf",
            )
        ],
    ),
)
