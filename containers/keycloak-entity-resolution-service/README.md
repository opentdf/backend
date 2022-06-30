# Keycloak Entity Resolution Service

Resolves one or more entity identifiers using a provided attribute type  (email, username, etc,) to a keycloak user ID

The service uses the keycloak [Admin REST API](https://www.keycloak.org/docs-api/18.0/rest-api/index.html) to retrieve this information.

The service authenticates using an OIDC Client Credentials flow.  A keycloak client needs to be provisioned with:
- Access Type = confidential
- Service Account Enabled = On
- Service Account Roles -> Client Roles:
  -  realm-management -> manage-users

## API
See [Swagger Docs](./docs/swagger.yaml)  