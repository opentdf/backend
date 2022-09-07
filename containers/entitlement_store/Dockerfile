# Context: opentdf/backend/containers
# NOTE - The version is also needed in the site-packages COPY command below
# context must be parent folder
ARG PY_VERSION=3.10
ARG ALPINE_VERSION=3.16
ARG CONTAINER_REGISTRY=ghcr.io
ARG PYTHON_BASE_IMAGE_SELECTOR=:${PY_VERSION}

FROM ${CONTAINER_REGISTRY}/opentdf/python-base${PYTHON_BASE_IMAGE_SELECTOR} AS base

FROM base AS build 
COPY --from=base --chown=root:root /build/ /build/python_base/
COPY --from=base --chown=root:root /scripts/ /scripts/
COPY --from=base --chown=root:root /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/

WORKDIR /build
COPY requirements.txt entitlement_store/requirements.txt
RUN pip3 install --no-cache-dir --upgrade pip setuptools && \
    pip3 install --no-cache-dir --requirement entitlement_store/requirements.txt
COPY *.py entitlement_store/
COPY VERSION entitlement_store/

RUN python3 -m compileall .
COPY openapi.json entitlement_store/


FROM build AS test
COPY tests entitlement_store/tests
RUN pip3 install --no-cache-dir --upgrade pip pytest
RUN python -m pytest entitlement_store/tests


FROM build AS validate-openapi
RUN diff <(python3 -m entitlement_store.main) entitlement_store/openapi.json


FROM python:${PY_VERSION}-alpine${ALPINE_VERSION} AS production
ARG PY_VERSION

WORKDIR /app
COPY --from=build --chown=root:root /build/ .
# NOTE - the python version needs to be specified in the following COPY command:
COPY --from=build --chown=root:root /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages
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
