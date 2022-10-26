
## Deploy Chart

1. Create Cluster: `ctlptl create cluster kind --registry=ctlptl-registry --name kind-opentdf`
2. Update Dependencies: `helm dependency update`
3. Run certs.env `source ../../certs/.env`
4. Install Chart: 
```
helm upgrade --install backend -f values.yaml -f testing/deployment.yaml \
--set kas.envConfig.attrAuthorityCert=$ATTR_AUTHORITY_CERTIFICATE \
--set kas.envConfig.ecCert=$KAS_EC_SECP256R1_CERTIFICATE \
--set kas.envConfig.cert=$KAS_CERTIFICATE \
--set kas.envConfig.ecPrivKey=$KAS_EC_SECP256R1_PRIVATE_KEY \
--set kas.envConfig.privKey=$KAS_PRIVATE_KEY .
```

## Cluster Status 
  To check to see if your cluster is running, enter the following command:
  `kubectl get pods` 

## Setting Up An Ingress (Optional)
```
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx

helm install nginx-ingress-controller ingress-nginx/ingress-nginx --version 4.2.1 --set controller.config.large-client-header-buffers="20 32k"

helm upgrade --install backend -f values.yaml -f testing/deployment.yaml \
-f testing/ingress.yaml \
--set kas.envConfig.attrAuthorityCert=$ATTR_AUTHORITY_CERTIFICATE \
--set kas.envConfig.ecCert=$KAS_EC_SECP256R1_CERTIFICATE \
--set kas.envConfig.cert=$KAS_CERTIFICATE \
--set kas.envConfig.ecPrivKey=$KAS_EC_SECP256R1_PRIVATE_KEY \
--set kas.envConfig.privKey=$KAS_PRIVATE_KEY .

kubectl port-forward service/nginx-ingress-controller-ingress-nginx-controller 65432:80
```

## Cleanup
1. Uninstall Chart: `helm uninstall backend`
2. Uninstall Ingress (if used): `helm uninstall nginx-ingress-controller`
3. Delete Cluster: `ctlptl delete cluster kind-opentdf`
