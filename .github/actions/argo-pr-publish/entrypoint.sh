#!/bin/bash -l

GITHUB_REPO_URL="$GITHUB_SERVER_URL/$GITHUB_REPOSITORY"
GITHUB_REPO_NAME=$(echo $GITHUB_REPOSITORY | cut -d'/' -f2)
GITHUB_ORG=$(echo $GITHUB_REPOSITORY | cut -d'/' -f1)

aws eks update-kubeconfig --region us-west-2 --name k8s-mgmt

export ARGO_TOKEN=$(argo auth token)

# Submits an Argo workflow off of a Github PR event
#
# NOTE: In a PR context, we have to use $GITHUB_HEAD_REF to get the PR branch
# and then strip the `refs/heads/XXX` prefix off
# Note that in NON-PR contexts, $GITHUB_HEAD_REF is not defined, and you must use $GITHUB_REF instead
# For more info see: https://docs.github.com/en/actions/reference/environment-variables
argo submit -n argo-events ./.argo/publish/pr-workflow.yaml \
    --generate-name="${GITHUB_ORG}-${GITHUB_REPO_NAME}-$GITHUB_SHA" \
    -p ciCommitSha="$GITHUB_SHA" \
    -p gitRepoName=${GITHUB_REPO_NAME} \
    -p branch="${GITHUB_HEAD_REF#refs/*/}" \
    -p gitRepoUrl="${GITHUB_REPO_URL}" \
    --wait \
    --log
# done
