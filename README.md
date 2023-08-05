# k8s-vertical-scale-to-zero
Sidecar proxy with vertical scaling to/from zero in Kubernetes implemented in Python. By making use of the sidecar pattern, we will deploy an app and a proxy in two different containers but in the same pod. The requests directed to the pod will be received by the proxy which in turn forwards them to the app but also decides whether to vertical scale the pod or not.

## How to get the project to run?

 1. Create the Kubernetes cluster: `kind create cluster --name k8s-playground --image=kindest/node:v1.27.3 --config "config/cluster-conf/development-cluster.yaml"`
 2. Install the RBACs: `kubectl apply -f config/permissions`
 3. Deploy the App + Proxy w/. vertical scaling: `kubectl apply -f application/deployment.yaml`
 4. Create service of the app: `kubectl apply -f application/service.yaml`
 5. Port-forwarding to service port: `kubectl port-forward service/prime-numbers 80:80`
 6. Try a request: `curl http://localhost:80/prime/12`

## Interesting links:

Sidecar deployment: https://iximiuz.com/en/posts/service-proxy-pod-sidecar-oh-my/

Python proxy server: https://ledinhcuong99.medium.com/build-simple-proxy-server-in-python-365bda288a52

Kubernetes API python: https://github.com/salsify/k8s-python/blob/master/kubernetes/docs/CoreV1Api.md
