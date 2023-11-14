FROM golang:1.19-alpine AS builder

ARG GOLANGCI_VERSION=v1.49.0
ARG COVERAGE_THRESH_PCT=55

ENV GO111MODULE=on \
    CGO_ENABLED=0

# Get git and other tools needed
RUN apk add --no-cache git=~2 wget=~1

# Get test coverage tool and swagger, codegen
RUN go install github.com/klmitch/overcover@latest && \
    go install github.com/swaggo/swag/cmd/swag@v1.8.4 && \
    go install github.com/golangci/golangci-lint/cmd/golangci-lint@${GOLANGCI_VERSION}

WORKDIR /build

# Copy the code necessary to build the application
# Hoovering in everything here doesn't matter -
# we're going to discard this intermediate image later anyway
# and just copy over the resulting binary
COPY . .

# Generate swagger docs from API def.
RUN swag init

# Vendor modules here so that subsequent steps don't
# re-fetch, and just use the vendored versions
RUN go mod vendor

# Let's create a /dist folder containing just the files necessary for runtime.
# Later, it will be copied as the / (root) of the output image.
RUN mkdir /dist

# TODO this is very slow on `arm64` - like 5x slower
RUN golangci-lint --version && golangci-lint run --timeout 20m

# Run tests
RUN go test --coverprofile cover.out ./...

# Test coverage
RUN overcover --coverprofile cover.out ./... --threshold ${COVERAGE_THRESH_PCT}

# Build the application
RUN go build -o /dist/entity-resolution-service


# Create the minimal runtime image
FROM golang:1.19-alpine AS emptyfinal

COPY --chown=root:root --chmod=755 --from=builder /dist/entity-resolution-service /entity-resolution-service

# use non-root user
USER 10001

ENTRYPOINT ["/entity-resolution-service"]
