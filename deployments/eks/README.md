

### Keycloak

#### Install
```shell
kubectl create namespace keycloak
helm install --version 6.0.0 --values keycloak-tdf-values.yaml --namespace keycloak keycloak bitnami/keycloak
```

#### Upgrade
```shell
export POSTGRESQL_PASSWORD=$(kubectl get secret --namespace "keycloak" keycloak-postgresql -o jsonpath="{.data.postgresql-password}" | base64 --decode)

helm upgrade --install \
    --version 6.0.0 \
    --set postgresql.postgresqlPassword=$POSTGRESQL_PASSWORD \
    --values keycloak-tdf-values.yaml \
    --namespace keycloak \
    keycloak bitnami/keycloak
```
