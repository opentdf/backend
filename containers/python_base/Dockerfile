ARG PY_VERSION=3.10
ARG ALPINE_VERSION=3.16

# stage - build
FROM python:${PY_VERSION}-alpine${ALPINE_VERSION} AS build
# CVE-2022-40674 - updating here until alpine does a relase with the fix - this can be removed once released
RUN apk info expat && apk update expat=2.4.9-r0 && apk info expat
# Install apk dependencies
RUN apk add --no-cache --upgrade \
    gcc \
    rust \
    build-base \
    postgresql-dev \
    postgresql-client \
    libressl-dev \
    musl-dev \
    zlib-dev \
    jpeg-dev \
    libffi-dev \
    openssl \
    bash

COPY ./scripts /scripts

WORKDIR /build
# Install pip dependencies
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip setuptools && \
    pip3 install --no-cache-dir -r requirements.txt
