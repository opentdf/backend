# Keycloak Protocol Mapper

The OpenTDF example backend uses Keycloak as our reference Identity Provider (IdP) software.

We build a custom image off of the upstream [Keycloak image](https://github.com/keycloak/keycloak-containers) and [Keycloak Helm chart](https://codecentric.github.io/helm-charts) - it is identical to the upstream image, just built for both `arm64` and `amd64` - upstream currently just builds for `amd64`, and includes a custom protocol mapper extension.

## Build and Setup

All build steps are scripted via [`Makefile`](Makefile)
Docker image names and version tags are set in [`Makefile`](Makefile).

### Build The OpenTDF Keycloak On Top Of The Keycloak Base Container Locally

```sh
make dockerbuild
```

### Build The OpenTDF Keycloak On Top Of The Keycloak Base Container Locally, Push To Remote Repo

```sh
make dockerbuildpush
```

### Build and publish the Keycloak base image (only required for Keycloak version changes)

> Note that the base image `opentdf/keycloak-multiarch-base` is unchanged from the upstream Keycloak image, and
> should not ever need to be built or published unless we change Keycloak versions,
> and we can drop it entirely if we make a PR to [Keycloak image](https://github.com/keycloak/keycloak-containers)
> enabling an `arm64` image build in upstream in the same manner we do here.

```sh
make keycloak-base-buildpush
```

## For people working on the repo

There are 3 special bits in this repo you need to care about:

1. Keycloak (we use the upstream container but pack in a custom JAR file)
1. A custom OpenTDF JAR extension for Keycloak that makes webservice calls, and is invoked by Keycloak during auth flows (see [custom-mapper](custom-mapper)).
1. A Custom Claim entitlement provider webservice that supplies entity entitlements, which the OpenTDF JAR calls (see [entitlements](../entitlements)).

### Custom Claims Mapper Jar

See [custom-mapper](custom-mapper)

### Examples of advanced OIDC/Keycloak flows

See [EXAMPLES.md](EXAMPLES.md)
