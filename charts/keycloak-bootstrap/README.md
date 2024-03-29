# keycloak-bootstrap

![Version: 0.4.4](https://img.shields.io/badge/Version-0.4.4-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: main](https://img.shields.io/badge/AppVersion-main-informational?style=flat-square)

Keycloak Bootstrap Configurator Job

## Maintainers

| Name    | Email                | Url          |
| ------- | -------------------- | ------------ |
| OpenTDF | <support@opentdf.io> | <opentdf.io> |

## Values

| Key                                       | Type   | Default                                                           | Description                                                                                                                                               |
| ----------------------------------------- | ------ | ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| attributes.clientId                       | string | `"dcr-test"`                                                      | Keycloak client id used to create attributes                                                                                                              |
| attributes.hostname                       | string | `"http://attributes"`                                             | Internal attributes service url                                                                                                                           |
| attributes.preloadedAttributes            | string | `nil`                                                             | List of attributes to create in the form: [{authority:"", name:"", rule:"", state:"", order:[]}]                                                          |
| attributes.preloadedAuthorities           | string | `nil`                                                             | List of authorities to create                                                                                                                             |
| attributes.realm                          | string | `"tdf"`                                                           | Realm of keycloak client used to create attributes                                                                                                        |
| entitlements.hostname                     | string | `"http://entitlements"`                                           | Internal entitlements service url                                                                                                                         |
| entitlements.realms[0].clientId           | string | `"dcr-test"`                                                      | OIDC client ID used to create entitlements                                                                                                                |
| entitlements.realms[0].name               | string | `"tdf"`                                                           | Name of realm for which creating entitlements                                                                                                             |
| entitlements.realms[0].password           | string | `"testuser123"`                                                   | Password for given username used to create entitlements                                                                                                   |
| entitlements.realms[0].preloadedClaims    | object | `{}`                                                              | Entitlements to create, in the form {client: ["attribute"]}                                                                                               |
| entitlements.realms[0].username           | string | `"user1"`                                                         | OIDC username used to create entitlements                                                                                                                 |
| existingConfigSecret                      | string | `nil`                                                             |                                                                                                                                                           |
| externalUrl                               | string | `nil`                                                             | Deprecated. Use `opentdf.externalUrl`                                                                                                                     |
| global.opentdf.common.imagePullSecrets    | list   | `[]`                                                              | JSON passed to the deployment's `template.spec.imagePullSecrets`                                                                                          |
| global.opentdf.common.oidcExternalBaseUrl | string | `"http://localhost:65432"`                                        | Base external url of OIDC provider                                                                                                                        |
| global.opentdf.common.oidcInternalBaseUrl | string | `"http://keycloak-http"`                                          | Base internal k8s url of OIDC provider                                                                                                                    |
| global.opentdf.common.oidcUrlPath         | string | `"auth"`                                                          | Optional path added to base OIDC url                                                                                                                      |
| image.pullPolicy                          | string | `"IfNotPresent"`                                                  | Defaults to `IfNotPresent` to skip lookup of newer versions.                                                                                              |
| image.repo                                | string | `"ghcr.io/opentdf/keycloak-bootstrap"`                            | The image selector, also called the 'image name' in k8s documentation and 'image repository' in docker's guides.                                          |
| image.tag                                 | string | `nil`                                                             | Chart.AppVersion will be used for image tag, override here if needed                                                                                      |
| istioTerminationHack                      | bool   | `false`                                                           | Is istio in place and requires a wait on the sidecar.                                                                                                     |
| job.backoffLimit                          | int    | `25`                                                              | number of retries before considering a Job as failed                                                                                                      |
| keycloak.customConfig                     | string | `nil`                                                             | if provided, will use custom configuration instead                                                                                                        |
| keycloak.hostname                         | string | `nil`                                                             | override for `global.opentdf.common.oidcExternalBaseUrl`                                                                                                  |
| keycloak.npeClients                       | string | `nil`                                                             | Create test clients configured for clientcreds auth flow (list)                                                                                           |
| keycloak.passwordUsers                    | string | `"testuser@virtru.com,user1,user2"`                               | Comma seperated list of users to be created with default password "testuser123"                                                                           |
| keycloak.preloadedClients                 | string | `nil`                                                             | Create clients in list with given client id and secret. In the form [{clientId:"id", clientSecret:"secret"}]                                              |
| keycloak.preloadedUsers                   | string | `nil`                                                             | Create user in list with given username and password. In the form [{username:"user", password:"pass"}]                                                    |
| nameOverride                              | string | `""`                                                              | Select a specific name for the resource, instead of the default, keycloak-bootstrap                                                                       |
| opentdf.externalUrl                       | string | `nil`                                                             | Base URL for clients. Defaults to `oidcExternalBaseUrl`. A client app's homepage Defaults to OIDC url without path attached.                              |
| opentdf.redirectUris                      | string | `nil`                                                             | A list of valid redirect paths. Defaults to `externalUrl`                                                                                                 |
| pki.browserEnable                         | string | `"true"`                                                          | # X.509 Client Certificate Authentication to a Browser Flow enabled                                                                                       |
| pki.directGrantEnable                     | string | `"true"`                                                          | X.509 Client Certificate Authentication to a Direct Grant Flow enabled                                                                                    |
| replicaCount                              | int    | `1`                                                               | Sets the default number of pod replicas in the deployment. Ignored if `autoscaling.enabled` == true                                                       |
| secretRef                                 | string | `"name: {{ template \"keycloak-bootstrap.fullname\" . }}-secret"` | Expect a secret with following keys: - keycloak_admin_username: - keycloak_admin_password: - CLIENT_SECRET: - ATTRIBUTES_USERNAME: - ATTRIBUTES_PASSWORD: |

---

Autogenerated from chart metadata using [helm-docs v1.11.0](https://github.com/norwoodj/helm-docs/releases/v1.11.0)
