# syntax=docker/dockerfile:experimental

# ^ remove that experimental tag when we migrate off of Docker v19
# as it is not required in current versions (v20 onward) of Docker

FROM golang:1.18-alpine AS builder

ARG GOLANGCI_VERSION=v1.46.0
ARG COVERAGE_THRESH_PCT=19

ENV GO111MODULE=on \
    CGO_ENABLED=0

# Get git and openssh client tools (for go mod private repo fetch over ssh)
RUN apk add --no-cache git=~2 openssh-client=~9 wget=~1

# Git creds come from host mount, but we need to do some setup to make sure fetching internal Virtru
# private Git repos via Go works correctly
# hadolint ignore=SC2174
RUN git config --global url."git@github.com:".insteadOf "https://github.com/" \
    && mkdir -p -m 0600 ~/.ssh \
    && ssh-keyscan github.com >> ~/.ssh/known_hosts

# Get test coverage tool and swagger codegen
RUN go install github.com/klmitch/overcover@latest \
    && go install github.com/swaggo/swag/cmd/swag@latest

WORKDIR /build

# Copy the code necessary to build the application
# Hoovering in everything here doesn't matter -
# we're going to discard this intermediate image later anyway
# and just copy over the resulting binary
COPY . .

# Generate swagger docs from API def.
RUN swag init

# Vendor modules here (that is, download them, using SSH creds if need be) so that subsequent steps don't
# re-fetch, and just use the vendored versions
RUN --mount=type=ssh go mod vendor

# Let's create a /dist folder containing just the files necessary for runtime.
# Later, it will be copied as the / (root) of the output image.
RUN mkdir /dist

# Run linters
SHELL ["/bin/ash", "-eo", "pipefail", "-c"]
RUN wget -O- -nv https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b ./ ${GOLANGCI_VERSION}

RUN ./golangci-lint --version && ./golangci-lint run --timeout 10m

# Run tests
RUN go test --coverprofile cover.out ./...

# Test coverage
RUN overcover --coverprofile cover.out ./... --threshold ${COVERAGE_THRESH_PCT}

# Build the application
RUN go build -o /dist/entitlement-pdp

# Create the minimal runtime image
FROM golang:1.18-alpine AS emptyfinal

COPY --chown=0:0 --from=builder /dist/entitlement-pdp /entitlement-pdp

ENTRYPOINT ["/entitlement-pdp"]
