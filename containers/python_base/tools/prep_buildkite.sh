#!/usr/bin/env bash
# Ditch this in favor of Tilt and/or kuttl

TOOLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null && pwd)"
export PATH="$PATH:$TOOLS_DIR"

: "${LOCAL_TOOL:="minikube"}"
export LOCAL_TOOL

monolog TRACE "prep_buildkite: [$0 $*]"

SCRIPT_TO_EXECUTE=$1

# We must source as this adds a new entry to the $PATH
# shellcheck disable=SC1091
. "${TOOLS_DIR}/pre-reqs-linux.sh" docker helm kuttl tilt "${LOCAL_TOOL}" || {
  monolog ERROR "pre-reqs failed"
  exit 1
}

# import local_load
# shellcheck disable=SC1091
. "${TOOLS_DIR}/lib-local.sh"

monolog INFO "********** Running Etheria quickstart [${SCRIPT_TO_EXECUTE}] in [$BUILDKITE_BUILD_CHECKOUT_PATH]"
cd "$BUILDKITE_BUILD_CHECKOUT_PATH" || {
  monolog ERROR "Not in buildkite"
  exit 1
}
bash "${SCRIPT_TO_EXECUTE}" || {
  monolog ERROR "Failed: [${SCRIPT_TO_EXECUTE}]"
  exit 1
}

# TODO this step can be dropped eventually
# This KUTTL test runner is just a Docker image containing the latest Eternia code - we don't publish
# proper/official dev images currently so this is a hack/workaround
monolog INFO "********** Preloading Eternia KUTTL test runner into ${LOCAL_TOOL} using build agent Docker pull credentials"
docker pull opentdf/eternia-kuttl-runner:"${ETERNIA_RUNNER_VERSION}" || {
  monolog ERROR "Unable to pull: [opentdf/eternia-kuttl-runner:${ETERNIA_RUNNER_VERSION}]"
  exit 1
}

local_load opentdf/eternia-kuttl-runner:"${ETERNIA_RUNNER_VERSION}" || {
  monolog ERROR "Unable to load: [opentdf/eternia-kuttl-runner:${ETERNIA_RUNNER_VERSION}]"
  exit 1
}

monolog INFO "********** Executing KUTTL tests"
kubectl kuttl test tests/cluster
