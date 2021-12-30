# NOTE - The version is also needed in the site-packages COPY command below
# context must be parent folder
ARG PY_VERSION=3.10
ARG ALPINE_VERSION=3.15

# stage - build
FROM virtru/tdf-python-base:${PY_VERSION} AS build
WORKDIR /build
# Install application dependencies
COPY service_entity_object/requirements.txt .
RUN pip3 install --no-cache-dir --requirement requirements.txt
# Install application into WORKDIR
COPY __init__.py .
COPY __init__.py containers/
COPY python_base/*.py containers/python_base/
COPY service_entity_object/*.py containers/claims/
# Compile application
RUN python3 -m compileall .
# stage - production server
FROM python:${PY_VERSION}-alpine${ALPINE_VERSION} AS production
ARG PY_VERSION
# Install apk dependencies
RUN apk add --no-cache --upgrade \
    bash \
    postgresql-client \
    libressl
# Install pip dependencies
#RUN pip3 install --no-cache-dir \
#    "uvicorn[standard]"
WORKDIR /app
COPY --from=build --chown=root:root /build/ .
# NOTE - the python version needs to be specified in the following COPY command:
COPY --from=build --chown=root:root /usr/local/lib/python${PY_VERSION}/site-packages/ /usr/local/lib/python${PY_VERSION}/site-packages
# add any new deployable directories and files from the build stage here

# Application
ENV EAS_PRIVATE_KEY ""
ENV EAS_ENTITY_EXPIRATION ""
ENV KAS_DEFAULT_URL ""
ENV KAS_CERTIFICATE ""
ENV KAS_EC_SECP256R1_CERTIFICATE ""
# Server
ENV SERVER_ROOT_PATH ""
ENV SERVER_PORT "4010"
ENV SERVER_PUBLIC_NAME ""
ENV SERVER_LOG_LEVEL "INFO"
ENV SERVER_CORS_ORIGINS ""
# Postgres
ENV POSTGRES_HOST ""
ENV POSTGRES_PORT "5432"
ENV POSTGRES_USER ""
ENV POSTGRES_PASSWORD ""
ENV POSTGRES_DATABASE ""
ENV POSTGRES_SCHEMA "tdf_entitlement"
# Disable OpenAPI
ENV OPENAPI_URL ""

ENTRYPOINT env & python3 -m uvicorn \
    --host 0.0.0.0 \
    --port ${SERVER_PORT} \
    --root-path ${SERVER_ROOT_PATH} \
    --no-use-colors \
    --no-server-header \
    --log-level error \
    --app-dir ./containers \
    claims.main:app