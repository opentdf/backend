# OpenTDF Configuration service

## Setup

1. minikube

2. Install Istio  
   Install istio via helm [Istio Docs](https://istio.io/latest/docs/setup/install/helm/)
    ```shell
    helm repo add istio https://istio-release.storage.googleapis.com/charts
    helm repo update  
    kubectl create namespace istio-system
    helm install istio-base istio/base -n istio-system
    helm install istiod istio/istiod -n istio-system --wait
    ```

3. Redis https://www.containiq.com/post/deploy-redis-cluster-on-kubernetes

   ```shell
   kubectl create ns redis
   kubens redis
   kubectl apply -f redis-storage-class.yaml
   kubectl apply -f redis-presistent-volume.yaml
   kubectl apply -f redis-config-map.yaml
   kubectl apply -f redis-statefulset.yaml
   kubectl apply -f redis-service.yaml
   
   kubectl get sc,pv,configmap,pods,service
   
   NAME                                             PROVISIONER                    RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
   storageclass.storage.k8s.io/local-storage        kubernetes.io/no-provisioner   Delete          WaitForFirstConsumer   true                   13m
   storageclass.storage.k8s.io/standard (default)   k8s.io/minikube-hostpath       Delete          Immediate              false                  23m
   
   NAME                         CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      CLAIM   STORAGECLASS    REASON   AGE
   persistentvolume/local-pv1   1Gi        RWO            Retain           Available           local-storage            11m
   persistentvolume/local-pv2   1Gi        RWO            Retain           Available           local-storage            11m
   persistentvolume/local-pv3   2Gi        RWO            Retain           Available           local-storage            11m
   
   NAME                         DATA   AGE
   configmap/kube-root-ca.crt   1      17m
   configmap/redis-config       1      18s
   ```
   
   Redis CLI
   ```shell
   kubectl -n redis exec -it redis-1 -- sh
   redis-cli
   auth a-very-complex-password-here
   KEYS *
   ```

4. External Authorizer with OPA https://istio.io/latest/blog/2021/better-external-authz/#example-with-opa

   ```shell
   kubectl label ns redis istio-injection=enabled
   kubectl create secret generic opa-policy --from-file policy.rego
   kubectl apply -f httpbin-with-opa.yaml
   kubectl edit configmap istio -n istio-system
   kubectl apply -f httpbin-opa-authorization-policy.yaml
   ```
   configmap istio
   ```yaml
   apiVersion: v1
   data:
     mesh: |-
       # Add the following contents:
       extensionProviders:
       - name: "opa.local"
         envoyExtAuthzGrpc:
           service: "local-opa-grpc.local"
           port: "9191"
   ```

### Development

```shell
kubectl port-forward service/redis 6379:6379

export REDIS_PASSWORD a-very-complex-password-here
```

### Future Considerations

Use Redis HA helm chart https://artifacthub.io/packages/helm/dandydev-charts/redis-ha

