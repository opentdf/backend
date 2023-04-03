FROM registry.access.redhat.com/ubi9/go-toolset:1.18 AS builder

ARG OPCR_POLICY_VERSION=v0.1.42

ENV GO111MODULE=on \
    CGO_ENABLED=0

RUN go install github.com/opcr-io/policy/cmd/policy@${OPCR_POLICY_VERSION}

# Copy the code necessary to build the application
# Hoovering in everything here doesn't matter -
# we're going to discard this intermediate image later anyway
# and just copy over the resulting binary
COPY . .

# Build the application
RUN go build .

# Build a local copy of the policy - normally OPA will be configured to fetch the policybundle from
# an OCI registry, and using a cluster-local OCI registry would be the best approach for offline mode for all OCI artifacts generally,
# but until we have a local OCI registry for offline scenarios, just pack a
# .tar.gz policy bundle into the cache which can (if OPA is configured accordingly) be used as a fallback
# when the remote OCI bundle is unreachable.
RUN /opt/app-root/src/go/bin/policy build entitlement-policy -t local:$(cat <VERSION) \
    && /opt/app-root/src/go/bin/policy save local:$(cat <VERSION)

# Create the minimal runtime image
FROM registry.access.redhat.com/ubi9-micro:9.1 AS emptyfinal

ENV HOME=/opt/app-root/src/entitlement-pdp
ENV CACHEDIR=$HOME/policycache/bundles/entitlement-policy

RUN mkdir -p $CACHEDIR

COPY --from=builder /opt/app-root/src/entitlement-pdp /entitlement-pdp
COPY --from=builder /opt/app-root/src/bundle.tar.gz $CACHEDIR/bundle.tar.gz

WORKDIR $HOME

ENTRYPOINT ["/entitlement-pdp"]
