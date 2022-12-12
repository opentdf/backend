# entitlement-store

![Version: 0.0.1](https://img.shields.io/badge/Version-0.0.1-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: main](https://img.shields.io/badge/AppVersion-main-informational?style=flat-square)

A read-only service that fetches and returns any entity<->attribute mappings present in the data store

## Maintainers

| Name | Email | Url |
| ---- | ------ | --- |
| Virtru |  |  |

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| affinity | object | `{}` |  |
| autoscaling.enabled | bool | `false` |  |
| autoscaling.maxReplicas | int | `100` |  |
| autoscaling.minReplicas | int | `1` |  |
| autoscaling.targetCPUUtilizationPercentage | int | `80` |  |
| fullnameOverride | string | `""` | The fully qualified appname override |
| global | object | `{"opentdf":{"common":{"imagePullSecrets":[],"oidcExternalBaseUrl":"http://localhost:65432","oidcInternalBaseUrl":"http://keycloak-http","oidcUrlPath":"auth","postgres":{"database":"tdf_database","host":"postgresql","port":5432}}}}` | Global values that may be overridden by a parent chart. |
| global.opentdf.common.imagePullSecrets | list | `[]` | JSON passed to the deployment's template.spec.imagePullSecrets |
| global.opentdf.common.oidcExternalBaseUrl | string | `"http://localhost:65432"` | Base external k8s url of OIDC provider |
| global.opentdf.common.oidcInternalBaseUrl | string | `"http://keycloak-http"` | Base internal k8s url of OIDC provider |
| global.opentdf.common.oidcUrlPath | string | `"auth"` | Optional path added to base OIDC url |
| global.opentdf.common.postgres.database | string | `"tdf_database"` | The database name within the given server |
| global.opentdf.common.postgres.host | string | `"postgresql"` | postgres server's k8s name or global DNS for external server |
| global.opentdf.common.postgres.port | int | `5432` | postgres server port |
| image | object | `{"pullPolicy":"IfNotPresent","repo":"ghcr.io/opentdf/entitlement_store","tag":null}` | Configure the container image to use in the deployment. |
| image.pullPolicy | string | `"IfNotPresent"` | The container's `imagePullPolicy` |
| image.repo | string | `"ghcr.io/opentdf/entitlement_store"` | The image selector, also called the 'image name' in k8s documentation and 'image repository' in docker's guides. |
| image.tag | string | `nil` | Chart.AppVersion will be used for image tag, override here if needed |
| imagePullSecrets | string | `nil` | JSON passed to the deployment's template.spec.imagePullSecrets. Overrides global.opentdf.common.imagePullSecrets |
| ingress | object | `{"annotations":{},"className":null,"enabled":false,"hosts":{},"tls":null}` | Ingress configuration. To configure, set enabled to true and set `hosts` to a map in the form:      [hostname]:       [path]:         pathType:    your-pathtype [default: "ImplementationSpecific"]         serviceName: your-service  [default: service.fullname]         servicePort: service-port  [default: service.port above] |
| logLevel | string | `"INFO"` | Sets the default loglevel for the application. One of the valid python logging levels: `DEBUG, INFO, WARNING, ERROR, CRITICAL` |
| nameOverride | string | `""` | Select a specific name for the resource, instead of the default, entitlement-store |
| nodeSelector | object | `{}` |  |
| oidc.clientId | string | `"tdf-attributes"` |  |
| oidc.externalHost | string | `nil` | Override for global.opentdf.common.oidcExternalBaseUrl & url path |
| oidc.internalHost | string | `nil` | Override for global.opentdf.common.oidcInternalBaseUrl & url path |
| oidc.realm | string | `"tdf"` |  |
| oidc.scopes | string | `"email"` |  |
| openapiUrl | string | `""` | Set to enable openapi endpoint |
| podAnnotations | object | `{}` | Values for the deployment spec.template.metadata.annotations field |
| podSecurityContext | object | `{}` | Values for deployment's spec.template.spec.securityContext |
| postgres | object | `{"database":null,"host":null,"port":null,"schema":"tdf_entitlement","user":"tdf_entitlement_reader"}` | Configuration for the database backend |
| postgres.database | string | `nil` | Override for global.opentdf.common.postgres.database |
| postgres.host | string | `nil` | Override for global.opentdf.common.postgres.host |
| postgres.port | string | `nil` | Override for global.opentdf.common.postgres.post |
| postgres.schema | string | `"tdf_entitlement"` | The entitlement schema |
| postgres.user | string | `"tdf_entitlement_reader"` | Must be a postgres user with tdf_entitlement_reader role |
| replicaCount | int | `1` | Sets the default number of pod replicas in the deployment. Ignored if autoscaling.enabled == true |
| resources | object | `{}` | Specify required limits for deploying this service to a pod. We usually recommend not to specify default resources and to leave this as a conscious choice for the user. This also increases chances charts run on environments with little resources, such as Minikube. |
| secretRef | string | `"name: {{ template \"entitlement-store.fullname\" . }}-secret"` | JSON to locate a k8s secret containing environment variables. Notably, this file should include the following environemnt variable definitions:     POSTGRES_PASSWORD: Password corresponding to postgres.user below     KAS_CERTIFICATE: Public key for Key Access service     KAS_EC_SECP256R1_CERTIFICATE: Public key (EC Mode) for Key Access service |
| securityContext | object | `{}` | Values for deployment's spec.template.spec.containers.securityContext |
| serverCorsOrigins | string | `""` | Allowed origins for CORS |
| serverPublicName | string | `"entitlement-store"` | Name of application. Used during oauth flows, for example when connecting to the OpenAPI endpoint with an OAuth authentication |
| serverRootPath | string | `"/"` | Base path for this service. Allows serving multiple REST services from the same origin, e.g. using an ingress with prefix mapping as suggested below. |
| service | object | `{"port":5000,"type":"ClusterIP"}` | Service configuation information. |
| service.port | int | `5000` | Port to assign to the `http` port |
| service.type | string | `"ClusterIP"` | Service `spec.type` |
| serviceAccount | object | `{"annotations":{},"create":true,"name":null}` | A service account to create |
| serviceAccount.annotations | object | `{}` | Annotations to add to the service account |
| serviceAccount.create | bool | `true` | Specifies whether a service account should be created |
| serviceAccount.name | string | `nil` | The name of the service account to use. If not set and create is true, a name is generated using the fullname template |
| tolerations | list | `[]` |  |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.11.0](https://github.com/norwoodj/helm-docs/releases/v1.11.0)
