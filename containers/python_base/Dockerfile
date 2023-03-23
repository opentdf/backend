ARG BUILD_IMAGE_REGISTRY=registry.access.redhat.com/
ARG BUILD_IMAGE=ubi9/python-39
ARG BUILD_IMAGE_TAG=1

# stage - build
FROM $BUILD_IMAGE_REGISTRY$BUILD_IMAGE:$BUILD_IMAGE_TAG AS build

COPY ./scripts /scripts

WORKDIR /build
# Install pip dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip setuptools && \
    pip3 install --no-cache-dir -r requirements.txt
