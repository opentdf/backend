

### Keycloak

```shell
kubectl create namespace keycloak
helm install --version 5.1.1 --values keycloak-tdf-values.yaml --namespace keycloak keycloak bitnami/keycloak
```