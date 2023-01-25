# entity-resolution

![Version: 0.0.1](https://img.shields.io/badge/Version-0.0.1-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: main](https://img.shields.io/badge/AppVersion-main-informational?style=flat-square)

Resolves external entity identifiers to OpenTDF entity identifiers

## Maintainers

| Name   | Email | Url |
| ------ | ----- | --- |
| OpenTDF | support@opentdf.io | opentdf.io |

## Values

| Key                                       | Type   | Default                                   | Description                                                                                                            |
| ----------------------------------------- | ------ | ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| config.disableTracing                     | string | `"false"`                                 | Disable emitting OpenTelemetry traces (avoids junk timeouts if environment has no OT collector)                        |
| config.externalHost                       | string | `""`                                      | External endpoint the server will be accessed from (used for OpenAPI endpoint serving)                                 |
| config.keycloak.clientId                  | string | `"tdf-entity-resolution-service"`         | OIDC Client ID used by Entity Resolution Service                                                                       |
| config.keycloak.legacy                    | bool   | `false`                                   | Using a legacy keycloak version. See https://github.com/Nerzal/gocloak/issues/346                                      |
| config.keycloak.realm                     | string | `"tdf"`                                   | Keycloak Realm used for integration                                                                                    |
| config.keycloak.url                       | string | `nil`                                     | Override for `global.opentdf.common.oidcInternalBaseUrl`                                                               |
| config.listenPort                         | int    | `7070`                                    | Port the server will listen on                                                                                         |
| config.otlpCollectorEndpoint              | string | `"opentelemetry-collector.otel.svc:4317"` | Open telemetry collector endpoint                                                                                      |
| config.verbose                            | string | `"false"`                                 | Enable verbose logging                                                                                                 |
| createKeycloakClientSecret                | bool   | `true`                                    | Create a secret for the ERS clientSecret                                                                               |
| fullnameOverride                          | string | `""`                                      | Optionally override the fully qualified name                                                                           |
| global.opentdf.common.imagePullSecrets    | list   | `[]`                                      | JSON passed to the deployment's `template.spec.imagePullSecrets`                                                       |
| global.opentdf.common.oidcInternalBaseUrl | string | `"http://keycloak-http"`                  | Base internal url of OIDC provider                                                                                     |
| image.pullPolicy                          | string | `"IfNotPresent"`                          | The container's `imagePullPolicy`                                                                                      |
| image.repo                                | string | `"ghcr.io/opentdf/entity-resolution"`     | The image selector, also called the 'image name' in k8s documentation and 'image repository' in docker's guides.       |
| image.tag                                 | string | `nil`                                     | `Chart.AppVersion` will be used for image tag, override here if needed                                                 |
| imagePullSecrets                          | string | `nil`                                     | JSON passed to the deployment's `template.spec.imagePullSecrets`. Overrides `global.opentdf.common.imagePullSecrets`   |
| nameOverride                              | string | `""`                                      | Optionally override the name                                                                                           |
| replicaCount                              | int    | `1`                                       | Sets the default number of pod replicas in the deployment. Ignored if `autoscaling.enabled` == true                    |
| secret.keycloak.clientSecret              | string | `"REPLACE_AT_INSTALL_TIME"`               | OIDC Client Secret used by Entity Resolution Service                                                                   |
| serviceAccount.annotations                | object | `{}`                                      | Annotations to add to the service account                                                                              |
| serviceAccount.create                     | bool   | `true`                                    | Specifies whether a service account should be created                                                                  |
| serviceAccount.name                       | string | `""`                                      | The name of the service account to use. If not set and create is true, a name is generated using the fullname template |

---

Autogenerated from chart metadata using [helm-docs v1.11.0](https://github.com/norwoodj/helm-docs/releases/v1.11.0)
