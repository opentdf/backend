# entitlement-pdp
Repo for Entitlement Policy Decision Point (PDP) service

What's an Entitlement PDP?
 - https://virtru.atlassian.net/wiki/spaces/ENG/pages/2433450039/Standardized+ABAC+Terminology+And+Abbreviations

![ABAC System](./index.png)

## Modifying/Building/Publishing Entitlement Policy Logic

See [entitlement-policy](entitlement-policy/README.md) subfolder

## Helm chart

Published to `oci://ghcr.io/virtru-corp/entitlement-pdp/chart`

## OCI container image

### Test

``` sh
make test
```

### Build container image

``` sh
make dockerbuild
```

### Publish container image

``` sh
make dockerbuildpush
```

Published to `oci://ghcr.io/virtru-corp/entitlement-pdp`
