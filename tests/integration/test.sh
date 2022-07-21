#!/usr/bin/env bash

# Since `tilt` isn't good at waiting for normal Kube resources it hasn't previously created itself/pretends things it didn't create don't exist, do that here.

echo "**************************************"
echo "Waiting (up to 10 min) for keycloak-bootstrap job to complete"
echo "**************************************"
if kubectl get job/keycloak-bootstrap -n default; then kubectl wait --for=condition=complete --timeout=10m job/keycloak-bootstrap; fi
echo "**************************************"
echo "Running 'Tiltfile.xtest'....
echo "**************************************"

# TODO move this tiltfile into this folder
tilt -f ../../Tiltfile.xtest
