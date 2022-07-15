# Entity Resolution Service

Resolves a query against one or more entity identifiers using a provided attribute type (email, username, etc,) to user information obtained from a remote entity store.

Currently, the only remote entity store supported is Keycloak.

## Keycloak Setup

The Keycloak implementation uses the Keycloak [Admin REST API](https://www.keycloak.org/docs-api/18.0/rest-api/index.html) to retrieve this information.

The service must authenticate with Keycloak using an OIDC Client Credentials flow, using a client that has explicitly been granted permissions to query the Keycloak user store.  

To grant an existing Keycloak client the permissions to query the Keycloak user store, provision it with the following:

- Access Type = confidential
- Service Account Enabled = On
- Service Account Roles -> Client Roles:
  - realm-management -> query-users
  - realm-management -> view-users
  - realm-management -> query-clients
  - realm-management -> view-clients
  
## Environment variables

| Name | Default | Description |
| ---- | ------- | ----------- |
| LISTEN_PORT | "7070" | Port the server will listen on |
| EXTERNAL_HOST | "" | External endpoint the server will be accessed from (used for OpenAPI endpoint serving) |
| VERBOSE | "false" | Enable verbose/debug logging |
| DISABLE_TRACING | "false" | Disable emitting OpenTelemetry traces (avoids junk timeouts if environment has no OT collector) |
| KEYCLOAK_URL | "http://localhost:8080" | Base URL (host + port) to access Keycloak |
| KEYCLOAK_REALM | "tdf" | Keycloak Realm used for integration |
| KEYCLOAK_CLIENT_ID | "tdf-entity-resolution-service" | OIDC Client ID used by Entity Resolution Service |
| KEYCLOAK_CLIENT_SECRET | "" | OIDC Client Secret used by Entity Resolution Service |
| LEGACY_KEYCLOAK | "false" | Is "/auth" in the Url path for Keycloak.  e.g. Keycloak 17+ /auth is not in the url path by default. Defaults to False, see [gocloak bug](https://github.com/Nerzal/gocloak/issues/346) for reference/context. |

## API

See [Swagger Docs](./docs/swagger.yaml)

If service is running, it will also expose a live OpenAPI endpoint on `https://<service>:<port>/docs`

> NOTE: If you get an error about `not being able to fetch doc.json`, make sure you've set `EXTERNAL_HOST` to the hostname the service is exposed on (`localhost`, etc), or just manually type in the service host in the OpenAPI URL box.

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

Published to `oci://ghcr.io/opentdf/entity-resolution`
