## Base

Provides a standard base for python microservices and job containers, including
a recommended set of dependencies, including `requests`, `fastapi`, and others.

### Base build image

#### Docker Hub

https://hub.docker.com/repository/docker/opentdf/python-base

#### Local build

```shell
cd containers/python_base
docker build --tag opentdf/python-base .
```

#### Upgrade requirements.txt

```shell
cd containers/python_base
pip3 install pip-upgrader
pip-upgrade --skip-package-installation
```
