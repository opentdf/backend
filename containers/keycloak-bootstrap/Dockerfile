ARG PY_VERSION=3.10
ARG ALPINE_VERSION=3.17

FROM python:${PY_VERSION}-alpine${ALPINE_VERSION}

ENV FLASK_APP=app.py
ENV FLASK_ENV=development
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1

WORKDIR /project
COPY VERSION VERSION
COPY bootstrap.py /project/bootstrap.py
COPY keycloak_bootstrap.py /project/keycloak_bootstrap.py
COPY entitlements_bootstrap.py /project/entitlements_bootstrap.py
COPY attributes_bootstrap.py /project/attributes_bootstrap.py
COPY requirements.txt /project/

RUN apk add --no-cache curl

RUN pip install --upgrade pip && \
    pip install --no-cache-dir --requirement requirements.txt

CMD ["/project/bootstrap.py"]
