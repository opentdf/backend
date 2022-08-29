# Tiltfile for development of OpenTDF backend
# reference https://docs.tilt.dev/api.html
# extensions https://github.com/tilt-dev/tilt-extensions
# helm remote usage https://github.com/tilt-dev/tilt-extensions/tree/master/helm_remote#additional-parameters

load("./common.Tiltfile", "backend")
load("./abacus.Tiltfile", "frontend")

ingress_enable = {
    ("%s.ingress.enabled" % s): "true"
    for s in ["attributes", "entitlements", "kas", "keycloak"]
}

backend(set=ingress_enable)
frontend()
