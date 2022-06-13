# entitlement-pdp
Repo for Entitlement Policy Decision Point (PDP) service

What's an Entitlement PDP?

![ABAC System](./index.png)

## Modifying/Building/Publishing Entitlement Policy Logic

See [entitlement-policy](entitlement-policy/README.md) subfolder

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

Published to `oci://ghcr.io/opentdf/entitlement-pdp`
