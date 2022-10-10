# Tiltfile for development of OpenTDF backend
# reference https://docs.tilt.dev/api.html
# extensions https://github.com/tilt-dev/tilt-extensions
# helm remote usage https://github.com/tilt-dev/tilt-extensions/tree/master/helm_remote#additional-parameters

load("./common.Tiltfile", "backend")

config.define_string('allow-origin')
cfg = config.parse()
host_arg = cfg.get('allow-origin', "http://localhost:3000")

ingress_enable = {
    ("%s.ingress.enabled" % s): "true"
    for s in ["attributes", "entitlements", "kas", "keycloak"]
}

openapi_enable = {
    ("%s.openapiUrl" % s): "/openapi"
    for s in ["attributes", "entitlements"]
}

server_root = {
    ("%s.serverRootPath" % s): ("/api/%s" % s)
    for s in ["attributes", "entitlements"]
}

cors_origins = {
    ("%s.serverCorsOrigins" % s): host_arg
    for s in ["attributes", "entitlements"]
}


backend(set=dict(ingress_enable.items() + openapi_enable.items() + server_root.items() + cors_origins.items()))
