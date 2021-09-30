#!/usr/bin/env bash

WORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null && pwd)"
PROJECT_ROOT="$(cd "${WORK_DIR}/../../" >/dev/null && pwd)"
CHART_ROOT="$PROJECT_ROOT/charts"
EXPORT_ROOT="$PROJECT_ROOT/build/export"
TOOLS_ROOT="$PROJECT_ROOT/containers/python_base/tools"
CERTS_ROOT="$PROJECT_ROOT/containers/python_base/certs"
export PATH="$TOOLS_ROOT:$PATH"

e() {
  local rval=$?
  monolog ERROR "${@}"
  exit $rval
}

: "${ETHERIA_TAG:="virtrulocal"}"
LOAD_IMAGES=1
LOAD_SECRETS=1
START_CLUSTER=1
export RUN_OFFLINE=
USE_KEYCLOAK=1

while [[ $# -gt 0 ]]; do
  key="$1"
  shift

  case "$key" in
    --no-keycloak)
      monolog TRACE "--no-keycloak"
      USE_KEYCLOAK=
      ;;
    --no-load-images)
      monolog TRACE "--no-load-images"
      LOAD_IMAGES=
      ;;
    --no-secrets)
      monolog TRACE "--no-secrets"
      LOAD_SECRETS=
      ;;
    --no-start)
      monolog TRACE "--no-start"
      START_CLUSTER=
      ;;
    --offline)
      monolog TRACE "--offline"
      RUN_OFFLINE=1
      ;;
    *)
      e "Unrecognized options: $*"
      ;;
  esac
done

. "${TOOLS_ROOT}/lib-local.sh"

# Make sure required utilities are installed.
local_info || e "Local cluster manager [${LOCAL_TOOL}] is not available"
kubectl version --client | monolog DEBUG || e "kubectl is not available"
helm version | monolog DEBUG || e "helm is not available"

if [[ $START_CLUSTER ]]; then
  local_start || e "Failed to start local k8s tool [${LOCAL_TOOL}]"
fi

maybe_load() {
  if [[ $LOAD_IMAGES ]]; then
    local_load $1 || e "Unable to load service image [${1}]"
  fi
}

if [[ $LOAD_IMAGES ]]; then
  monolog INFO "Caching locally-built development Etheria images in dev cluster"
  # Cache locally-built `latest` images, bypassing registry.
  # If this fails, try running 'docker-compose build' in the repo root
  for s in entity-attribute-service key-access-service abacus-web entitlement-service storage-service attribute-authority-service; do
    maybe_load virtru/tdf-$s:${ETHERIA_TAG}
  done
else
  monolog DEBUG "Skipping loading of locally built service images"
fi

if [[ $LOAD_SECRETS ]]; then
  $TOOLS_ROOT/genkeys-if-needed || e "Unable to generate keys"

  printf "\nCreating 'etheria-secrets'..."
  kubectl create secret generic etheria-secrets \
    "--from-file=EAS_PRIVATE_KEY=${CERTS_ROOT}/eas-private.pem" \
    "--from-file=EAS_CERTIFICATE=${CERTS_ROOT}/eas-public.pem" \
    "--from-file=KAS_EC_SECP256R1_CERTIFICATE=${CERTS_ROOT}/kas-ec-secp256r1-public.pem" \
    "--from-file=KAS_CERTIFICATE=${CERTS_ROOT}/kas-public.pem" \
    "--from-file=KAS_EC_SECP256R1_PRIVATE_KEY=${CERTS_ROOT}/kas-ec-secp256r1-private.pem" \
    "--from-file=KAS_PRIVATE_KEY=${CERTS_ROOT}/kas-private.pem" \
    "--from-file=ca-cert.pem=${CERTS_ROOT}/ca.crt" || e "create etheria-secrets failed"

  kubectl create secret generic attribute-authority-secrets --from-literal=POSTGRES_PASSWORD=myPostgresPassword || e "create aa secrets failed"
  kubectl create secret generic entitlement-secrets --from-literal=POSTGRES_PASSWORD=myPostgresPassword || e "create ea secrets failed"
  kubectl create secret generic tdf-storage-secrets \
    --from-literal=AWS_ACCESS_KEY_ID=myAccessKeyId \
    --from-literal=AWS_SECRET_ACCESS_KEY=mySecretAccessKey || e "create tdf-storage-secrets failed"
fi

# Only do this if we were told to disable Keycloak
# This should be removed eventually, as Keycloak isn't going away
if [[ $USE_KEYCLOAK ]]; then
  monolog INFO "Caching locally-built development opentdf Keycloak in dev cluster"
  for s in claim-test-webservice keycloak keycloak-bootstrap; do
    maybe_load virtru/tdf-$s:${ETHERIA_TAG}
  done

  monolog INFO --- "Installing Virtru-ified Keycloak"
  if [[ $RUN_OFFLINE ]]; then
    helm upgrade --install keycloak "${EXPORT_ROOT}"/keycloak-15.0.1.tgz -f "${WORK_DIR}/values-virtru-keycloak.yaml" --set image.tag=${ETHERIA_TAG:-virtrulocal} || e "Unable to helm upgrade keycloak"
  else
    helm upgrade --install keycloak --repo https://codecentric.github.io/helm-charts keycloak -f "${WORK_DIR}/values-virtru-keycloak.yaml" --set image.tag=${ETHERIA_TAG:-virtrulocal} || e "Unable to helm upgrade keycloak"
  fi
  monolog INFO "Waiting until Keycloak server is ready"

  while [[ $(kubectl get pods keycloak-0 -n default -o 'jsonpath={..status.conditions[?(@.type=="Ready")].status}') != "True" ]]; do
    sleep 5
  done

fi

monolog INFO --- "Umbrella chart"
val_file="${WORK_DIR}/values-all-in-one.yaml"
if [[ $ETHERIA_TAG ]]; then
  sed "s/:virtrulocal/:$ETHERIA_TAG/" "${WORK_DIR}/values-all-in-one.yaml" > values-all.yaml.tmp
  val_file=values-all.yaml.tmp
fi
if [[ $RUN_OFFLINE ]]; then
  helm upgrade --install etheria "${CHARTS_ROOT}"/etheria -f "${val_file}" || e "Unable to install composite chart"
else
  helm repo add virtru https://charts.production.virtru.com || true #Might fail if you've already done this, and that's OK
  helm dependency update "$CHART_ROOT/etheria" || e "Unable to update composite chart"
  helm upgrade --install etheria "$CHART_ROOT/etheria" -f "${val_file}" || e "Unable to install composite chart"
fi
