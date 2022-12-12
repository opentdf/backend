# backend

![Version: 0.0.1](https://img.shields.io/badge/Version-0.0.1-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: main](https://img.shields.io/badge/AppVersion-main-informational?style=flat-square)

Minimal deployment of OpenTDF backend services

## Maintainers

| Name | Email | Url |
| ---- | ------ | --- |
| Virtru |  |  |

## Deploy Chart

1. Create Cluster: `ctlptl create cluster kind --registry=ctlptl-registry --name kind-opentdf`
1. Update Dependencies: `helm dependency update`
1. Install Chart (will generate non-production KAS keys if none provided):

```sh
helm upgrade --install backend -f testing/deployment.yaml .
```

If you wish to provide and manage your own KAS keys (recommended), you may do so by either:

1. Creating/managing your own named K8S Secret in the chart namespace in the form described by [](./templates/secrets.yaml), and setting `kas.externalEnvSecretName` accordingly:
``` sh
helm upgrade --install backend -f testing/deployment.yaml \
  --set kas.externalEnvSecretName=<Secret-with-rsa-and-ec-keypairs> .
```

1. Supplying each private/public key as a values override, e.g:

``` sh
helm upgrade --install backend -f testing/deployment.yaml \
  --set kas.envConfig.attrAuthorityCert=$ATTR_AUTHORITY_CERTIFICATE \
  --set kas.envConfig.ecCert=$KAS_EC_SECP256R1_CERTIFICATE \
  --set kas.envConfig.cert=$KAS_CERTIFICATE \
  --set kas.envConfig.ecPrivKey=$KAS_EC_SECP256R1_PRIVATE_KEY \
  --set kas.envConfig.privKey=$KAS_PRIVATE_KEY .
```

## Cluster Status
  To check to see if your cluster is running, enter the following command:
  `kubectl get pods`

## Setting Up An Ingress (Optional)
```
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx

helm install nginx-ingress-controller ingress-nginx/ingress-nginx --version 4.2.1 --set controller.config.large-client-header-buffers="20 32k"

helm upgrade --install backend -f values.yaml -f testing/deployment.yaml \
-f testing/ingress.yaml \
--set kas.envConfig.attrAuthorityCert=$ATTR_AUTHORITY_CERTIFICATE \
--set kas.envConfig.ecCert=$KAS_EC_SECP256R1_CERTIFICATE \
--set kas.envConfig.cert=$KAS_CERTIFICATE \
--set kas.envConfig.ecPrivKey=$KAS_EC_SECP256R1_PRIVATE_KEY \
--set kas.envConfig.privKey=$KAS_PRIVATE_KEY .

kubectl port-forward service/nginx-ingress-controller-ingress-nginx-controller 65432:80
```

## Cleanup
1. Uninstall Chart: `helm uninstall backend`
2. Uninstall Ingress (if used): `helm uninstall nginx-ingress-controller`
3. Delete Cluster: `ctlptl delete cluster kind-opentdf`

## Requirements

| Repository | Name | Version |
|------------|------|---------|
| file://../attributes | attributes | 0.0.1 |
| file://../entitlement-pdp | entitlement-pdp | 0.0.10 |
| file://../entitlement-store | entitlement-store | 0.0.1 |
| file://../entitlements | entitlements | 0.0.1 |
| file://../entity-resolution | entity-resolution | 0.0.1 |
| file://../kas | kas | 0.0.1 |
| file://../keycloak-bootstrap | keycloak-bootstrap | 0.4.4 |
| https://charts.bitnami.com/bitnami | postgresql | 10.16.2 |
| https://codecentric.github.io/helm-charts | keycloak(keycloakx) | 1.6.1 |

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| global | object | `{"opentdf":{"common":{"imagePullSecrets":[],"oidcExternalBaseUrl":"http://localhost:65432","oidcInternalBaseUrl":"http://keycloak-http","oidcUrlPath":"auth","postgres":{"database":"tdf_database","host":"postgresql","port":5432}}}}` | Global values that may be overridden by a parent chart. |
| global.opentdf.common.imagePullSecrets | list | `[]` | Any existing image pull secrets subcharts should use e.g. imagePullSecrets:   - name: my-existing-ghcr-pullsecret   - name: my-other-pullsecret |
| global.opentdf.common.keycloak.password | string | `"mykeycloakpassword"` | The Keycloak admin password |
| global.opentdf.common.keycloak.user | string | `"keycloakadmin"` | The Keycloak admin username |
| global.opentdf.common.oidcExternalBaseUrl | string | `"http://localhost:65432"` | The external scheme + hostname to keycloak endpoint, oidcUrlPrefix used in constructing end urls. |
| global.opentdf.common.oidcInternalBaseUrl | string | `"http://keycloak-http"` | The cluster internal scheme + hostname for keycloak endpoint, oidcUrlPrefix used in constructing end urls. |
| global.opentdf.common.oidcUrlPath | string | `"auth"` | The url path (no preceding / ) to keycloak |
| global.opentdf.common.postgres.database | string | `"tdf_database"` | The database name within the given server |
| global.opentdf.common.postgres.host | string | `"postgresql"` | postgres server's k8s name or global DNS for external server |
| global.opentdf.common.postgres.port | int | `5432` | postgres server port |
| attributes.fullnameOverride | string | `"attributes"` | Optionally override the name |
| attributes.ingress.annotations."nginx.ingress.kubernetes.io/rewrite-target" | string | `"/$2"` |  |
| attributes.ingress.className | string | `"nginx"` |  |
| attributes.ingress.enabled | bool | `false` |  |
| attributes.ingress.hosts."host.docker.internal"."/api/attributes(/|$)(.*)".pathType | string | `"Prefix"` |  |
| attributes.ingress.hosts."opentdf.local"."/api/attributes(/|$)(.*)".pathType | string | `"Prefix"` |  |
| attributes.ingress.hosts.."/api/attributes(/|$)(.*)".pathType | string | `"Prefix"` |  |
| attributes.ingress.hosts.localhost."/api/attributes(/|$)(.*)".pathType | string | `"Prefix"` |  |
| attributes.logLevel | string | `"DEBUG"` | What log level to output |
| attributes.secretRef | string | `"name: \"{{ template \"attributes.fullname\" . }}-otdf-secret\""` |  |
| bootstrapKeycloak | bool | `true` |  |
| embedded.keycloak | bool | `true` | Whether to use an embedded keycloak |
| embedded.postgresql | bool | `true` | Whether to use an embedded postgres |
| entitlement-pdp.config.disableTracing | bool | `true` | Disable the open telemetry tracing |
| entitlement-pdp.fullnameOverride | string | `"entitlement-pdp"` | Optionally override the name |
| entitlement-pdp.opaConfig.policy.useStaticPolicy | bool | `true` | If `useStaticPolicy` is set to `true`, then an OPA config will be generated that forces the use of a policy bundle that was built and packed into the `entitlement-pdp` container at *build* time, and no policy bundle will be fetched dynamically from the registry on startup. This is not a desirable default, but it is useful in offline deployments. `Tilt` tries make docker image caching automagic, but it isn't particularly smart about non-Docker OCI caches, so tell the PDP chart to use the default on-disk policy bundle we create and pack into the image to work around this |
| entitlement-pdp.secretRef | string | `"name: \"{{ template \"entitlement-pdp.fullname\" . }}-otdf-secret\""` |  |
| entitlement-store.fullnameOverride | string | `"entitlement-store"` | Optionally override the name |
| entitlement-store.ingress.annotations."nginx.ingress.kubernetes.io/rewrite-target" | string | `"/$2"` |  |
| entitlement-store.ingress.className | string | `"nginx"` |  |
| entitlement-store.ingress.enabled | bool | `false` |  |
| entitlement-store.ingress.hosts."host.docker.internal"."/api/entitlement-store(/|$)(.*)".pathType | string | `"Prefix"` |  |
| entitlement-store.ingress.hosts."opentdf.local"."/api/entitlement-store(/|$)(.*)".pathType | string | `"Prefix"` |  |
| entitlement-store.ingress.hosts.."/api/entitlement-store(/|$)(.*)".pathType | string | `"Prefix"` |  |
| entitlement-store.ingress.hosts.localhost."/api/entitlement-store(/|$)(.*)".pathType | string | `"Prefix"` |  |
| entitlement-store.secretRef | string | `"name: \"{{ template \"entitlement-store.fullname\" . }}-otdf-secret\""` |  |
| entitlements.fullnameOverride | string | `"entitlements"` | Optionally override the name |
| entitlements.ingress.annotations."nginx.ingress.kubernetes.io/rewrite-target" | string | `"/$2"` |  |
| entitlements.ingress.className | string | `"nginx"` |  |
| entitlements.ingress.enabled | bool | `false` |  |
| entitlements.ingress.hosts."host.docker.internal"."/api/entitlements(/|$)(.*)".pathType | string | `"Prefix"` |  |
| entitlements.ingress.hosts."opentdf.local"."/api/entitlements(/|$)(.*)".pathType | string | `"Prefix"` |  |
| entitlements.ingress.hosts.."/api/entitlements(/|$)(.*)".pathType | string | `"Prefix"` |  |
| entitlements.ingress.hosts.localhost."/api/entitlements(/|$)(.*)".pathType | string | `"Prefix"` |  |
| entitlements.secretRef | string | `"name: \"{{ template \"entitlements.fullname\" . }}-otdf-secret\""` |  |
| entity-resolution.config.keycloak.legacy | bool | `true` |  |
| entity-resolution.fullnameOverride | string | `"entity-resolution"` | Optionally override the name |
| fullnameOverride | string | `""` | Optionally override the fully qualified name |
| kas.endpoints.attrHost | string | `"http://attributes:4020"` |  |
| kas.endpoints.statsdHost | string | `"statsd"` |  |
| kas.envConfig.attrAuthorityCert | string | `nil` |  |
| kas.envConfig.cert | string | `nil` |  |
| kas.envConfig.ecCert | string | `nil` |  |
| kas.envConfig.ecPrivKey | string | `nil` |  |
| kas.envConfig.privKey | string | `nil` |  |
| kas.fullnameOverride | string | `"kas"` | Optionally override the name |
| kas.ingress.annotations."nginx.ingress.kubernetes.io/rewrite-target" | string | `"/$2"` |  |
| kas.ingress.className | string | `"nginx"` |  |
| kas.ingress.enabled | bool | `false` |  |
| kas.ingress.hosts."host.docker.internal"."/api/kas(/|$)(.*)".pathType | string | `"Prefix"` |  |
| kas.ingress.hosts."opentdf.local"."/api/kas(/|$)(.*)".pathType | string | `"Prefix"` |  |
| kas.ingress.hosts.."/api/kas(/|$)(.*)".pathType | string | `"Prefix"` |  |
| kas.ingress.hosts.localhost."/api/kas(/|$)(.*)".pathType | string | `"Prefix"` |  |
| kas.logLevel | string | `"DEBUG"` |  |
| kas.pdp.disableTracing | string | `"true"` |  |
| kas.pdp.verbose | string | `"true"` |  |
| keycloak-bootstrap.attributes.clientId | string | `"dcr-test"` |  |
| keycloak-bootstrap.attributes.hostname | string | `"http://attributes:4020"` |  |
| keycloak-bootstrap.attributes.preloadedAttributes[0].authority | string | `"https://example.com"` |  |
| keycloak-bootstrap.attributes.preloadedAttributes[0].name | string | `"Classification"` |  |
| keycloak-bootstrap.attributes.preloadedAttributes[0].order[0] | string | `"TS"` |  |
| keycloak-bootstrap.attributes.preloadedAttributes[0].order[1] | string | `"S"` |  |
| keycloak-bootstrap.attributes.preloadedAttributes[0].order[2] | string | `"C"` |  |
| keycloak-bootstrap.attributes.preloadedAttributes[0].order[3] | string | `"U"` |  |
| keycloak-bootstrap.attributes.preloadedAttributes[0].rule | string | `"hierarchy"` |  |
| keycloak-bootstrap.attributes.preloadedAttributes[0].state | string | `"published"` |  |
| keycloak-bootstrap.attributes.preloadedAttributes[1].authority | string | `"https://example.com"` |  |
| keycloak-bootstrap.attributes.preloadedAttributes[1].name | string | `"COI"` |  |
| keycloak-bootstrap.attributes.preloadedAttributes[1].order[0] | string | `"PRX"` |  |
| keycloak-bootstrap.attributes.preloadedAttributes[1].order[1] | string | `"PRA"` |  |
| keycloak-bootstrap.attributes.preloadedAttributes[1].order[2] | string | `"PRB"` |  |
| keycloak-bootstrap.attributes.preloadedAttributes[1].order[3] | string | `"PRC"` |  |
| keycloak-bootstrap.attributes.preloadedAttributes[1].order[4] | string | `"PRD"` |  |
| keycloak-bootstrap.attributes.preloadedAttributes[1].order[5] | string | `"PRF"` |  |
| keycloak-bootstrap.attributes.preloadedAttributes[1].rule | string | `"allOf"` |  |
| keycloak-bootstrap.attributes.preloadedAttributes[1].state | string | `"published"` |  |
| keycloak-bootstrap.attributes.preloadedAuthorities[0] | string | `"https://example.com"` |  |
| keycloak-bootstrap.attributes.realm | string | `"tdf"` |  |
| keycloak-bootstrap.entitlements.hostname | string | `"http://entitlements:4030"` |  |
| keycloak-bootstrap.entitlements.realms[0].clientId | string | `"dcr-test"` |  |
| keycloak-bootstrap.entitlements.realms[0].name | string | `"tdf"` |  |
| keycloak-bootstrap.entitlements.realms[0].password | string | `"testuser123"` |  |
| keycloak-bootstrap.entitlements.realms[0].preloadedClaims.alice_1234[0] | string | `"https://example.com/attr/Classification/value/C"` |  |
| keycloak-bootstrap.entitlements.realms[0].preloadedClaims.alice_1234[1] | string | `"https://example.com/attr/COI/value/PRD"` |  |
| keycloak-bootstrap.entitlements.realms[0].preloadedClaims.bob_1234[0] | string | `"https://example.com/attr/Classification/value/C"` |  |
| keycloak-bootstrap.entitlements.realms[0].preloadedClaims.bob_1234[1] | string | `"https://example.com/attr/COI/value/PRC"` |  |
| keycloak-bootstrap.entitlements.realms[0].preloadedClaims.browsertest[0] | string | `"https://example.com/attr/Classification/value/C"` |  |
| keycloak-bootstrap.entitlements.realms[0].preloadedClaims.browsertest[1] | string | `"https://example.com/attr/COI/value/PRA"` |  |
| keycloak-bootstrap.entitlements.realms[0].preloadedClaims.client_x509[0] | string | `"https://example.com/attr/Classification/value/S"` |  |
| keycloak-bootstrap.entitlements.realms[0].preloadedClaims.client_x509[1] | string | `"https://example.com/attr/COI/value/PRX"` |  |
| keycloak-bootstrap.entitlements.realms[0].preloadedClaims.dcr-test[0] | string | `"https://example.com/attr/Classification/value/C"` |  |
| keycloak-bootstrap.entitlements.realms[0].preloadedClaims.dcr-test[1] | string | `"https://example.com/attr/COI/value/PRF"` |  |
| keycloak-bootstrap.entitlements.realms[0].preloadedClaims.service-account-tdf-client[0] | string | `"https://example.com/attr/Classification/value/C"` |  |
| keycloak-bootstrap.entitlements.realms[0].preloadedClaims.service-account-tdf-client[1] | string | `"https://example.com/attr/COI/value/PRB"` |  |
| keycloak-bootstrap.entitlements.realms[0].preloadedClaims.tdf-client[0] | string | `"https://example.com/attr/Classification/value/S"` |  |
| keycloak-bootstrap.entitlements.realms[0].preloadedClaims.tdf-client[1] | string | `"https://example.com/attr/COI/value/PRX"` |  |
| keycloak-bootstrap.entitlements.realms[0].preloadedClaims.tdf-client[2] | string | `"https://example.com/attr/Env/value/CleanRoom"` |  |
| keycloak-bootstrap.entitlements.realms[0].preloadedClaims.tdf-user[0] | string | `"https://example.com/attr/Classification/value/C"` |  |
| keycloak-bootstrap.entitlements.realms[0].preloadedClaims.tdf-user[1] | string | `"https://example.com/attr/COI/value/PRX"` |  |
| keycloak-bootstrap.entitlements.realms[0].preloadedClaims.user1[0] | string | `"https://example.com/attr/Classification/value/S"` |  |
| keycloak-bootstrap.entitlements.realms[0].preloadedClaims.user1[1] | string | `"https://example.com/attr/COI/value/PRX"` |  |
| keycloak-bootstrap.entitlements.realms[0].username | string | `"user1"` |  |
| keycloak-bootstrap.fullnameOverride | string | `"keycloak-bootstrap"` | Optionally override the name |
| keycloak-bootstrap.keycloak.clientId | string | `"tdf-client"` |  |
| keycloak-bootstrap.keycloak.realm | string | `"tdf"` |  |
| keycloak-bootstrap.secretRef | string | `"name: \"{{ template \"keycloak-bootstrap.fullname\" . }}-otdf-secret\""` |  |
| keycloak.command[0] | string | `"/opt/keycloak/bin/kc.sh"` |  |
| keycloak.command[1] | string | `"--verbose"` |  |
| keycloak.command[2] | string | `"start-dev"` |  |
| keycloak.externalDatabase.database | string | `"keycloak_database"` |  |
| keycloak.extraEnv | string | `"- name: KC_LOG_LEVEL\n  value: INFO\n- name: CLAIMS_URL\n  value: http://entitlement-pdp:3355/entitlements\n- name: KC_DB\n  value: postgres\n- name: KC_DB_URL_PORT\n  value: \"5432\"\n- name: KC_HTTP_RELATIVE_PATH\n  value: \"/auth\"\n- name: KC_HOSTNAME_STRICT_HTTPS\n  value: \"false\"\n- name: KC_HOSTNAME_STRICT\n  value: \"false\"\n- name: KC_HTTP_ENABLED\n  value: \"true\"\n- name: KC_PROXY\n  value: \"edge\"\n- name: JAVA_OPTS_APPEND\n  value: -Djgroups.dns.query={{ include \"keycloak.fullname\" . }}-headless"` |  |
| keycloak.extraEnvFrom | string | `"- secretRef:\n    name: \"{{ include \"keycloak.fullname\" . }}-otdf-secret\""` |  |
| keycloak.fullnameOverride | string | `"keycloak"` | Optionally override the name |
| keycloak.image.pullPolicy | string | `"IfNotPresent"` |  |
| keycloak.image.repository | string | `"ghcr.io/opentdf/keycloak"` |  |
| keycloak.image.tag | string | `"main"` |  |
| keycloak.ingress.annotations."nginx.ingress.kubernetes.io/rewrite-target" | string | `"/auth/$2"` |  |
| keycloak.ingress.enabled | bool | `false` |  |
| keycloak.ingress.ingressClassName | string | `"nginx"` |  |
| keycloak.ingress.rules[0].host | string | `"localhost"` |  |
| keycloak.ingress.rules[0].paths[0].path | string | `"/auth(/|$)(.*)"` |  |
| keycloak.ingress.rules[0].paths[0].pathType | string | `"Prefix"` |  |
| keycloak.ingress.rules[1].host | string | `"host.docker.internal"` |  |
| keycloak.ingress.rules[1].paths[0].path | string | `"/auth(/|$)(.*)"` |  |
| keycloak.ingress.rules[1].paths[0].pathType | string | `"Prefix"` |  |
| keycloak.ingress.rules[2].host | string | `"opentdf.local"` |  |
| keycloak.ingress.rules[2].paths[0].path | string | `"/auth(/|$)(.*)"` |  |
| keycloak.ingress.rules[2].paths[0].pathType | string | `"Prefix"` |  |
| keycloak.ingress.rules[3].host | string | `""` |  |
| keycloak.ingress.rules[3].paths[0].path | string | `"/auth(/|$)(.*)"` |  |
| keycloak.ingress.rules[3].paths[0].pathType | string | `"Prefix"` |  |
| keycloak.ingress.tls | list | `[]` |  |
| keycloak.postgresql.enabled | bool | `false` |  |
| nameOverride | string | `""` | Optionally override the name |
| postgresql.existingSecret | string | `"{{ include \"postgresql.primary.fullname\" . }}-otdf-secret\n"` |  |
| postgresql.fullnameOverride | string | `"postgresql"` | Optionally override the name |
| postgresql.image | object | `{"debug":true}` | Configuration https://github.com/bitnami/charts/tree/master/bitnami/postgresql/#parameters |
| postgresql.initdbScriptsSecret | string | `"{{ include \"postgresql.primary.fullname\" . }}-initdb-secret\n"` |  |
| postgresql.initdbUser | string | `"postgres"` |  |
| secrets.keycloakBootstrap.attributes.password | string | `"testuser123"` | Password of user used to create attributes during bootstap |
| secrets.keycloakBootstrap.attributes.username | string | `"user1"` | Username of user used to create attributes during bootstrap |
| secrets.keycloakBootstrap.clientSecret | string | `"123-456"` | Secret used for 'tdf-client' test client created by bootstrap by default |
| secrets.oidcClientSecret | string | `nil` | Client secret used to verify identity in attributes and entitlements |
| secrets.opaPolicyPullSecret | string | `nil` | Token used to pull OPA policy from private store |
| secrets.postgres.dbPassword | string | `"otdf-pgsql-admin"` | The postgres admin password |
| secrets.postgres.dbUser | string | `"postgres"` | The postgres admin username |
| attributes.affinity | object | `{}` |  |
| attributes.autoscaling.enabled | bool | `false` |  |
| attributes.autoscaling.maxReplicas | int | `100` |  |
| attributes.autoscaling.minReplicas | int | `1` |  |
| attributes.autoscaling.targetCPUUtilizationPercentage | int | `80` |  |
| attributes.fullnameOverride | string | `""` | The fully qualified appname override |
| attributes.image | object | `{"pullPolicy":"IfNotPresent","repo":"ghcr.io/opentdf/attributes","tag":null}` | Configure the container image to use in the deployment. |
| attributes.image.pullPolicy | string | `"IfNotPresent"` | The container's `imagePullPolicy` |
| attributes.image.repo | string | `"ghcr.io/opentdf/attributes"` | The image selector, also called the 'image name' in k8s documentation and 'image repository' in docker's guides. |
| attributes.image.tag | string | `nil` | Chart.AppVersion will be used for image tag, override here if needed |
| attributes.imagePullSecrets | string | `nil` | JSON passed to the deployment's template.spec.imagePullSecrets. Overrides global.opentdf.common.imagePullSecrets |
| attributes.ingress | object | `{"annotations":{},"className":null,"enabled":false,"hosts":{},"tls":null}` | Ingress configuration. To configure, set enabled to true and set `hosts` to a map in the form:      [hostname]:       [path]:         pathType:    your-pathtype [default: "ImplementationSpecific"]         serviceName: your-service  [default: service.fullname]         servicePort: service-port  [default: service.port above] |
| attributes.logLevel | string | `"INFO"` | Sets the default loglevel for the application. One of the valid python logging levels: `DEBUG, INFO, WARNING, ERROR, CRITICAL` |
| attributes.nameOverride | string | `""` | Select a specific name for the resource, instead of the default, attributes |
| attributes.nodeSelector | object | `{}` |  |
| attributes.oidc | object | `{"clientId":"tdf-attributes","externalHost":null,"internalHost":null,"realm":"tdf","scopes":"email"}` | Additional information for connecting to an OIDC provider for AuthN Note that you must also specify a client secret via a secretRef, in the form of an environment variable such as: OIDC_CLIENT_SECRET: myclientsecret |
| attributes.oidc.externalHost | string | `nil` | Override for global.opentdf.common.oidcExternalBaseUrl & url path |
| attributes.oidc.internalHost | string | `nil` | Override for global.opentdf.common.oidcInternalBaseUrl & url path |
| attributes.openapiUrl | string | `""` | Set to enable openapi endpoint |
| attributes.podAnnotations | object | `{}` | Values for the deployment spec.template.metadata.annotations field |
| attributes.podSecurityContext | object | `{}` | Values for deployment's spec.template.spec.securityContext |
| attributes.postgres | object | `{"database":null,"host":null,"port":null,"schema":"tdf_attribute","user":"tdf_attribute_manager"}` | Configuration for the database backend |
| attributes.postgres.database | string | `nil` | Override for global.opentdf.common.postgres.database |
| attributes.postgres.host | string | `nil` | Override for global.opentdf.common.postgres.host |
| attributes.postgres.port | string | `nil` | Override for global.opentdf.common.postgres.post |
| attributes.postgres.schema | string | `"tdf_attribute"` | The entitlement schema |
| attributes.postgres.user | string | `"tdf_attribute_manager"` | Must be a postgres user with tdf_attribute_manager role |
| attributes.replicaCount | int | `1` | Sets the default number of pod replicas in the deployment. Ignored if autoscaling.enabled == true |
| attributes.resources | object | `{}` | Specify required limits for deploying this service to a pod. We usually recommend not to specify default resources and to leave this as a conscious choice for the user. This also increases chances charts run on environments with little resources, such as Minikube. |
| attributes.secretRef | string | `"name: \"{{ template \"attributes.fullname\" . }}-secret\""` | JSON to locate a k8s secret containing environment variables. Notably, this file should include the following environemnt variable definitions:     POSTGRES_PASSWORD: Password corresponding to postgres.user below |
| attributes.securityContext | object | `{}` | Values for deployment's spec.template.spec.containers.securityContext |
| attributes.serverCorsOrigins | string | `""` | Allowed origins for CORS |
| attributes.serverPublicName | string | `"Attribute Authority"` | Name of application. Used during oauth flows, for example when connecting to the OpenAPI endpoint with an OAuth authentication |
| attributes.serverRootPath | string | `"/"` | Base path for this service. Allows serving multiple REST services from the same origin, e.g. using an ingress with prefix mapping as suggested below. |
| attributes.service | object | `{"port":4020,"type":"ClusterIP"}` | Service configuation information. |
| attributes.service.port | int | `4020` | Port to assign to the `http` port |
| attributes.service.type | string | `"ClusterIP"` | Service `spec.type` |
| attributes.serviceAccount | object | `{"annotations":{},"create":true,"name":null}` | A service account to create |
| attributes.serviceAccount.annotations | object | `{}` | Annotations to add to the service account |
| attributes.serviceAccount.create | bool | `true` | Specifies whether a service account should be created |
| attributes.serviceAccount.name | string | `nil` | The name of the service account to use. If not set and create is true, a name is generated using the fullname template |
| attributes.tolerations | list | `[]` |  |
| entitlement-pdp.config.disableTracing | string | `"false"` |  |
| entitlement-pdp.config.externalHost | string | `""` |  |
| entitlement-pdp.config.listenPort | int | `3355` |  |
| entitlement-pdp.config.opaConfigPath | string | `"/etc/opa/config/opa-config.yaml"` |  |
| entitlement-pdp.config.otlpCollectorEndpoint | string | `"opentelemetry-collector.otel.svc:4317"` |  |
| entitlement-pdp.config.verbose | string | `"false"` |  |
| entitlement-pdp.image.pullPolicy | string | `"IfNotPresent"` |  |
| entitlement-pdp.image.repo | string | `"ghcr.io/opentdf/entitlement-pdp"` |  |
| entitlement-pdp.imagePullSecrets | string | `nil` | JSON passed to the deployment's template.spec.imagePullSecrets. Overrides global.opentdf.common.imagePullSecrets when set |
| entitlement-pdp.opaConfig.extraConfigYaml | object | `{"decision_logs":{"console":true}}` | Any extra/additional OPA config defined here will be appended as-is, as raw YAML to the OPA config file generated by the chart. |
| entitlement-pdp.opaConfig.policy.OCIRegistryUrl | string | `"https://ghcr.io"` |  |
| entitlement-pdp.opaConfig.policy.allowInsecureTLS | bool | `false` | This will tell OPA to ignore TLS errors (bad cert, self-signed cert, etc) when downloading an OCI policy bundle from an OCI registry.  Unsuitable for production, used for testing with `localhost` registries |
| entitlement-pdp.opaConfig.policy.bundleRepo | string | `"ghcr.io/opentdf/entitlement-pdp/entitlements-policybundle"` |  |
| entitlement-pdp.opaConfig.policy.updatePolling.maxDelay | int | `120` |  |
| entitlement-pdp.opaConfig.policy.updatePolling.minDelay | int | `60` |  |
| entitlement-pdp.opaConfig.policy.useStaticPolicy | bool | `false` | If `useStaticPolicy` is set to `true`, then an OPA config will be generated that forces the use of a policy bundle that was built and packed into the `entitlement-pdp` container at *build* time, and no policy bundle will be fetched dynamically from the registry on startup. This is not a desirable default, but it is useful in offline deployments. |
| entitlement-pdp.opaConfigMountPath | string | `"/etc/opa/config"` | Where the opa config yaml is mounted |
| entitlement-pdp.replicaCount | int | `3` |  |
| entitlement-pdp.secret.opaPolicyPullSecret | string | `"YOUR_GHCR_PAT_HERE"` |  |
| entitlement-pdp.secretRef | string | `nil` | Additional secrets. You can also add opa |
| entitlement-pdp.serviceAccount.annotations | object | `{}` | Annotations to add to the service account |
| entitlement-pdp.serviceAccount.create | bool | `true` | Specifies whether a service account should be created |
| entitlement-pdp.serviceAccount.name | string | `""` | The name of the service account to use. If not set and create is true, a name is generated using the fullname template |
| entitlement-store.affinity | object | `{}` |  |
| entitlement-store.autoscaling.enabled | bool | `false` |  |
| entitlement-store.autoscaling.maxReplicas | int | `100` |  |
| entitlement-store.autoscaling.minReplicas | int | `1` |  |
| entitlement-store.autoscaling.targetCPUUtilizationPercentage | int | `80` |  |
| entitlement-store.fullnameOverride | string | `""` | The fully qualified appname override |
| entitlement-store.image | object | `{"pullPolicy":"IfNotPresent","repo":"ghcr.io/opentdf/entitlement_store","tag":null}` | Configure the container image to use in the deployment. |
| entitlement-store.image.pullPolicy | string | `"IfNotPresent"` | The container's `imagePullPolicy` |
| entitlement-store.image.repo | string | `"ghcr.io/opentdf/entitlement_store"` | The image selector, also called the 'image name' in k8s documentation and 'image repository' in docker's guides. |
| entitlement-store.image.tag | string | `nil` | Chart.AppVersion will be used for image tag, override here if needed |
| entitlement-store.imagePullSecrets | string | `nil` | JSON passed to the deployment's template.spec.imagePullSecrets. Overrides global.opentdf.common.imagePullSecrets |
| entitlement-store.ingress | object | `{"annotations":{},"className":null,"enabled":false,"hosts":{},"tls":null}` | Ingress configuration. To configure, set enabled to true and set `hosts` to a map in the form:      [hostname]:       [path]:         pathType:    your-pathtype [default: "ImplementationSpecific"]         serviceName: your-service  [default: service.fullname]         servicePort: service-port  [default: service.port above] |
| entitlement-store.logLevel | string | `"INFO"` | Sets the default loglevel for the application. One of the valid python logging levels: `DEBUG, INFO, WARNING, ERROR, CRITICAL` |
| entitlement-store.nameOverride | string | `""` | Select a specific name for the resource, instead of the default, entitlement-store |
| entitlement-store.nodeSelector | object | `{}` |  |
| entitlement-store.oidc.clientId | string | `"tdf-attributes"` |  |
| entitlement-store.oidc.externalHost | string | `nil` | Override for global.opentdf.common.oidcExternalBaseUrl & url path |
| entitlement-store.oidc.internalHost | string | `nil` | Override for global.opentdf.common.oidcInternalBaseUrl & url path |
| entitlement-store.oidc.realm | string | `"tdf"` |  |
| entitlement-store.oidc.scopes | string | `"email"` |  |
| entitlement-store.openapiUrl | string | `""` | Set to enable openapi endpoint |
| entitlement-store.podAnnotations | object | `{}` | Values for the deployment spec.template.metadata.annotations field |
| entitlement-store.podSecurityContext | object | `{}` | Values for deployment's spec.template.spec.securityContext |
| entitlement-store.postgres | object | `{"database":null,"host":null,"port":null,"schema":"tdf_entitlement","user":"tdf_entitlement_reader"}` | Configuration for the database backend |
| entitlement-store.postgres.database | string | `nil` | Override for global.opentdf.common.postgres.database |
| entitlement-store.postgres.host | string | `nil` | Override for global.opentdf.common.postgres.host |
| entitlement-store.postgres.port | string | `nil` | Override for global.opentdf.common.postgres.post |
| entitlement-store.postgres.schema | string | `"tdf_entitlement"` | The entitlement schema |
| entitlement-store.postgres.user | string | `"tdf_entitlement_reader"` | Must be a postgres user with tdf_entitlement_reader role |
| entitlement-store.replicaCount | int | `1` | Sets the default number of pod replicas in the deployment. Ignored if autoscaling.enabled == true |
| entitlement-store.resources | object | `{}` | Specify required limits for deploying this service to a pod. We usually recommend not to specify default resources and to leave this as a conscious choice for the user. This also increases chances charts run on environments with little resources, such as Minikube. |
| entitlement-store.secretRef | string | `"name: {{ template \"entitlement-store.fullname\" . }}-secret"` | JSON to locate a k8s secret containing environment variables. Notably, this file should include the following environemnt variable definitions:     POSTGRES_PASSWORD: Password corresponding to postgres.user below     KAS_CERTIFICATE: Public key for Key Access service     KAS_EC_SECP256R1_CERTIFICATE: Public key (EC Mode) for Key Access service |
| entitlement-store.securityContext | object | `{}` | Values for deployment's spec.template.spec.containers.securityContext |
| entitlement-store.serverCorsOrigins | string | `""` | Allowed origins for CORS |
| entitlement-store.serverPublicName | string | `"entitlement-store"` | Name of application. Used during oauth flows, for example when connecting to the OpenAPI endpoint with an OAuth authentication |
| entitlement-store.serverRootPath | string | `"/"` | Base path for this service. Allows serving multiple REST services from the same origin, e.g. using an ingress with prefix mapping as suggested below. |
| entitlement-store.service | object | `{"port":5000,"type":"ClusterIP"}` | Service configuation information. |
| entitlement-store.service.port | int | `5000` | Port to assign to the `http` port |
| entitlement-store.service.type | string | `"ClusterIP"` | Service `spec.type` |
| entitlement-store.serviceAccount | object | `{"annotations":{},"create":true,"name":null}` | A service account to create |
| entitlement-store.serviceAccount.annotations | object | `{}` | Annotations to add to the service account |
| entitlement-store.serviceAccount.create | bool | `true` | Specifies whether a service account should be created |
| entitlement-store.serviceAccount.name | string | `nil` | The name of the service account to use. If not set and create is true, a name is generated using the fullname template |
| entitlement-store.tolerations | list | `[]` |  |
| entitlements.affinity | object | `{}` |  |
| entitlements.autoscaling.enabled | bool | `false` |  |
| entitlements.autoscaling.maxReplicas | int | `100` |  |
| entitlements.autoscaling.minReplicas | int | `1` |  |
| entitlements.autoscaling.targetCPUUtilizationPercentage | int | `80` |  |
| entitlements.fullnameOverride | string | `""` | The fully qualified appname override |
| entitlements.image | object | `{"pullPolicy":"IfNotPresent","repo":"ghcr.io/opentdf/entitlements","tag":null}` | Container image configuration. |
| entitlements.image.pullPolicy | string | `"IfNotPresent"` | The container's `imagePullPolicy` |
| entitlements.image.repo | string | `"ghcr.io/opentdf/entitlements"` | The image selector, also called the 'image name' in k8s documentation and 'image repository' in docker's guides. |
| entitlements.image.tag | string | `nil` | Chart.AppVersion will be used for image tag, override here if needed |
| entitlements.imagePullSecrets | string | `nil` | JSON passed to the deployment's template.spec.imagePullSecrets. Overrides global.opentdf.common.imagePullSecrets |
| entitlements.ingress | object | `{"annotations":{},"className":null,"enabled":false,"hosts":{},"tls":null}` | Ingress configuration. To configure, set enabled to true and set `hosts` to a map in the form:      [hostname]:       [path]:         pathType:    your-pathtype [default: "ImplementationSpecific"]         serviceName: your-service  [default: service.fullname]         servicePort: service-port  [default: service.port above] |
| entitlements.logLevel | string | `"INFO"` | Sets the default loglevel for the application. One of the valid python logging levels: `DEBUG, INFO, WARNING, ERROR, CRITICAL` |
| entitlements.nameOverride | string | `""` | Select a specific name for the resource, instead of the default, entitlements |
| entitlements.nodeSelector | object | `{}` |  |
| entitlements.oidc | object | `{"clientId":"tdf-entitlement","externalHost":null,"internalHost":null,"realm":"tdf","scopes":"email"}` | Additional information for connecting to an OIDC provider for AuthN Note that you must also specify a client secret via a secretRef, in the form of an environment variable such as: OIDC_CLIENT_SECRET: myclientsecret |
| entitlements.oidc.externalHost | string | `nil` | Override for global.opentdf.common.oidcExternalBaseUrl & url path |
| entitlements.oidc.internalHost | string | `nil` | Override for global.opentdf.common.oidcInternalBaseUrl & url path |
| entitlements.openapiUrl | string | `""` | Set to enable openapi endpoint |
| entitlements.podAnnotations | object | `{}` | Values for the deployment spec.template.metadata.annotations field |
| entitlements.podSecurityContext | object | `{}` | Values for deployment's spec.template.spec.securityContext |
| entitlements.postgres | object | `{"database":null,"host":null,"port":null,"schema":"tdf_entitlement","user":"tdf_entitlement_manager"}` | Configuration for the database backend |
| entitlements.postgres.database | string | `nil` | Override for global.opentdf.common.postgres.database |
| entitlements.postgres.host | string | `nil` | Override for global.opentdf.common.postgres.host |
| entitlements.postgres.port | string | `nil` | Override for global.opentdf.common.postgres.post |
| entitlements.postgres.schema | string | `"tdf_entitlement"` | The entitlement schema |
| entitlements.postgres.user | string | `"tdf_entitlement_manager"` | Must be a postgresql user with the tdf_entitlement_manager role |
| entitlements.replicaCount | int | `1` | Sets the default number of pod replicas in the deployment. Ignored if autoscaling.enabled == true |
| entitlements.resources | object | `{}` | Specify required limits for deploying this service to a pod. We usually recommend not to specify default resources and to leave this as a conscious choice for the user. This also increases chances charts run on environments with little resources, such as Minikube. |
| entitlements.secretRef | string | `"name: {{ template \"entitlements.fullname\" . }}-secret"` | JSON to locate a k8s secret containing environment variables. Notably, this file should include the following environemnt variable definitions:     POSTGRES_PASSWORD: Password corresponding to postgres.user below |
| entitlements.securityContext | object | `{}` | Values for deployment's spec.template.spec.containers.securityContext |
| entitlements.serverCorsOrigins | string | `""` | Allowed origins for CORS |
| entitlements.serverPublicName | string | `"Entitlement"` | Name of application. Used during oauth flows, for example when connecting to the OpenAPI endpoint with an OAuth authentication |
| entitlements.serverRootPath | string | `"/"` | Base path for this service. Allows serving multiple REST services from the same origin, e.g. using an ingress with prefix mapping as suggested below. |
| entitlements.service | object | `{"port":4030,"type":"ClusterIP"}` | Service configuation information. |
| entitlements.service.port | int | `4030` | Port to assign to the `http` port |
| entitlements.service.type | string | `"ClusterIP"` | Service `spec.type` |
| entitlements.serviceAccount | object | `{"annotations":{},"create":true,"name":null}` | A service account to create |
| entitlements.serviceAccount.annotations | object | `{}` | Annotations to add to the service account |
| entitlements.serviceAccount.create | bool | `true` | Specifies whether a service account should be created |
| entitlements.serviceAccount.name | string | `nil` | The name of the service account to use. If not set and create is true, a name is generated using the fullname template |
| entitlements.tolerations | list | `[]` |  |
| entity-resolution.config.disableTracing | string | `"false"` |  |
| entity-resolution.config.externalHost | string | `""` |  |
| entity-resolution.config.keycloak.clientId | string | `"tdf-entity-resolution-service"` |  |
| entity-resolution.config.keycloak.legacy | bool | `false` | Using a legacy keycloak version. See https://github.com/Nerzal/gocloak/issues/346 |
| entity-resolution.config.keycloak.realm | string | `"tdf"` |  |
| entity-resolution.config.keycloak.url | string | `nil` | Override for global.opentdf.common.oidcInternalBaseUrl |
| entity-resolution.config.listenPort | int | `7070` |  |
| entity-resolution.config.otlpCollectorEndpoint | string | `"opentelemetry-collector.otel.svc:4317"` |  |
| entity-resolution.config.verbose | string | `"false"` |  |
| entity-resolution.createKeycloakClientSecret | bool | `true` |  |
| entity-resolution.fullnameOverride | string | `""` | Optionally override the fully qualified name |
| entity-resolution.image.pullPolicy | string | `"IfNotPresent"` |  |
| entity-resolution.image.repo | string | `"ghcr.io/opentdf/entity-resolution"` |  |
| entity-resolution.imagePullSecrets | string | `nil` | JSON passed to the deployment's template.spec.imagePullSecrets. Overrides global.opentdf.common.imagePullSecrets |
| entity-resolution.nameOverride | string | `""` | Optionally override the name |
| entity-resolution.replicaCount | int | `1` |  |
| entity-resolution.secret.keycloak.clientSecret | string | `"REPLACE_AT_INSTALL_TIME"` |  |
| entity-resolution.serviceAccount | object | `{"annotations":{},"create":true,"name":""}` | A service account to create |
| entity-resolution.serviceAccount.annotations | object | `{}` | Annotations to add to the service account |
| entity-resolution.serviceAccount.create | bool | `true` | Specifies whether a service account should be created |
| entity-resolution.serviceAccount.name | string | `""` | The name of the service account to use. If not set and create is true, a name is generated using the fullname template |
| kas.SWAGGER_UI | string | `"True"` | To enable swagger ui |
| kas.affinity | object | `{}` |  |
| kas.autoscaling.enabled | bool | `false` |  |
| kas.autoscaling.maxReplicas | int | `100` |  |
| kas.autoscaling.minReplicas | int | `1` |  |
| kas.autoscaling.targetCPUUtilizationPercentage | int | `80` |  |
| kas.certFileSecretName | string | `nil` | Secret containing an additional ca-cert.pem file for locally signed TLS certs. Used for a private PKI mode, for example. |
| kas.endpoints.attrHost | string | `"http://attributes:4020"` | Internal url of attributes service |
| kas.endpoints.oidcPubkeyEndpoint | string | `nil` | Local override for global.opentdf.common.oidcInternalBaseUrl + path |
| kas.endpoints.statsdHost | string | `"statsd"` | Internal url of statsd |
| kas.envConfig | object | `{"attrAuthorityCert":null,"cert":null,"ecCert":null,"ecPrivKey":null,"privKey":null}` | Environment configuration values for keys and certs used by the key server.  If externalSecretName is defined these are ignored. |
| kas.externalEnvSecretName | string | `nil` | The name of a secret containing required config values (see envConfig below); overrides envConfig |
| kas.extraEnvSecretName | string | `nil` | Secret containing additional env variables in addition to those provided by envConfig or externalSecretName |
| kas.flaskDebug | string | `"False"` | If the debug mode should  be enabled in flask |
| kas.fullnameOverride | string | `""` | The fully qualified appname override |
| kas.image | object | `{"pullPolicy":"IfNotPresent","repo":"ghcr.io/opentdf/kas","tag":null}` | Container image configuration. |
| kas.image.pullPolicy | string | `"IfNotPresent"` | The container's `imagePullPolicy` |
| kas.image.repo | string | `"ghcr.io/opentdf/kas"` | The image selector, also called the 'image name' in k8s documentation and 'image repository' in docker's guides. |
| kas.image.tag | string | `nil` | Chart.AppVersion will be used for image tag, override here if needed |
| kas.imagePullSecrets | string | `nil` | JSON passed to the deployment's template.spec.imagePullSecrets. Overrides global.opentdf.common.imagePullSecrets |
| kas.ingress | object | `{"annotations":{},"className":null,"enabled":false,"hosts":{},"tls":null}` | Ingress configuration. To configure, set enabled to true and set `hosts` to a map in the form:      [hostname]:       [path]:         pathType:    your-pathtype [default: "ImplementationSpecific"]         serviceName: your-service  [default: service.fullname]         servicePort: service-port  [default: service.port above]  To configure HTTPS mode for mutual TLS,    tls:      certFileSecretName: your-k8s-secret |
| kas.jsonLogger | string | `"true"` | Determinies whether KAS uses the json formatter for logging, if false the dev formatter is used. Default is true |
| kas.livenessProbe | object | `{"httpGet":{"path":"/healthz?probe=liveness","port":"http"}}` | Adds a container livenessProbe, if set. |
| kas.logLevel | string | `"INFO"` | Sets the default loglevel for the application. One of the valid python logging levels: `DEBUG, INFO, WARNING, ERROR, CRITICAL` |
| kas.maxUnavailable | int | `1` | Pod disruption budget |
| kas.nameOverride | string | `""` | Select a specific name for the resource, instead of the default, kas |
| kas.nodeSelector | object | `{}` |  |
| kas.openapiUrl | string | `""` | Set to enable openapi endpoint |
| kas.pdp.disableTracing | string | `"true"` | KAS's internal Access PDP can send OpenTelemetry traces to collectors - if no collectors configured, the traces will get redirected to STDOUT, which is a bit spammy, so turn this off until we do proper OT trace collection everywhere. |
| kas.pdp.verbose | string | `"false"` | Enables verbose mode for the internal PDP (policy decision point) KAS uses. If `yes`, decisions will be logged with much additional detail |
| kas.podAnnotations | object | `{}` | Values for the deployment spec.template.metadata.annotations field |
| kas.podSecurityContext | object | `{}` | Values for deployment's spec.template.spec.securityContext |
| kas.readinessProbe | object | `{"httpGet":{"path":"/healthz?probe=readiness","port":"http"}}` | Adds a container readinessProbe, if set. |
| kas.replicaCount | int | `1` | Sets the default number of pod replicas in the deployment. Ignored if autoscaling.enabled == true |
| kas.resources | object | `{}` | Specify required limits for deploying this service to a pod. We usually recommend not to specify default resources and to leave this as a conscious choice for the user. This also increases chances charts run on environments with little resources, such as Minikube. |
| kas.securityContext | object | `{}` | Values for deployment's spec.template.spec.containers.securityContext |
| kas.serverRootPath | string | `"/"` | Base path for this service. Allows serving multiple REST services from the same origin, e.g. using an ingress with prefix mapping as suggested below. |
| kas.service | object | `{"port":8000,"type":"ClusterIP"}` | Service configuation information. |
| kas.service.port | int | `8000` | Port to assign to the `http` port |
| kas.service.type | string | `"ClusterIP"` | Service `spec.type` |
| kas.serviceAccount | object | `{"annotations":{},"create":true,"name":null}` | A service account to create |
| kas.serviceAccount.annotations | object | `{}` | Annotations to add to the service account |
| kas.serviceAccount.create | bool | `true` | Specifies whether a service account should be created |
| kas.serviceAccount.name | string | `nil` | The name of the service account to use. If not set and create is true, a name is generated using the fullname template |
| kas.tolerations | list | `[]` |  |
| keycloak-bootstrap.attributes.clientId | string | `"dcr-test"` |  |
| keycloak-bootstrap.attributes.hostname | string | `"http://attributes"` |  |
| keycloak-bootstrap.attributes.preloadedAttributes | string | `nil` |  |
| keycloak-bootstrap.attributes.preloadedAuthorities | string | `nil` |  |
| keycloak-bootstrap.attributes.realm | string | `"tdf"` |  |
| keycloak-bootstrap.entitlements.hostname | string | `"http://entitlements"` |  |
| keycloak-bootstrap.entitlements.realms[0].clientId | string | `"dcr-test"` |  |
| keycloak-bootstrap.entitlements.realms[0].name | string | `"tdf"` |  |
| keycloak-bootstrap.entitlements.realms[0].password | string | `"testuser123"` |  |
| keycloak-bootstrap.entitlements.realms[0].preloadedClaims | object | `{}` |  |
| keycloak-bootstrap.entitlements.realms[0].username | string | `"user1"` |  |
| keycloak-bootstrap.externalUrl | string | `nil` | Deprecated. Use opentdf.externalUrl |
| keycloak-bootstrap.image.pullPolicy | string | `"IfNotPresent"` | Defaults to IfNotPresent to skip lookup of newer versions. |
| keycloak-bootstrap.image.repo | string | `"ghcr.io/opentdf/keycloak-bootstrap"` |  |
| keycloak-bootstrap.image.tag | string | `nil` | Chart.AppVersion will be used for image tag, override here if needed |
| keycloak-bootstrap.istioTerminationHack | bool | `false` | Is istio in place and requires a wait on the sidecar. |
| keycloak-bootstrap.job.backoffLimit | int | `25` |  |
| keycloak-bootstrap.keycloak.clientId | string | `"tdf-client"` |  |
| keycloak-bootstrap.keycloak.customConfig | string | `nil` | if provided, will use custom configuration instead |
| keycloak-bootstrap.keycloak.hostname | string | `nil` | override for global.opentdf.common.oidcExternalBaseUrl |
| keycloak-bootstrap.keycloak.npeClients | string | `nil` |  |
| keycloak-bootstrap.keycloak.passwordUsers | string | `"testuser@virtru.com,user1,user2"` |  |
| keycloak-bootstrap.keycloak.preloadedClients | string | `nil` |  |
| keycloak-bootstrap.keycloak.preloadedUsers | string | `nil` |  |
| keycloak-bootstrap.nameOverride | string | `""` | Select a specific name for the resource, instead of the default, keycloak-bootstrap |
| keycloak-bootstrap.opentdf.externalUrl | string | `nil` | Base URL for clients. Defaults to oidcExternalBaseUrl. A client app's homepage Defaults to OIDC url without path attached. |
| keycloak-bootstrap.opentdf.redirectUris | string | `nil` | A list of valid redirect paths. Defaults to externalUrl |
| keycloak-bootstrap.pki.browserEnable | string | `"true"` |  |
| keycloak-bootstrap.pki.directGrantEnable | string | `"true"` |  |
| keycloak-bootstrap.replicaCount | int | `1` |  |
| keycloak-bootstrap.secretRef | string | `"name: {{ template \"keycloak-bootstrap.fullname\" . }}-secret"` | Expect a secret with following keys: - keycloak_admin_username: - keycloak_admin_password: - CLIENT_SECRET: - ATTRIBUTES_USERNAME: - ATTRIBUTES_PASSWORD: |