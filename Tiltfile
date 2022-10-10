# Tiltfile for development of OpenTDF backend
# reference https://docs.tilt.dev/api.html
# extensions https://github.com/tilt-dev/tilt-extensions
# helm remote usage https://github.com/tilt-dev/tilt-extensions/tree/master/helm_remote#additional-parameters

def dict_union(x, y):
   z = {}
   z.update(x)
   z.update(y)
   return z

load("./common.Tiltfile", "backend")

config.define_string('allow-origin')
cfg = config.parse()
host_arg = cfg.get('allow-origin', "http://localhost:3000")

ingress_enable = {
    ("%s.ingress.enabled" % s): "true"
    for s in ["attributes", "entitlements", "kas", "keycloak"]
}

cors_origins = {
    ("%s.serverCorsOrigins" % s): host_arg
    for s in ["attributes", "entitlements"]
}

merged_values = dict_union(ingress_enable, cors_origins)

backend(set=merged_values)
