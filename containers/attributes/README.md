# Attributes

## Development

### Start database

see [migration](../migration/README.md)

### Configure server

```shell
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=tdf_attribute_manager
export POSTGRES_PASSWORD=myPostgresPassword
export POSTGRES_DATABASE=tdf_database
export POSTGRES_SCHEMA=tdf_attribute
export SERVER_LOG_LEVEL=DEBUG
export OIDC_CLIENT_ID="localhost-attributes"
export OIDC_REALM="opentdf-realm"
export OIDC_SCOPES="openid"
export OIDC_SERVER_URL="https://<<host>>/auth/"
export OIDC_AUTHORIZATION_URL="https://<<host>>/auth/realms/opentdf-realm/protocol/openid-connect/auth"
export OIDC_TOKEN_URL="https://<<host>>s/auth/realms/opentdf-realm/protocol/openid-connect/token"
export OIDC_CONFIGURATION_URL="https://<<host>>/auth/realms/opentdf-realm/.well-known/openid-configuration"
```

### Start Server

Update import for local, non-container env
`from ..python_base import get_query, Pagination`

Add blank `__init__.py` to `containers/`

Run from project root

```shell
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install --requirement python_base/requirements.txt
python3 -m pip install --requirement attributes/requirements.txt
python3 -m uvicorn attributes.main:app --reload --port 4020
python3 -m pip install --requirement containers/attributes/requirements.txt
python3 -m uvicorn containers.attributes.main:app --reload --port 4020
```

### Extract OpenAPI

```shell
./scripts/openapi-generator
```

### View API

#### Swagger UI

http://localhost:4020/docs

#### ReDoc

http://localhost:4020/redoc

## Kubernetes

### build image

```shell
# from project root
docker build --no-cache --tag opentdf/attributes:0.2.0 attributes
```

### secrets

```shell
kubectl create secret generic attributes-secrets --from-literal=POSTGRES_PASSWORD=myPostgresPassword
```

### helm

```shell
# from project root
helm upgrade --install attributes ./charts/attributes --debug
```

### Troubleshooting

Check connectivity, run shell in pod

```shell
apk add curl
curl telnet://keycloak-http/auth/
```
