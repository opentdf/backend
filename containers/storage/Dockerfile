# NOTE - The version is also needed in the site-packages COPY command below
ARG PY_VERSION=3.10
ARG CONTAINER_REGISTRY=ghcr.io
ARG PYTHON_BASE_IMAGE_SELECTOR=:${PY_VERSION}
ARG PROD_IMAGE_REGISTRY=registry.access.redhat.com/
ARG PROD_IMAGE=ubi9/python-39
ARG PROD_IMAGE_TAG=1

# stage - build
FROM ${CONTAINER_REGISTRY}/opentdf/python-base${PYTHON_BASE_IMAGE_SELECTOR} AS build
WORKDIR /build
# Install application dependencies
COPY Pipfile .
COPY Pipfile.lock .
RUN pipenv lock --keep-outdated --requirements > requirements.txt && \
    pip3 install --no-cache-dir -r requirements.txt
# Install application into WORKDIR
COPY *.py ./
COPY VERSION VERSION
# Compile application
# RUN python3 -m compileall .
# stage - production server
FROM python:${PY_VERSION}-alpine${ALPINE_VERSION} AS production
ARG PY_VERSION
# Install apk dependencies
RUN apk add --no-cache --upgrade \
    bash \
    libressl
# Install pip dependencies
#RUN pip3 install --no-cache-dir \
#    "uvicorn[standard]"
WORKDIR /app
COPY --from=build /build/ .
# NOTE - the python version needs to be specified in the following COPY command:
COPY --from=build /opt/app-root/lib/python${PY_VERSION}/site-packages/ /opt/app-root/lib/python${PY_VERSION}/site-packages
# add any new deployable directories and files from the build stage here

# Application
ENV BUCKET ""
ENV SERVER_LOG_LEVEL "INFO"

EXPOSE 4050
ENTRYPOINT python3 -m uvicorn --host 0.0.0.0 --port 4050 main:app
