# docker build -t ct1 -f xtest/Dockerfile . && docker run --net=host ct1
# We need `node` for the test harness and node tests, and python pysdk testing
ARG NODE_VERSION=16
ARG PY_OSS_VERSION=1.1.1
ARG PY_TEST_VERSION=3.8

FROM node:${NODE_VERSION}

RUN apt-get update || : && apt-get -y install \
  curl \
  default-jdk \
  jq \
  python:${PY_TEST_VERSION} \
  python3-pip \
  python3-venv
RUN pip3 install --upgrade pip
RUN python3 --version

# test
WORKDIR /wrk
COPY ./tests/containers/clients/package.json \
 ./tests/containers/clients/package-lock.json \
 ./tests/containers/clients/requirements.txt \
 ./tests/containers/clients/opentdf-client-0.0.2.tgz \
 ./tests/containers/clients/opentdf-cli-0.0.2.tgz \
 /wrk/
RUN npm install
RUN pip3 install --requirement /wrk/requirements.txt || true
COPY ./scripts /scripts
COPY ./tests/containers/clients /wrk
ENV KAS_ENDPOINT http://host.docker.internal:65432/api/kas
ENV OIDC_ENDPOINT http://host.docker.internal:65432

CMD ["python3", "xtest.py", "--attrtest"]
