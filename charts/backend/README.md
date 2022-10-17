
## Deploy Chart

1. Update Dependencies: `helm dependency update`
1. Install Chart: `helm upgrade --install backend -f values.yaml`

## Troubleshooting 

Helm Upgrade Usage Error:

```Error: "helm upgrade" requires 2 arguments

Usage:  helm upgrade [RELEASE] [CHART] [flags]
```

Try running `helm upgrade --install backend -f values.yaml .` 


Secrets Errors:
```Error: unable to build kubernetes objects from release manifest: error validating "": error validating data: unknown object type "nil" in Secret.stringData.OIDC_CLIENT_SECRET
```

Add default values (or your own configured values) to the [backend/values.yaml](https://github.com/opentdf/backend/blob/main/charts/backend/values.yaml#L42) file:
```secrets:
  opaPolicyPullSecret: "xy"
  oidcClientSecret: "xx"
  ```

## Cluster status 
  To check to see if your cluster is running, enter the following command:
  `kubectl get pods` 