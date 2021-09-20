# etheria Tiltfile for development
# reference https://docs.tilt.dev/api.html
#
# ## Fun things you can learn:
#
# 

# extensions https://github.com/tilt-dev/tilt-extensions
# nice-to-have change from `ext:` to `@tilt_ext`
load('ext://secret', 'secret_yaml_generic')
load('ext://helm_remote', 'helm_remote')

PY_VERSION = os.environ.get('PY_VERSION', '3.9')
std_args = {'PY_VERSION': PY_VERSION}

# secrets
watch_file('certs')
k8s_yaml(secret_yaml_generic('etheria-secrets',
                             from_file=[
                                 'EAS_PRIVATE_KEY=certs/eas-private.pem',
                                 'EAS_CERTIFICATE=certs/eas-public.pem',
                                 'KAS_EC_SECP256R1_CERTIFICATE=certs/kas-ec-secp256r1-public.pem',
                                 'KAS_CERTIFICATE=certs/kas-public.pem',
                                 'KAS_EC_SECP256R1_PRIVATE_KEY=certs/kas-ec-secp256r1-private.pem',
                                 'KAS_PRIVATE_KEY=certs/kas-private.pem',
                                 'ca-cert.pem=certs/ca.crt'
                                 ]))
k8s_yaml(secret_yaml_generic('attribute-authority-secrets', from_literal='POSTGRES_PASSWORD=myPostgresPassword'))
k8s_yaml(secret_yaml_generic('entitlement-secrets', from_literal=['POSTGRES_PASSWORD=myPostgresPassword']))
k8s_yaml(secret_yaml_generic('tdf-storage-secrets', from_literal=['AWS_SECRET_ACCESS_KEY=mySecretAccessKey','AWS_ACCESS_KEY_ID=myAccessKeyId']))
k8s_yaml(local(['kubectl', 'create', 'secret', 'tls', 'etheria-tls',
    '--cert', 'certs/reverse-proxy.crt',
    '--key', 'certs/reverse-proxy.key',
    '-o=yaml', '--dry-run=client']))

# builds
docker_build('opentdf/tdf-python-base', 'containers/python_base',
    build_args=std_args, extra_tag=PY_VERSION)
docker_build('opentdf/tdf-attribute-authority', 'containers/service_attribute_authority', build_args=std_args)
docker_build('opentdf/tdf-entitlement', 'containers/service_entitlement', build_args=std_args)
docker_build('opentdf/tdf-remote-payload', 'containers/service_remote_payload')
docker_build('opentdf/tdf-key-access', 'containers/kas', build_args=std_args)


# Note: Abacus URL parameters are currently baked into the base 
# image
docker_build('opentdf/tdf-abacus', 'containers/abacus',
    target='server',
    build_args={
        'abacusBaseUrl': '/abacus',
        'abacusAssetPrefix': '/abacus',
        'easApiUrl': 'https://etheria.local/eas',
    },
)

# remote resources
# usage https://github.com/tilt-dev/tilt-extensions/tree/master/helm_remote#additional-parameters
# Docs: https://github.com/codecentric/helm-charts/blob/master/charts/keycloak/README.md
helm_remote('keycloak', repo_url='https://codecentric.github.io/helm-charts', values=['deployments/local/values-virtru-keycloak.yaml'])
# Docs: https://github.com/bitnami/charts/tree/master/bitnami/postgresql
helm_remote('postgresql', repo_url='https://charts.bitnami.com/bitnami', release_name='tdf', values=['deployments/local/values-postgresql-tdf.yaml'])

# helm charts
# usage https://docs.tilt.dev/helm.html#helm-options
k8s_yaml(helm('charts/etheria', name='etheria', values=['deployments/local/values-all-in-one.yaml']))

# ##Resource Graph
#
# Tile reads helm and other kubernetes yaml data into its own service
# and will only deploys what you ask for. otherwise it deploys 'everything'
# it can find in the resource graph you build. Since most k8s tools have
# implicit resource deps, if you add a new service or job (or sometimes when
# you update a service or aggregate object like a chart or application) you
# should also add a corresponding k8s_resource metadata line. This makes sure
# services come up in an order that minimizes thrashing, and services that have
# deps will start properly using `tile up my-service`, which is often useful
# if you are working with a smaller part of the backend graph.

# Found in the umbrella chart, a web front end for entitlements and attributes
k8s_resource('abacus', labels=['frontend'], resource_deps=['etheria-entitlement'])

k8s_resource('etheria-attribute-authority', labels=['backend'], resource_deps=['tdf-postgresql'])
# k8s_resource('attribute-provider', labels=['backend'])
k8s_resource('etheria-entitlement', labels=['backend'], resource_deps=['tdf-postgresql'])
# k8s_resource('eas', labels=['backend'])
# k8s_resource('kas', labels=['backend'])

# TODO: rename keycloak-* to identity-*
k8s_resource('keycloak', labels=['backend', 'thirdparty'], resource_deps=['keycloak-postgresql'])
k8s_resource('keycloak-postgresql', labels=['backend', 'thirdparty'])
k8s_resource('keycloak-bootstrap', labels=['backend', 'thirdparty'])

# Postgres service for opentdf backend. Included in charts/etheria.
k8s_resource('tdf-postgresql', labels=['backend', 'thirdparty'], port_forwards=[5432])
# Persistent storage service for opentdf backend. Included in charts/etheria.
k8s_resource('etheria-tdf-storage', labels=['backend'])

# TODO this service requires actual S3 secrets
# TODO or use https://github.com/localstack/localstack
#k8s_yaml(helm('charts/remote_payload', 'remote-payload', values=['deployments/docker-desktop/remote_payload-values.yaml']))
# deprecated
#k8s_yaml(helm('charts/eas', 'eas', values=['deployments/docker-desktop/eas-values.yaml']))
#k8s_yaml(helm('charts/abacus', 'abacus', values=['deployments/docker-desktop/abacus-values.yaml']))


# resource dependencies
# k8s_resource('abacus', resource_deps=['tdf-postgresql'])
# k8s_resource('attribute-authority', resource_deps=['tdf-postgresql'])
# k8s_resource('entitlement', resource_deps=['tdf-postgresql'])
# k8s_resource('entitlement', resource_deps=['tdf-postgresql'])



# Test service
# TODO How do we load these into test (aka local_resource) below?
# docker_build('eternia-base', '../eternia')
# docker_build('opentdf/eternia-kuttl-runner', 'tests/containers/eternia-kuttl-runner')

test('kuttl-tests', 'tests/containers/eternia-kuttl-runner/build-test-runner-image.sh && kubectl kuttl test tests/cluster', deps=['./tests/cluster'], resource_deps=["attribute-provider"])
# k8s_resource(workload='kuttl-tests', labels=['test'])
