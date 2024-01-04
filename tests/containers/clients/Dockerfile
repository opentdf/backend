# We need `node` for the test harness and node tests, and python pysdk testing
ARG PY_OSS_VERSION=1.1.1
ARG PY_TEST_VERSION=3.10
ARG NPM_SOURCE npmjs



FROM python:${PY_TEST_VERSION}

# Latest pip to avoid noisy pip complaints
RUN pip3 install --upgrade pip

# Generic node-js advice: https://github.com/nodesource/distributions#nodejs
ENV NODE_VERSION 18
RUN apt-get update || : && apt-get -y install \
  ca-certificates \
  curl \
  default-jdk \
  gnupg \
  jq
RUN mkdir -p /etc/apt/keyrings
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - &&\
  apt-get install -y nodejs
RUN npm install -g npm
RUN python3 --version && pip3 --version && node --version && npm --version

# test
WORKDIR /wrk
COPY ./tests/containers/clients/package.json \
 ./tests/containers/clients/package-lock.json \
 ./tests/containers/clients/requirements.txt \
 ./tests/containers/clients/.npmrc \
 /wrk/
RUN npm install
RUN pip3 install --requirement /wrk/requirements.txt || true
COPY ./scripts /scripts
COPY ./tests/containers/clients /wrk
ENV KAS_ENDPOINT http://host.docker.internal:65432/api/kas
ENV OIDC_ENDPOINT http://host.docker.internal:65432

CMD ["python3", "xtest.py", "--attrtest"]
