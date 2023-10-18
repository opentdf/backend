# Context: opentdf/backend/containers
# NOTE - The version is also needed in the site-packages COPY command below
# context must be parent folder
ARG PY_VERSION=3.10
ARG ALPINE_VERSION=3.17
ARG CONTAINER_REGISTRY=docker.io
ARG PYTHON_BASE_IMAGE_SELECTOR=:${PY_VERSION}

# stage - build
FROM ${CONTAINER_REGISTRY}/opentdf/python-base${PYTHON_BASE_IMAGE_SELECTOR} AS build
WORKDIR /build
# Install application dependencies
COPY entitlement_store/requirements.txt entitlement_store/requirements.txt
COPY python_base/requirements.txt python_base/requirements.txt
RUN pip3 install --no-cache-dir --upgrade pip setuptools && \
    pip3 install --no-cache-dir --requirement entitlement_store/requirements.txt
# Install application into WORKDIR
COPY python_base/*.py python_base/
COPY entitlement_store/*.py entitlement_store/
COPY entitlement_store/VERSION entitlement_store/

# Compile application
RUN python3 -m compileall .

# Validate openapi
COPY entitlement_store/openapi.json entitlement_store/

FROM build AS validate-openapi
RUN diff <(python3 -m entitlement_store.main) entitlement_store/openapi.json

# stage - production server
FROM python:${PY_VERSION}-alpine${ALPINE_VERSION} AS production
ARG PY_VERSION

# use non-root user
USER 10001

WORKDIR /app
COPY --from=build --chown=10001:10001 /build/ .
# NOTE - the python version needs to be specified in the following COPY command:
COPY --from=build --chown=10001:10001 /usr/local/lib/python${PY_VERSION}/site-packages/ /usr/local/lib/python${PY_VERSION}/site-packages
# add any new deployable directories and files from the build stage here

# Application
ENV KAS_CERTIFICATE ""
ENV KAS_EC_SECP256R1_CERTIFICATE ""
# Server
ENV SERVER_ROOT_PATH "/"
ENV SERVER_PORT "5000"
ENV SERVER_PUBLIC_NAME ""
ENV SERVER_LOG_LEVEL "INFO"
# Postgres
ENV POSTGRES_HOST ""
ENV POSTGRES_PORT "5432"
ENV POSTGRES_USER ""
ENV POSTGRES_PASSWORD ""
ENV POSTGRES_DATABASE ""
ENV POSTGRES_SCHEMA "tdf_entitlement"

EXPOSE 5000
ENTRYPOINT python3 -m uvicorn \
    --host 0.0.0.0 \
    --port ${SERVER_PORT} \
    --root-path ${SERVER_ROOT_PATH} \
    --no-use-colors \
    --no-server-header \
    --log-level error \
    entitlement_store.main:app
