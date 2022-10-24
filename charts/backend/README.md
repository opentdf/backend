
## Deploy Chart

1. Create Cluster: `ctlptl create cluster kind --registry=ctlptl-registry --name kind-opentdf`
2. Update Dependencies: `helm dependency update`
3. Install Chart: `helm upgrade --install backend -f values.yaml -f deployment.yaml .`

## Cluster Status 
  To check to see if your cluster is running, enter the following command:
  `kubectl get pods` 

## Cleanup

1. Uninstall Chart: `helm uninstall backend`
2. Delete Cluster: `ctlptl delete cluster kind-opentdf`

## Troubleshooting 
Secrets Errors:
```
Error: unable to build kubernetes objects from release manifest: error validating "": error validating data: unknown object type "nil" in Secret.stringData.OIDC_CLIENT_SECRET
```

Add default values (or your own configured values) to the [backend/values.yaml](https://github.com/opentdf/backend/blob/main/charts/backend/values.yaml#L42) file:
```
secrets:
  opaPolicyPullSecret: "xy"
  oidcClientSecret: "xx"
```
