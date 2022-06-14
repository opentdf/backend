# entitlement-pdp
Repo for Entitlement Policy Decision Point (PDP) service

What's an Entitlement PDP?

![ABAC System](./index.png)

## Modifying/Building/Publishing Entitlement Policy Logic

See [entitlement-policy](entitlement-policy/README.md) subfolder

## REST API endpoints

See [OpenAPI definition](docs/swagger.json)

If service is running, it will also expose a live OpenAPI endpoint on `https://<service>:<port>/docs`

> NOTE: If you get an error about `not being able to fetch doc.json`, make sure you've set `EXTERNAL_HOST` to the hostname the service is exposed on (`localhost`, etc), or just manually type in the service host in the OpenAPI URL box.

## Environment variables

| Name | Default | Description |
| ---- | ------- | ----------- |
| LISTEN_PORT | "3355" | Port the server will listen on |
| EXTERNAL_HOST | "" | External endpoint the server will be accessed from (used for OpenAPI endpoint serving) |
| VERBOSE | "false" | Enable verbose/debug logging |
| DISABLE_TRACING | "false" | Disable emitting OpenTelemetry traces (avoids junk timeouts if environment has no OT collector) |
| OPA_CONFIG_PATH | "/etc/opa/config/opa-config.yaml" | Path to OPA config yaml - valid OPA config must exist here or service will not start. Normally this should be left alone |
| OPA_POLICYBUNDLE_PULLCRED | "YOURPATHERE" | If the OPA config used points to a policybundle stored in an OCI registry that requires credentials to fetch OCI artifacts, this should be set to a valid personal access token that has pull access to that registry |

## OCI container image

### Test

``` sh
make test
```

### Build container image

``` sh
make dockerbuild
```

### Publish container image

``` sh
make dockerbuildpush
```

Published to `oci://ghcr.io/opentdf/entitlement-pdp`
