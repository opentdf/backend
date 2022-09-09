# Context: opentdf/backend/containers
# NOTE - The version is also needed in the site-packages COPY command below
# Context: opentdf/backend/containers
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
# Install application dependencies
COPY requirements.txt entitlements/requirements.txt
RUN pip3 install --no-cache-dir --upgrade pip setuptools && \
    pip3 install --no-cache-dir --requirement entitlements/requirements.txt
# Install application into WORKDIR
COPY *.py entitlements/
COPY VERSION entitlements/
COPY openapi.* entitlements/

RUN python3 -m compileall .

FROM build AS test
COPY tests entitlements/tests
RUN pip3 install --no-cache-dir --upgrade pip pytest
RUN python -m pytest entitlements/tests

FROM build AS validate-openapi
RUN diff <(python3 -m entitlements.main) entitlements/openapi.json

# stage - production server
FROM python:${PY_VERSION}-alpine${ALPINE_VERSION} AS production
ARG PY_VERSION

WORKDIR /app
COPY --from=build --chown=root:root /build/ .
# NOTE - the python version needs to be specified in the following COPY command:
COPY --from=build --chown=root:root /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
# add any new deployable directories and files from the build stage here

# Server
ENV SERVER_ROOT_PATH "/"
ENV SERVER_PORT "4030"
ENV SERVER_PUBLIC_NAME ""
ENV SERVER_LOG_LEVEL "INFO"
ENV SERVER_CORS_ORIGINS ""
# Postgres
ENV POSTGRES_HOST ""
ENV POSTGRES_PORT "5432"
ENV POSTGRES_USER "tdf_entitlement_manager"
ENV POSTGRES_PASSWORD ""
ENV POSTGRES_DATABASE "tdf_database"
ENV POSTGRES_SCHEMA "tdf_entitlement"
# OIDC
ENV OIDC_CLIENT_ID ""
ENV OIDC_CLIENT_SECRET ""
ENV OIDC_REALM ""
## trailing / is required
ENV OIDC_SERVER_URL ""
ENV OIDC_AUTHORIZATION_URL ""
ENV OIDC_TOKEN_URL ""
# Disable OpenAPI
ENV OPENAPI_URL ""

ENTRYPOINT python3 -m uvicorn \
    --host 0.0.0.0 \
    --port ${SERVER_PORT} \
    --root-path ${SERVER_ROOT_PATH} \
    --no-use-colors \
    --no-server-header \
    --log-level error \
    entitlements.main:app
