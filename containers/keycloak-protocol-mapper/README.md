# Keycloak Identity Provider (IdP)

Keycloak is our Identity Provider (IdP) software.

We build a custom image off of the Bitnami [Keycloak image](https://github.com/bitnami/bitnami-docker-keycloak) and [Keycloak Helm chart](https://github.com/bitnami/charts/tree/master/bitnami/keycloak)

The custom image simply contains a custom openTDF claims mapper JAR file, copied into a folder in the Keycloak image.

We can stop building a custom Bitnami image if we PR a fix to their repo to build both `arm64` and `amd64` images,
their tooling supports this and they are doing it for other images, they just aren't doing it for the Keycloak image yet.

## Build and Setup

All build steps are scripted via [`Makefile`](Makefile)
Docker image names and version tags are set in [`Makefile`](Makefile).

`
### Build The openTDF Keycloak On Top Of The Bitnami Base Container Locally

```sh
make dockerbuild
```

### Build The openTDF Keycloak On Top Of The Bitnami Base Container Locally, Push To Remote Repo

```sh
make dockerbuildpush
```

### Build and publish the Bitnami base image (only required for Keycloak version changes)
> Note that the Bitnami base image `virtru/keycloak-base` should not ever need to be built or published
> unless we change Keycloak versions, and we can drop it entirely if we make a PR to [Keycloak image](https://github.com/bitnami/bitnami-docker-keycloak) enabling an `arm64` image build in upstream 

``` sh
make bitnami-base-buildpush
```

## For people working on the repo

There are 3 special bits in this repo you need to care about:

1. Keycloak (we use the upstream container but pack in a custom JAR file)
1. A custom openTDF JAR extension for Keycloak that makes webservice calls, and is invoked by Keycloak during auth flows (see [custom-mapper](custom-mapper)).
1. A Custom Claim entitlement provider webservice that supplies entity entitlements, which the openTDF JAR calls (see [entitlements](../entitlements)).

### Custom Claims Mapper Jar

See [custom-mapper](custom-mapper)

### Examples of advanced OIDC/Keycloak flows

See [EXAMPLES.md](EXAMPLES.md)
