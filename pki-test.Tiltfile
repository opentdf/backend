load("./common.Tiltfile", "backend")

backend(values=["./tests/integration/backend-pki-values.yaml"])

# TODO PKI tests involve only clients, Ingress and Keycloak - they are not backend tests, they are frontend tests,
# and we should move them out of this repo if we keep them at all.
#
# PKI tests involve local clients using mTLS to go thru the cluster Ingress, and so we must port-forward
# We cannot use `tilt`'s native `port_forward` functionality because tilt will not "see" any resources it didn't create
# even if they're sitting right there in the cluster. And, as elsewhere, Tilt being both limited and controlling means
# we have to work around it.
local_resource(
    "kubectl-portforward-https",
    serve_cmd="kubectl port-forward service/ingress-nginx-controller 4567:443",
    resource_deps=["ingress-nginx-controller"],
)

local_resource(
    "pki-test",
    "python3 tests/integration/pki-test/client_pki_test.py",
    resource_deps=[
        "backend",
        "kubectl-portforward-https",
        "kubectl-portforward-http",
    ],
)
