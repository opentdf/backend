# syntax=docker/dockerfile:1
ARG ALPINE_VERSION=3.17
ARG GOLANG_VERSION=1.20
FROM golang:${GOLANG_VERSION}-alpine${ALPINE_VERSION} AS builder
WORKDIR /build/
# dependencies
COPY go.mod go.sum ./
RUN go mod download
# copy Go files - add new package to this list
COPY *.go ./
COPY /docs/ ./docs/
COPY /handlers/ ./handlers/
COPY /pdp/ ./pdp/
COPY VERSION .
# build
RUN CGO_ENABLED=0 GOOS=linux go build
# END AS builder

FROM golang:${GOLANG_VERSION}-alpine${ALPINE_VERSION} AS policy-builder
ARG OPCR_POLICY_VERSION=v0.1.42
WORKDIR /build/
RUN go install github.com/opcr-io/policy/cmd/policy@${OPCR_POLICY_VERSION}
COPY /entitlement-policy/ ./entitlement-policy/
COPY offline-config-example/opa-config.yaml ./
COPY VERSION .
# Build a local copy of the policy - normally OPA will be configured to fetch the policybundle from
# an OCI registry, and using a cluster-local OCI registry would be the best approach for offline mode for all OCI artifacts generally,
# but until we have a local OCI registry for offline scenarios, just pack a
# .tar.gz policy bundle into the cache which can (if OPA is configured accordingly) be used as a fallback
# when the remote OCI bundle is unreachable.
RUN policy build entitlement-policy -t local:$(cat <VERSION) \
    && policy save local:$(cat <VERSION)
# END AS policy-builder

# Create the minimal runtime image
FROM alpine:${ALPINE_VERSION} AS production
# policy bundle
ENV OPA_POLICY_BUNDLE_PATH=/opt/app-root/src/entitlement-pdp/policycache/bundles/entitlement-policy/bundle.tar.gz
ENV OPA_CONFIG_PATH=/etc/opa/config/opa-config.yaml
COPY --from=policy-builder /build/bundle.tar.gz $OPA_POLICY_BUNDLE_PATH
COPY --from=policy-builder /build/opa-config.yaml $OPA_CONFIG_PATH
# service
COPY --from=builder /build/entitlement-pdp /entitlement-pdp
ENTRYPOINT ["/entitlement-pdp"]
# END AS production
