## Base

Base image for building python webservices.

### Base build image

#### Docker Hub

https://hub.docker.com/repository/docker/opentdf/tdf-python-base

#### Buildkite

https://buildkite.com/virtru/opentdf-base

#### Local build
```shell
cd service_base
docker build --tag opentdf/tdf-python-base .
```

#### Update requirements.txt
```shell
cd service_entity_object
pipenv lock --keep-outdated --requirements > ../service_base/requirements.txt
```