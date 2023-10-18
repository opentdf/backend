all: dockerbuild

COMPONENT_NAME=bootstrap
COMPONENT_NAME_SNAKE=bootstrap
IMAGE:=ghcr.io/opentdf/keycloak-bootstrap
PLATFORMS?=linux/arm64,linux/amd64
VERSION:=$(shell cat VERSION)
VENV_DIR:=.venv
PIPENV_VENV_IN_PROJECT := enabled

.PHONY: localbuild
localbuild: lint
	mkdir -p ${VENV_DIR}
	pipenv install

.PHONY: dockerbuild
dockerbuild:
	@DOCKER_BUILDKIT=1 docker buildx build --platform $(PLATFORMS) --ssh default -t $(IMAGE):$(VERSION) .

.PHONY: dockerbuildpush
dockerbuildpush: dockerbuild
	@DOCKER_BUILDKIT=1 docker buildx build --platform $(PLATFORMS) --ssh default -t $(IMAGE):$(VERSION) --push .

.PHONY: run
run:
	pipenv run ./bootstrap.py

.PHONY: testenv
testenv:
	pipenv install --dev

.PHONY: test
test:
	pipenv run pytest --cov-config=.coveragerc --cov=. \
	  --cov-report=term-missing
	  
.PHONY: lint
lint: testenv
	pipenv run pylint bootstrap.py

.PHONY: dockertestenv
dockertestenv:
	pipenv --rm || true
	pipenv install --dev
	pipenv run pytest --cov-config=.coveragerc --cov=. \
	  --cov-report=term-missing
	pipenv --rm || true

.PHONY: clean
clean:
	rm -rf __pycache__ dist/ build/ \
	  src/${COMPONENT_NAME_SNAKE}.egg-info

.PHONY: venvclean
venvclean:
	pipenv --rm || true

