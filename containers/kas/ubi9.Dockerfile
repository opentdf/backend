ARG PY_VERSION=3.11
ARG CONTAINER_REGISTRY=ghcr.io
ARG PYTHON_BASE_IMAGE_SELECTOR=:${PY_VERSION}-ubi9
ARG PROD_IMAGE_REGISTRY=registry.access.redhat.com/
ARG PROD_IMAGE=ubi9/python-311
ARG PROD_IMAGE_TAG=1

# KAS is a PEP (policy enforcement point) that depends on/wraps an internal PDP
# (policy definition point)
FROM golang:1.19-bullseye AS gobuilder
RUN mkdir /dist
RUN GOBIN=/dist go install github.com/virtru/access-pdp@v1.2.0

# stage - build
FROM ${CONTAINER_REGISTRY}/opentdf/python-base${PYTHON_BASE_IMAGE_SELECTOR} AS build

# Install pip dependencies
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1

# Establish a working directory in the container for tdf3_kas. This directory
# does not exist but will be created. All future commands root from here.

WORKDIR /kas_app
ENV PYTHONPATH .
ENV PYTHONUNBUFFERED 1

# NOTE - This must match the UID set for the certs in scripts/genkey_apps or the value passed in via docker --user
ENV KAS_UID ${KAS_UID:-909}

# Install application dependencies
COPY kas_app/requirements.txt /kas_app/
COPY kas_app/setup.py /kas_app/
COPY kas_core/setup.py /kas_core/
COPY kas_core/requirements.txt /kas_core/
# workaround for setuptools requiring root
USER root
RUN pip3 install --no-cache-dir --upgrade pip setuptools && \
    pip3 install --no-cache-dir -r requirements.txt
# Install and compiile application
COPY kas_app /kas_app/
COPY kas_core /kas_core/
# RUN python3 -m compileall .

CMD /bin/bash
# stage - production server
FROM ${PROD_IMAGE_REGISTRY}${PROD_IMAGE}:${PROD_IMAGE_TAG} AS production

ARG PY_VERSION

WORKDIR /kas_app
ENV KAS_UID ${KAS_UID:-909}

RUN pip3 install \
    gunicorn \
    gunicorn[gthread] \
    wsgicors

# workaround for groupadd and useradd requiring root
USER root
# Add kas user and kas group
RUN groupadd --system kas && useradd --system --uid ${KAS_UID:-909} kas --gid kas

COPY --from=build --chown=kas:kas /kas_app/ /kas_app
COPY --from=build --chown=kas:kas /kas_core/ /kas_core

COPY --from=build --chown=root:root /opt/app-root/lib/python${PY_VERSION}/site-packages/ /opt/app-root/lib/python${PY_VERSION}/site-packages

# add any new deployable directories and files from the build stage here
RUN mkdir -p /certs && chown kas /certs && chgrp kas /certs

# `tini` is a tiny, valid init process that runs inside the container
# We use it because we need to launch multiple processes from a single Docker
# entrypoint - this is a valid pattern, and in fact upstream Docker Desktop bundles
# `tini` expressly for this purpose - we're adding it here.
#
ENV TINI_VERSION=v0.19.0
# Note that this is automatically populated by `docker build/buildx` to be the correct target architecture (arm64/amd64)
ARG TARGETARCH
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini-${TARGETARCH} /sbin/tini
RUN chmod 755 /sbin/tini
# Copy over the standalone binary that is the PDP grpc server, as well as the
# tini launch script that starts both the PDP grpc server and KAS process.
RUN mkdir -p /opentdf/bin
COPY tini-init.sh /opentdf/bin/

COPY --chown=kas:kas --from=gobuilder /dist/access-pdp /opentdf/bin/access-pdp-grpc-server

# Run as kas instead of root
USER kas

# Configure Gunicorn
#
# See docs.gunicorn.org/en/latest/settings.html for options.
# The environment variables are those settings variables, but in uppercase
# prefixed with GUNICORN_ for easier parsing.
#
ENV GUNICORN_WORKERS 2
ENV GUNICORN_WORKER-TMP-DIR=/dev/shm
ENV GUNICORN_WORKER-CLASS=gthread
ENV GUNICORN_THREADS=1
ENV GUNICORN_BIND :8000

ENV LEGACY_NANOTDF_IV=1


# Environment variables used for CORS configuration
# See https://github.com/may-day/wsgicors for more info.
ENV WSGI_CORS_HEADERS *
ENV WSGI_CORS_METHODS *
ENV WSGI_CORS_MAX_AGE 180
ENV WSGI_CORS_ORIGIN *
# Publish stats
ENV STATSD_HOST ""
ENV STATSD_PORT "8125"

EXPOSE 8000

# Run program under Tini
ENTRYPOINT ["/sbin/tini", "--", "/opentdf/bin/tini-init.sh"]
