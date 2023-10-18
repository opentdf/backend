FROM registry.access.redhat.com/ubi9/go-toolset:1.18 AS builder

ENV GO111MODULE=on \
    CGO_ENABLED=0

# Copy the code necessary to build the application
# Hoovering in everything here doesn't matter -
# we're going to discard this intermediate image later anyway
# and just copy over the resulting binary
COPY . .

# Build the application
RUN go build .

# Create the minimal runtime image
FROM registry.access.redhat.com/ubi9-micro:9.1 AS emptyfinal

# use non-root user
USER 10001

COPY --from=builder --chown=10001:10001 /opt/app-root/src/entity-resolution /entity-resolution-service

ENTRYPOINT ["/entity-resolution-service"]
