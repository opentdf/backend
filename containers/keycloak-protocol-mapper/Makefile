IMAGE=opentdf/keycloak
VERSION=15.0.2-r1
BITNAMI_BASE_IMAGE=virtru/keycloak-base
BITNAMI_BASE_VERSION=15.0.2
BITNAMI_DOCKER_REPO_TAG=15.0.2-debian-10-r106

all: build

# Destroy any previously-created buildx context
.PHONY: docker-buildx-armclean
docker-buildx-armclean:
	docker buildx use default
	docker buildx rm opentdf-keycloak-cross || true

# Clone the Bitnami docker image repo
.PHONY: bitnami-repo-clone
bitnami-repo-clone: docker-buildx-armclean
	rm -rf bitnami-docker-keycloak
	git clone -b ${BITNAMI_DOCKER_REPO_TAG} 'https://github.com/bitnami/bitnami-docker-keycloak.git'

# Set up a custom buildx context that supports building a multi-arch image
.PHONY: docker-buildx-armsetup
docker-buildx-armsetup: docker-buildx-armclean
	docker buildx create --name opentdf-keycloak-cross
	docker buildx use opentdf-keycloak-cross
	docker buildx inspect --bootstrap

# Use buildx to build and push an image with amd64 and arm64 compat
# NOTE that this base image has to be pushed to a registry before other images can be built off of it
# because of some buildkite manifest incompatibility stuff
# https://docs.docker.com/engine/reference/commandline/buildx_build/#output
.PHONY: bitnami-base-buildpush
bitnami-base-buildpush: docker-buildx-armsetup bitnami-repo-clone
	cd bitnami-docker-keycloak/*/*/ && \
		ls -lah && \
		docker buildx build --platform linux/amd64,linux/arm64 -t ${BITNAMI_BASE_IMAGE}:${BITNAMI_BASE_VERSION} --push .

.PHONY: dockerbuild
dockerbuild: bitnami-base-buildpush
	docker build -t ${IMAGE}:${VERSION} .

.PHONY: dockerbuildpush
dockerbuildpush: bitnami-base-buildpush
	docker push ${IMAGE}:${VERSION}
