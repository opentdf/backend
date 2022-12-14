# kas

![Version: 0.0.1](https://img.shields.io/badge/Version-0.0.1-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: main](https://img.shields.io/badge/AppVersion-main-informational?style=flat-square)

TDF key access control service

## Maintainers

| Name | Email | Url |
| ---- | ------ | --- |
| Virtru |  |  |

## Kas's Keys

KAS needs at least 4 keys (2 pairs, one RSA and one EC pair) to run.

These keys are important, as they are the "keys to the kingdom", so to speak - possessing them might allow data access by unauthorized parties.

Also, if the keys change, TDF files created with the previous set will no longer be decryptable.

Therefore, it is strongly recommended that these keys be generated and managed properly in a production environment.

1. Install Chart (will generate throwaway non-production KAS keys if none provided at install time, not recommended or supported for production):

```sh
helm upgrade --install kas .
```

If you wish to provide and manage your own KAS keys (recommended), you may do so by either:

2. Creating/managing your own named K8S Secret in the chart namespace in the form described by [](./templates/secrets.yaml), and setting `kas.externalEnvSecretName` accordingly:
``` sh
helm upgrade --install kas --set externalEnvSecretName=<Secret-with-rsa-and-ec-keypairs> .
```

3. Supplying each private/public key as a values override, e.g:

``` sh
helm upgrade --install kas \
  --set envConfig.attrAuthorityCert=$ATTR_AUTHORITY_CERTIFICATE \
  --set envConfig.ecCert=$KAS_EC_SECP256R1_CERTIFICATE \
  --set envConfig.cert=$KAS_CERTIFICATE \
  --set envConfig.ecPrivKey=$KAS_EC_SECP256R1_PRIVATE_KEY \
  --set envConfig.privKey=$KAS_PRIVATE_KEY .
```

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| SWAGGER_UI | string | `"True"` | To enable swagger ui |
| affinity | object | `{}` | Pod scheduling preferences |
| autoscaling.enabled | bool | `false` | Enables autoscaling. When set to `true`, `replicas` is no longer applied. |
| autoscaling.maxReplicas | int | `100` | Sets maximum replicas for autoscaling. |
| autoscaling.minReplicas | int | `1` | Sets minimum replicas for autoscaling. |
| autoscaling.targetCPUUtilizationPercentage | int | `80` | Target average CPU usage across all the pods |
| certFileSecretName | string | `nil` | Secret containing an additional ca-cert.pem file for locally signed TLS certs. Used for a private PKI mode, for example. |
| endpoints.attrHost | string | `"http://attributes:4020"` | Internal url of attributes service |
| endpoints.oidcPubkeyEndpoint | string | `nil` | Local override for `global.opentdf.common.oidcInternalBaseUrl` + path |
| endpoints.statsdHost | string | `"statsd"` | Internal url of statsd |
| envConfig.attrAuthorityCert | string | `nil` | The public key used to validate responses from `attrHost` |
| envConfig.cert | string | `nil` | Public key KAS clients can use to validate responses |
| envConfig.ecCert | string | `nil` | The public key of curve secp256r1, KAS clients can use to validate responses |
| envConfig.ecPrivKey | string | `nil` | Private key of curve secp256r1, KAS uses to certify responses |
| envConfig.privKey | string | `nil` | Private key KAS uses to certify responses |
| externalEnvSecretName | string | `nil` | The name of a secret containing required config values (see `envConfig` below); overrides `envConfig` |
| extraEnvSecretName | string | `nil` | Secret containing additional env variables in addition to those provided by `envConfig` or `externalSecretName` |
| flaskDebug | string | `"False"` | If the debug mode should  be enabled in flask |
| fullnameOverride | string | `""` | The fully qualified appname override |
| global.opentdf.common.imagePullSecrets | list | `[]` | JSON passed to the deployment's `template.spec.imagePullSecrets` |
| global.opentdf.common.oidcInternalBaseUrl | string | `"http://keycloak-http"` | Base internal url of OIDC provider |
| image.pullPolicy | string | `"IfNotPresent"` | The container's `imagePullPolicy` |
| image.repo | string | `"ghcr.io/opentdf/kas"` | The image selector, also called the 'image name' in k8s documentation and 'image repository' in docker's guides. |
| image.tag | string | `nil` | `Chart.AppVersion` will be used for image tag, override here if needed |
| imagePullSecrets | string | `nil` | JSON passed to the deployment's `template.spec.imagePullSecrets`. Overrides `global.opentdf.common.imagePullSecrets` |
| ingress.annotations | object | `{}` | Ingress annotations |
| ingress.className | string | `nil` | Ingress class to use. |
| ingress.enabled | bool | `false` | Enables the Ingress |
| ingress.hosts | object | `{}` | Map in the form: [hostname]:   [path]:     pathType:    your-pathtype [default: "ImplementationSpecific"]     serviceName: your-service  [default: `service.fullname`]     servicePort: service-port  [default: `service.port` above] |
| ingress.tls | string | `nil` | Ingress TLS configuration |
| jsonLogger | string | `"true"` | Determinies whether KAS uses the json formatter for logging, if `false` the dev formatter is used. Default is `true` |
| livenessProbe | object | `{"httpGet":{"path":"/healthz?probe=liveness","port":"http"}}` | Adds a container `livenessProbe`, if set. |
| logLevel | string | `"INFO"` | Sets the default loglevel for the application. One of the valid python logging levels: `DEBUG, INFO, WARNING, ERROR, CRITICAL` |
| maxUnavailable | int | `1` | Pod disruption budget |
| nameOverride | string | `""` | Select a specific name for the resource, instead of the default, kas |
| nodeSelector | object | `{}` | Node labels for pod assignment |
| openapiUrl | string | `""` | Set to enable openapi endpoint |
| pdp.disableTracing | string | `"true"` | KAS's internal Access PDP can send OpenTelemetry traces to collectors - if no collectors configured, the traces will get redirected to STDOUT, which is a bit spammy, so turn this off until we do proper OT trace collection everywhere. |
| pdp.verbose | string | `"false"` | Enables verbose mode for the internal PDP (policy decision point) KAS uses. If `true`, decisions will be logged with much additional detail |
| podAnnotations | object | `{}` | Values for the deployment `spec.template.metadata.annotations` field |
| podSecurityContext | object | `{}` | Values for deployment's `spec.template.spec.securityContext` |
| readinessProbe | object | `{"httpGet":{"path":"/healthz?probe=readiness","port":"http"}}` | Adds a container `readinessProbe`, if set. |
| replicaCount | int | `1` | Sets the default number of pod replicas in the deployment. Ignored if `autoscaling.enabled` == true |
| resources | object | `{}` | Specify required limits for deploying this service to a pod. We usually recommend not to specify default resources and to leave this as a conscious choice for the user. This also increases chances charts run on environments with little resources, such as Minikube. |
| securityContext | object | `{}` | Values for deployment's `spec.template.spec.containers.securityContext` |
| serverRootPath | string | `"/"` | Base path for this service. Allows serving multiple REST services from the same origin, e.g. using an ingress with prefix mapping as suggested below. |
| service.port | int | `8000` | Port to assign to the `http` port |
| service.type | string | `"ClusterIP"` | Service `spec.type` |
| serviceAccount.annotations | object | `{}` | Annotations to add to the service account |
| serviceAccount.create | bool | `true` | Specifies whether a service account should be created |
| serviceAccount.name | string | `nil` | The name of the service account to use. If not set and create is true, a name is generated using the fullname template |
| tolerations | list | `[]` | Tolerations for nodes that have taints on them |

