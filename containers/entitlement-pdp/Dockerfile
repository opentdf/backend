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
COPY /handlers/ ./handlers/
COPY /pdp/ ./pdp/
COPY VERSION .
# build
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w -X main.Version=$(cat <VERSION)"
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
ENV HOME=/opt/entitlement-pdp
ENV CACHEDIR=$HOME/policycache/bundles/entitlement-policy
RUN mkdir -p $CACHEDIR
RUN chmod -R 777 /opt/entitlement-pdp

# use non-root user
USER 10001

WORKDIR $HOME
# openapi
COPY --chown=10001:10001 openapi.json .
COPY --chown=10001:10001 --from=builder /build/entitlement-pdp /entitlement-pdp
COPY --chown=10001:10001 --chmod=777 --from=policy-builder /build/bundle.tar.gz $CACHEDIR/bundle.tar.gz
ENTRYPOINT ["/entitlement-pdp"]
# END AS production

