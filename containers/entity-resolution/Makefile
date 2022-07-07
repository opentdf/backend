IMAGEVERSION?=$(shell cat VERSION)
IMAGETAG?=ghcr.io/opentdf/entity-resolution
PLATFORMS?=linux/arm64,linux/amd64
CGO_ENABLED=0
COVERAGE_THRESH_PCT=55

.PHONY: localprep
localprep: clean
	@echo "Making sure Go is installed"
	@go version
	@echo "Making sure golangci-lint is installed"
	@golangci-lint version
	@echo "Making sure overcover is installed"
	@go install github.com/klmitch/overcover@latest
	@echo "Making sure swag gen is installed"
	@go install github.com/swaggo/swag/cmd/swag@latest
	@echo "Generating swagger"
	@swag init
	@echo "Vendoring modules"
	@go mod vendor


.PHONY: clean
clean:
	@echo "Removing vendored Go module folder"
	@rm -rf vendor



# Set up a custom buildx context that supports building a multi-arch image
.PHONY: docker-buildx-armsetup
docker-buildx-armsetup:
    # Try to create builder context, ignoring failure if one already exists
	docker buildx create --name dcr-cross || true
	docker buildx use dcr-cross
	docker buildx inspect --bootstrap

.PHONY: dockerbuild
dockerbuild: clean docker-buildx-armsetup
	@echo "Building '$(IMAGETAG):$(IMAGEVERSION)' Docker image"
	@DOCKER_BUILDKIT=1 docker buildx build --platform $(PLATFORMS) --ssh default -t $(IMAGETAG):$(IMAGEVERSION) --build-arg COVERAGE_THRESH_PCT=$(COVERAGE_THRESH_PCT) .

.PHONY: dockerbuildpush
dockerbuildpush: clean docker-buildx-armsetup
	@echo "Publishing '$(IMAGETAG):$(IMAGEVERSION)' to Dockerhub"
	@DOCKER_BUILDKIT=1 docker buildx build --platform $(PLATFORMS) --ssh default -t $(IMAGETAG):$(IMAGEVERSION) --build-arg COVERAGE_THRESH_PCT=$(COVERAGE_THRESH_PCT) --push .

.PHONY: test
test: lint
	@echo "Testing Go code"
	@go test --coverprofile cover.out ./...
	@overcover --coverprofile cover.out ./... --threshold $(COVERAGE_THRESH_PCT)

.PHONY: lint
lint: localprep
	golangci-lint run --timeout 5m

.PHONY: build
build: localprep
	go build


