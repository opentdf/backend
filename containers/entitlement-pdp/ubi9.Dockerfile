# syntax=docker/dockerfile:1
#  image from https://catalog.redhat.com/software/containers/ubi9/go-toolset/61e5c00b4ec9945c18787690
FROM registry.access.redhat.com/ubi9/go-toolset:1.19 AS builder
# enable FIPS security - not working at the moment Case #03539611
#USER root
#RUN fips-mode-setup --enable
#USER default
#RUN fips-mode-setup --is-enabled
# dependencies
COPY go.mod go.sum ./
RUN go mod download
# copy Go files - add new package to this list
COPY *.go ./
COPY /docs/ ./docs/
COPY /handlers/ ./handlers/
COPY /pdp/ ./pdp/
# build
RUN CGO_ENABLED=0 GOOS=linux go build
# END AS builder

FROM registry.access.redhat.com/ubi9/go-toolset:1.19 AS policy-builder
ARG OPCR_POLICY_VERSION=v0.1.42
RUN go install github.com/opcr-io/policy/cmd/policy@${OPCR_POLICY_VERSION}
# Build a local copy of the policy - normally OPA will be configured to fetch the policybundle from
# an OCI registry, and using a cluster-local OCI registry would be the best approach for offline mode for all OCI artifacts generally,
# but until we have a local OCI registry for offline scenarios, just pack a
# .tar.gz policy bundle into the cache which can (if OPA is configured accordingly) be used as a fallback
# when the remote OCI bundle is unreachable.
RUN /opt/app-root/src/go/bin/policy build entitlement-policy -t local:$(cat <VERSION) \
    && /opt/app-root/src/go/bin/policy save local:$(cat <VERSION)
# END AS policy-builder

# Create the minimal runtime image
FROM registry.access.redhat.com/ubi9-micro:9.2 AS production
# policy bundle
#ENV CACHEDIR=/opt/app-root/src/entitlement-pdp/policycache/bundles/entitlement-policy
#RUN mkdir -p $CACHEDIR
#COPY --from=policy-builder /opt/app-root/src/bundle.tar.gz $CACHEDIR/bundle.tar.gz
# service
COPY --from=builder /opt/app-root/src/entitlement-pdp /entitlement-pdp

ENTRYPOINT ["/entitlement-pdp"]
# END AS production

FROM registry.access.redhat.com/ubi9/go-toolset:1.19 AS test-fips
RUN go get github.com/acardace/fips-detect .
COPY --from=production /entitlement-pdp /entitlement-pdp
RUN ./fips-detect
# END AS test-fips
