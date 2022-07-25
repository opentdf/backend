#!/usr/bin/env bash

if [ "$#" -lt 3 ]; then
    echo "Usage: $0 [jobname] [duration] [namespace]"
    exit
fi
# Since `tilt` isn't good at waiting for normal Kube resources it hasn't previously created itself/pretends things it didn't create don't exist, do that here.

echo "**************************************"
echo "Waiting (up to $2) for $1 job to complete"
echo "**************************************"
if kubectl get $1 -n $3; then kubectl wait --for=condition=complete --timeout=$2 $1; fi
