# Protected Data Format Reference Services and Support Tools · [![Build status](https://badge.buildkite.com/7f4ea01205aa3096d9c5cb3404ce0285b4310d33626f46a049.svg?branch=master)](https://buildkite.com/virtru/etheria-pr)

This repository is for a reference implementation of the [TDF3 Services](https://github.com/virtru/tdf3-spec), and sufficient tooling and testing to support the development of it.

## Monorepo

Etheria is a monorepo which contains the following projects:

- EAS
  - [Readme](eas/README.md)
  - ![Linting and Coverage](https://github.com/virtru/etheria/workflows/Linting%20and%20Coverage/badge.svg)
  - ![Validate OpenAPI](https://github.com/virtru/etheria/workflows/Validate%20OpenAPI/badge.svg)
- KAS
  - [Readme](kas/lib/README.md)
  - ![Linting and Coverage](https://github.com/virtru/etheria/workflows/Linting%20and%20Coverage/badge.svg)
  - ![Validate OpenAPI](https://github.com/virtru/etheria/workflows/Validate%20OpenAPI/badge.svg)
- Abacus Web
  - [Readme](abacus/web/README.md) 
  - ![Abacus Lint & Test](https://github.com/virtru/etheria/workflows/Abacus%20Lint%20&%20Test/badge.svg)
  - [Storybook](https://virtru.github.io/etheria)
  - ![Deploy Storybook](https://github.com/virtru/etheria/workflows/Deploy%20Storybook/badge.svg)
- A reference Keycloak OIDC identity provider handling auth flows
  - [Readme](README-keycloak-idp.md)
  - [KUTTL K8S Cluster tests](tests/README.md)
- _Misc_
  - ![Docker Deploy](https://github.com/virtru/etheria/workflows/Docker%20Deploy/badge.svg)

In addition to the products there are a number of supporting tools and test suites which are described in this document.

### Monorepo structure

1. The `containers` folder contains individual containerized services in folders, each of which should have a `Dockerfile`
1. The build context for each individual containerized service _should be restricted to the folder of that service_ - shared dependencies should either live in a shared base image, or be installable via package management.

## Quick Start and Development

This quick start guide is primarily for development and testing the EAS and KAS infrastructure. See [Production](#production) for details on running in production.

### Tilt

https://tilt.dev

#### Install

https://docs.tilt.dev/install.html

`brew install tilt-dev/tap/tilt`

#### Usage

##### Local Quickstart

```shell
# Install pre-requisites (drop what you've already got)
./tools/pre-reqs docker helm tilt kind octant

# Generate local certs in certs/ directory
./tools/genkeys-if-needed

# Create a local cluster, using e.g. kind
kind create cluster --name opentdf

# start
tilt up --context kind-opentdf

# Hit spacebar to open web UI

# stop and cleanup
tilt down
```

> (Optional) Run `octant` -> This will open a browser window giving you an overview of your local cluster.

### PR builds

When you open a Github PR, an Argo job will run which will publish all Etheria images and Helm charts to Virtru's image/chart
repos under the git shortSha of your PR branch.

To add the Virtru Helm chart repo (one time step)

``` sh
helm repo add virtru https://charts.production.virtru.com
helm repo update
```

> NOTE: Docker images are tagged with longSha, Helm charts are tagged with shortSha
> NOTE: You can check the Argo build output to make sure you're using the same SHAs that Argo published.

This means you can fetch any resource built from your PR branch by appending your SHA.

For instance, if Argo generated a shortSha of `b616e2f`, to fetch the KAS chart for that branch, you would run

`helm pull virtru/kas --version 0.4.4-rc-$(git rev-parse --short HEAD) --devel`

Or, if you wanted to install all of Etheria, you could fetch the top-level chart (which will have all subcharts and images updated to the current PR branch's SHA)

`helm pull virtru/etheria --version 0.1.1-rc-b616e2f --devel`

### (Deprecated) Local `docker-compose`

If you don't want to fool with `minikube`, you can still stand everything up using `docker-compose` - this is not recommended
going forward, but it's an option if you want it.

For this mode, we use docker-compose to compose the EAS and KAS services. Part of this process is putting them behind a reverse proxy.
During this process you will be generating keys for EAS, KAS, the reverse proxy, Certificate Authority (CA), and optionally client certificate.

_Note: This quick start guide is not intended to guide you on using pre-generated keys. Please see [Production]

```sh
./tools/genkeys-if-needed
. certs/.env
export {EAS,KAS{,_EC_SECP256R1}}_{CERTIFICATE,PRIVATE_KEY}
docker compose up -e EAS_CERTIFICATE,EAS_PRIVATE_KEY,KAS_CERTIFICATE,KAS_PRIVATE_KEY,KAS_EC_SECP256R1_CERTIFICATE,KAS_EC_SECP256R1_PRIVATE_KEY --build
```

> Note: OIDC-enabled deployments do not use the flows described below, or docker-compose - they're purely Helm/Minikube based and exclude deprecated services like EAS.
> Refer to the [OIDC Readme](README-keycloak-idp.md) for instructions on how to deploy Eternia with Keycloak and OIDC.

## Swagger-UI

KAS and EAS servers support Swagger UI to provide documentation and easier interaction for the REST API.  
Add "/ui" to the base URL of the appropriate server. For example, `http://127.0.0.1:4010/ui/`.
KAS and EAS each have separate REST APIs that together with the SDK support the full TDF3 process for encryption,
authorization, and decryption.

Swagger-UI can be disabled through the SWAGGER_UI environment variable. See the configuration sections of the
README documentation for [KAS](kas_app/README.md) and [EAS](eas/README.md) in this repository.

## Committing Code

Please use the autoformatters included in the tools directory. To get them
running in git as a pre-commit, use the following:

```sh
tools/black --install
tools/shfmt --install
```

These commands will autoformat python and bash scripts after you run 'git commit' but before
the commit is written to the tree. Then mail a PR and follow the advice on the PR template.

## Testing

### Unit Tests

Our unit tests use pytest, and should integrate with your favorite environment.
For continuous integration, we use `monotest`, which runs
all the unit tests in a python virtual environment.

To run all the unit tests in the repo:

``` shell
tools/monotest all
```

To run a subset of unit tests (e.g. just the `kas_core` tests from the [kas_core](kas_core) subfolder):

``` shell
tools/monotest kas_core
```

### Cluster tests

Our E2E cluster tests use [kuttl](https://kuttl.dev/docs/cli.html#setup-the-kuttl-kubectl-plugin), and you can run them
against an instance of Etheria deployed to a cluster (local minikube, or remote)

1. Install Etheria to a Kubernetes cluster (using the quickstart method above, for example)
1. Install [kuttl](https://kuttl.dev/docs/cli.html#setup-the-kuttl-kubectl-plugin)
1. From the repo root, run `kubectl kuttl test tests/cluster`
1. For advanced usage and more details, refer to [tests/cluster/README.md](tests/cluster/README.md)

> Etheria's CI is not currently cluster based, and so the kuttl tests are not being run via CI - this should be corrected when the CI is moved to K8S/Argo.

### Integration Tests

You can run a complete integration test locally using docker compose with the `docker-compose.ci.yml`, or with the `docker-compose.pki-ci.yml` to use the PKI keys you generated earlier. A helper script is available to run both sets of integration tests, `xtest/scripts/test-in-containers`.

To run a local integration test with the test harness running in
in the host machine, and not in a container, you may do the following:

```sh
docker-compose -f docker-compose.yml up --build
cd xtest
python3 test/runner.py -o Alice_1234 -s local --sdk sdk/py/oss/cli.sh
```

To test docker-compose using SDK and Python versions, create a .env

```dotenv
PY_OSS_VERSION===1.1.1
PY_SDK_VERSION=3.9
NODE_VERSION=14
```

### Security, Performance, and End-to-end Tests

```shell script
docker-compose --env-file certs/.env --file security-test/docker-compose.yml up --build --exit-code-from security-test security-test

docker-compose --env-file certs/.env --file performance-test/docker-compose.yml up --build --exit-code-from performance-test performance-test

docker-compose --env-file certs/.env --file e2e-test/docker-compose.yml up --build --exit-code-from e2e-test e2e-test
```

## Logs

In development Docker Compose runs in a attached state so logs can be seen from the terminal.

In a detached state logs can be accessed via [docker-compose logs](https://docs.docker.com/compose/reference/logs/)

Example:

```
> docker-compose logs kas
Attaching to kas
kas        | Some log here
```

## Deployment

TBD - Etheria deployment will be done to Kubernetes clusters via Helm chart.
TBD - for an idea of what's involved in this, including what Helm charts are required, [check the local install script](~/Source/etheria/deployments/local/start.sh)

### (Deprecated) Docker Compose Deployment

With Docker Compose deployment is [made easy with Docker Swarm](https://docs.docker.com/engine/swarm/stack-deploy/).

### (Deprecated) Configuration

Deployment configuration can be done through `docker-compose.yml` via the environment property.

#### Workers

The number of worker processes for handling requests.

A positive integer generally in the 2-4 x \$(NUM_CORES) range. You'll want to vary this a bit to find the best for your particular application's work load.

By default, the value of the WEB_CONCURRENCY environment variable. If it is not defined, the default is 1.

#### Threads

The number of worker threads for handling requests.

Run each worker with the specified number of threads.

A positive integer generally in the 2-4 x \$(NUM_CORES) range. You'll want to vary this a bit to find the best for your particular application's work load.

If it is not defined, the default is 1.

This setting only affects the Gthread worker type.

#### Profiling

https://gist.github.com/michaeltcoelho/c8bc65e5c3dce0f85312349353bf155a

https://docs.python.org/3/using/cmdline.html#environment-variables

### Advanced Manual setup

It's better to use one of the [above methods](#local-quickstart) for setup, but this explains the step by step details of how
the above methods work, and is included here for completeness.

#### Generate Keys

**WARNING: By generating new certs you will invalidate existing entity objects.**

##### Quick Start

To assist in quickly starting use the `./tools/genkeys-if-needed` to build all the keys. The hostname will be assigned `etheria.local`.
Make sure to add `127.0.0.1           etheria.local` to your `/etc/hosts` or `c:\windows\system32\drivers\etc\hosts`.

Additionally you can set a custom hostname `ETHERIA_HOSTNAME=myhost.com ./tools/genkeys-if-needed`, but you might have to update the docker-compose files.

_If you need to customization please see the Advanced Usage guide alongside the Genkey Tools._

1. Decide what your host name will be for the reverse proxy will be (e.g. example.com)
2. Generate reverse proxy certs `./tools/genkey-reverse-proxy $HOSTNAME_OF_REVERSE_PROXY`
3. Generate EAS & KAS certs `./tools/genkey-apps`
4. (Optional) Generate client certificates `./tools/genkey-client` for PKI support

##### Genkey Tools

Each genkey tools each have a brief help which you can access like

- `./tools/genkey-apps --help`
- `./tools/genkey-client --help`
- `./tools/genkey-reverse-proxy --help`

#### Start Services (non-PKI)

1. Update `docker-compose.yml` to use the reverse-proxy CN you defined above rather than `localhost`
1. Run:

```sh
. certs/.env
export {EAS,KAS{,_EC_SECP256R1}}_{CERTIFICATE,PRIVATE_KEY}
docker compose up -e EAS_CERTIFICATE,EAS_PRIVATE_KEY,KAS_CERTIFICATE,KAS_PRIVATE_KEY,KAS_EC_SECP256R1_CERTIFICATE,KAS_EC_SECP256R1_PRIVATE_KEY --build
```

_To learn more about [docker-compose see the manual](https://docs.docker.com/compose/reference/up/)._

#### Start Services in PKI mode

If you need support for PKI you can follow these steps.
There are a few requirements for starting in PKI mode:

1. Must create reverse proxy certificates with a CA
2. Must create a client certificate signed with CA
3. (Optional) Install CA and client certificate to OS keychain (_Please search the internet for instructions_)

Requirements (1) and (2) are described in [generate keys](#generate-keys) above.

`docker-compose -f docker-compose.pki.yml up --build`

## Production

_TBD_

## Abacus

To get Abacus up and running

1. Update `abacus.Dockerfile` with the location of the EAS URL `ENV NEXT_PUBLIC_EAS_API_URL https://etheria.local/eas/`
2. Build Docker image from root dir `docker build --file abacus.Dockerfile . --target server`
3. Run the image `docker run -d -p 8080:80 -e NEXT_TELEMETRY_DISABLED=1 <container_id>`

See [Abacus's README](abacus/README) for more info.

[^1]: https://docs.docker.com/compose/reference/logs/
