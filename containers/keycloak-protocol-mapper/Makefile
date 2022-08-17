OTDF_IMAGE=opentdf/keycloak
OTDF_VERSION:=$(shell cat VERSION)
KEYCLOAK_BASE_VERSION:=$(shell cut -d- -f1 < VERSION)
KEYCLOAK_BASE_IMAGE=quay.io/keycloak/keycloak

# Destroy any previously-created buildx context
.PHONY: docker-buildx-armclean
docker-buildx-armclean:
	docker buildx use default
	docker buildx rm opentdf-keycloak-cross || true

# Set up a custom buildx context that supports building a multi-arch image
.PHONY: docker-buildx-armsetup
docker-buildx-armsetup: docker-buildx-armclean
	docker buildx create --name opentdf-keycloak-cross
	docker buildx use opentdf-keycloak-cross
	docker buildx inspect --bootstrap

.PHONY: dockerbuild
dockerbuild:
	docker build -t ${OTDF_IMAGE}:$(OTDF_VERSION) .

.PHONY: dockerbuildpush
dockerbuildpush: dockerbuild
	docker push ${OTDF_IMAGE}:$(OTDF_VERSION)

#List targets in makefile
.PHONY: list
list:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$'
