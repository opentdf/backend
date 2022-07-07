# Keycloak Entity Resolution Service

Resolves one or more entity identifiers using a provided attribute type  (email, username, etc,) to a keycloak user ID

The service uses the keycloak [Admin REST API](https://www.keycloak.org/docs-api/18.0/rest-api/index.html) to retrieve this information.

The service authenticates using an OIDC Client Credentials flow.  A keycloak client needs to be provisioned with:
- Access Type = confidential
- Service Account Enabled = On
- Service Account Roles -> Client Roles:
  -  realm-management -> manage-users
  
Environment Variables / Configuration:  
- KeycloakUrl: Base Url (host + port) to access keycloak
- KeycloakRealm: Keycloak Realm used for integration
- KeycloakClientId: OIDC Client ID used by Entity Resolution Service
- KeycloakClientSecret: OIDC Client Secret used by Entity Resolution Service
- LegacyKeycloak: Is "/auth" in the Url path for Keycloak.  e.g. Keycloak 17+ /auth is not in the url path by default. Defaults to False, see [gocloak bug](https://github.com/Nerzal/gocloak/issues/346) for reference/context.
- ListenPort: Service listen port, default = 7070
- ExternalHost 
- Verbose : Verbose logging; false/true
- DisableTracing: Disable telemetry tracing

## API
See [Swagger Docs](./docs/swagger.yaml)  
