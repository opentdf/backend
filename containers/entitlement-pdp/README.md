# entitlement-pdp

Repo for Entitlement Policy Decision Point (PDP) service

What's an Entitlement PDP?

![ABAC System](./index.png)

## Modifying/Building/Publishing Entitlement Policy Logic

See [entitlement-policy](entitlement-policy/README.md) subfolder

### Entitlement PDP Rego entrypoint

The example Rego policy bundle in [entitlement-policy](entitlement-policy/README.md) emulates basic OpenTDF entitlement functionality.

However, the example Rego policy bundle can be replaced entirely without changing `entitlement-pdp` code itself,
as long as the following is also true of the Rego policy bundle it is replaced with:

1. The Rego policy bundle has a `opentdf.entitlement` package.
1. The `opentdf.entitlement` package has a rule named `generated_entitlements`
1. `generated_entitlements` evaluates to an array of objects in the following schema:

```json
[
    {
      "entity_identifier": "xxx",
      "entity_attributes": [
      {
        "attribute": "xx",
        "displayName": "xx"
      },
    }
]
```

### Where Rego policy bundles are stored

This service expects a valid [OPA config file](https://www.openpolicyagent.org/docs/latest/configuration/) to exist at the path pointed to by `OPA_CONFIG_PATH`. That config file will "tell" the OPA runtime embedded within this service where to load the policy bundle from.

The standard OPA approach is to store policy bundles remotely, e.g. in an OCI artifact registry (preferred), or e.g. S3, and regularly check the remote policy store for updated policy bundles.

Typically, a valid OPA config file will be mounted into this container at runtime. See the OPA config reference for the available options in the config file.

It is also possible to drop a policy `.tar.gz` bundle at a specific location in the local filesystem, and tell OPA via config
to use that locally cached policy bundle.

This requires disabling automatic policy bundle updates/fetches and is not suitable for normal deployments, but is handy for e.g. airgapped deployments. An example of an OPA config that supports this can be found in [offline-config-example](offline-config-example)

## REST API endpoints

See [OpenAPI definition](docs/swagger.json)

If service is running, it will also expose a live OpenAPI endpoint on `https://<service>:<port>/docs`

> NOTE: If you get an error about `not being able to fetch doc.json`, make sure you've set `EXTERNAL_HOST` to the hostname the service is exposed on (`localhost`, etc), or just manually type in the service host in the OpenAPI URL box.

## Environment variables

| Name                      | Default                           | Description                                                                                                                                                                                                           |
| ------------------------- | --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| LISTEN_PORT               | "3355"                            | Port the server will listen on                                                                                                                                                                                        |
| EXTERNAL_HOST             | ""                                | External endpoint the server will be accessed from (used for OpenAPI endpoint serving)                                                                                                                                |
| VERBOSE                   | "false"                           | Enable verbose/debug logging                                                                                                                                                                                          |
| DISABLE_TRACING           | "false"                           | Disable emitting OpenTelemetry traces (avoids junk timeouts if environment has no OT collector)                                                                                                                       |
| OPA_CONFIG_PATH           | "/etc/opa/config/opa-config.yaml" | Path to OPA config yaml - valid OPA config must exist here or service will not start. Normally this should be left alone                                                                                              |
| OPA_POLICYBUNDLE_PULLCRED | "YOURPATHERE"                     | If the OPA config used points to a policybundle stored in an OCI registry that requires credentials to fetch OCI artifacts, this should be set to a valid personal access token that has pull access to that registry |

## OCI container image

### Test

```sh
make test
```

### Build container image

```sh
make dockerbuild
```

### Publish container image

```sh
make dockerbuildpush
```

Published to `oci://ghcr.io/opentdf/entitlement-pdp`
