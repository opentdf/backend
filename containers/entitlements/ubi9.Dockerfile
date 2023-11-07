# Context: opentdf/backend/containers
# NOTE - The version is also needed in the site-packages COPY command below
# Context: opentdf/backend/containers
ARG PY_VERSION=3.9
ARG CONTAINER_REGISTRY=ghcr.io
ARG PYTHON_BASE_IMAGE_SELECTOR=:${PY_VERSION}-ubi9
ARG PROD_IMAGE_REGISTRY=registry.access.redhat.com/
ARG PROD_IMAGE=ubi9/python-39
ARG PROD_IMAGE_TAG=1

# stage - build
FROM ${CONTAINER_REGISTRY}/opentdf/python-base${PYTHON_BASE_IMAGE_SELECTOR} AS build
WORKDIR /build
# Install application dependencies
COPY entitlements/requirements.txt entitlements/requirements.txt
COPY python_base/requirements.txt python_base/requirements.txt
RUN pip3 install --no-cache-dir --upgrade pip setuptools && \
    pip3 install --no-cache-dir --requirement entitlements/requirements.txt
# Install application into WORKDIR
COPY python_base/*.py python_base/
COPY entitlements/*.py entitlements/
COPY entitlements/VERSION entitlements/
COPY entitlements/tests entitlements/tests

# Compile application
#RUN python3 -m compileall .

# Validate openapi
COPY entitlements/openapi.json entitlements/

FROM build AS validate-openapi
RUN diff <(python3 -m entitlements.main) entitlements/openapi.json

# stage - production server
FROM ${PROD_IMAGE_REGISTRY}${PROD_IMAGE}:${PROD_IMAGE_TAG} AS production
ARG PY_VERSION

WORKDIR /app
COPY --from=build --chown=root:root /build/ .
# NOTE - the python version needs to be specified in the following COPY command:
COPY --from=build --chown=root:root --chmod=755 /opt/app-root/lib/python${PY_VERSION}/site-packages/ /opt/app-root/lib/python${PY_VERSION}/site-packages
# add any new deployable directories and files from the build stage here

# use non-root user
USER 10001

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
