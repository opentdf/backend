FROM registry.access.redhat.com/ubi9/go-toolset:1.18 AS builder

ARG GOLANGCI_VERSION=v1.49.0
ARG COVERAGE_THRESH_PCT=19
ARG OPCR_POLICY_VERSION=v0.1.42
ARG OVERCOVER_VERSION=v1.2.1

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
FROM registry.access.redhat.com/ubi9-minimal:9.1 AS emptyfinal

COPY --from=builder /opt/app-root/entity-resolution-service /entity-resolution-service

ENTRYPOINT ["/entity-resolution-service"]
