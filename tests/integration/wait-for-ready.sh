#!/usr/bin/env bash

if [ "$#" -lt 3 ]; then
    echo "Usage: $0 [jobname] [duration] [namespace]"
    exit
fi
# Since `tilt` isn't good at waiting for normal Kube resources it hasn't previously created itself/pretends things it didn't create don't exist, do that here.

echo "[INFO] Waiting (up to $2) for [$1] job to complete"
echo "[DEBUG] [kubectl get $1 -n $3]"
if kubectl get "$1" -n "$3"; then
    if ! kubectl wait --for=condition=complete --timeout="$2" "$1"; then
        kubectl logs "$1"
    fi
fi
echo "[INFO] Finished waiting"
