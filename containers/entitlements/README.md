# Entitlements

## Development

### Start database

see [migration](../migration/README.md)

### Configure server
```shell
export POSTGRES_HOST=localhost
export POSTGRES_USER=tdf_entitlement_manager
export POSTGRES_PASSWORD=myPostgresPassword
export POSTGRES_DATABASE=tdf_database
export POSTGRES_SCHEMA=tdf_entitlement
export SERVER_LOG_LEVEL=DEBUG
```

### Start Server
```shell
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install --requirement requirements.txt
python3 -m uvicorn main:app --reload --port 4030
```

### Extract OpenAPI
```shell
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install --requirement requirements.txt
python3 main.py > openapi.json
```

### View API

#### Swagger UI
http://localhost:4030/docs

#### ReDoc
http://localhost:4030/redoc

## Kubernetes

### build image
```shell
# from project root
docker build --no-cache --tag virtru/tdf-entitlements-service:0.2.0 entitlements
```

### secrets
```shell
kubectl create secret generic entitlements-secrets --from-literal=POSTGRES_PASSWORD=myPostgresPassword
```

### helm
```shell
# from project root
helm upgrade --install entitlements ./charts/entitlements --debug
```
