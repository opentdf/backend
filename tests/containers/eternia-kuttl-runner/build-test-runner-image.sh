#!/usr/bin/env bash
set -euo pipefail

CONTAINER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null && pwd)"
PROJECT_DIR="$(git rev-parse --show-toplevel)"
ETERNIA_PATH="$(cd "${PROJECT_DIR}/../eternia" >/dev/null && pwd)"
export PATH="$PATH:$PROJECT_DIR/tools"

IMAGE_NAME="opentdf/eternia-kuttl-runner"
IMAGE_TAG="$(git rev-parse --short HEAD)"

pushd "${ETERNIA_PATH}" || {
  monolog ERROR "To build this test runner, you need a copy of the Eternia git repo cloned next to your Etheria top-level folder"
  exit 1
}

monolog TRACE "Moving to Eternia to build base image with SDK-CLI.."

# Use the current Eternia Git commit SHA as this test runner's image tag
BASE_VER="$(git rev-parse --short HEAD)"

monolog INFO "Tagging this test runner with current Eternia HEAD: [${BASE_VER}]"
docker build --target tester -t eternia-base .
monolog TRACE "Built eternia-base at [${BASE_VER}]"
popd

pushd "${CONTAINER_DIR}" || {
  monolog ERROR "Failed to cd to container context"
  exit 1
}
docker build -t $IMAGE_NAME:$IMAGE_TAG .
monolog INFO "Built $IMAGE_NAME image; to push this to Dockerhub run: [docker push $IMAGE_NAME:$IMAGE_TAG]"
popd
