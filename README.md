![imagen](https://github.com/daqo98/k8s-vertical-scale-to-zero/assets/68958822/4cb7ae72-ec96-4fe2-95d1-c1caca4b9419)# k8s-vertical-scale-to-zero
Sidecar proxy with vertical scaling to/from zero in Kubernetes implemented in Python. By making use of the sidecar pattern, we will deploy an app and a proxy in two different containers but in the same pod. The requests directed to the pod will be received by the proxy which in turn forwards them to the app but also decides whether to vertical scale the pod or not.

## Logic behind the proxy w/ vertical scaling:
- **Vertical scaling to zero:** The container resources are downscaled to zero if more than X seconds have elapsed since the last request was forwarded to the app (e.g. prime-numbers). This time is fixed in the `TIME` variable (currently hardcoded).
- **Vertical scaling from zero:** Infinite loop (a while) that resizes the container and every 5 seconds checks if the container is ready before forwarding the request to the prime-numbers app.

## Pre-requisites
It is required to have Kubectl v1.27 and a recent version of Kind installed. Personally, I'm using:
- kind v0.17.0 go1.19.2 windows/amd64
- kubectl client version v1.27.4 windows/amd64

## How to test it in Kubernetes?
 1. Create the Kubernetes cluster: `kind create cluster --name k8s-playground --image=kindest/node:v1.27.3 --config "config/cluster-conf/development-cluster.yaml"`
 2. Install the RBACs: `kubectl apply -f config/permissions`
 3. Deploy the App + Proxy w/. vertical scaling: `kubectl apply -f application/deployment.yaml`
 4. Create service of the app: `kubectl apply -f application/service.yaml`
 5. Port-forwarding to service port: `kubectl port-forward service/prime-numbers 80:80`
 6. Try a request: `curl http://localhost:80/prime/12`
 7. Delete cluster: `kind delete cluster --name k8s-playground`

## How to test it locally?
Let's use the `pipenv` module to create a virtual environment, so first install it with `pip install pipenv`.
 1. Install the dependencies of our venv: `pipenv install`
 2. Run the virtual environment: `pipenv shell`
 3. Run the proxy: `python http_scale2zero.py`
 4. In other tab, follow the steps described in [How to test it in Kubernetes?](https://github.com/daqo98/k8s-vertical-scale-to-zero/tree/main#how-to-test-it-in-kubernetes) but since we're going to use our local proxy and not the one deployed in Kubernetes, do port-forward of the app not the proxy i.e. port 8080:8080 `kubectl port-forward pods/<pod-name> 8080:8080`
 5. In other tab send the requests `curl http://localhost:80/prime/12`. Our local proxy will forward the request to `localhost:8080` which forwards the request to the prime-numbers app running in Kubernetes.

## Interesting links:
1. [Sidecar deployment](https://iximiuz.com/en/posts/service-proxy-pod-sidecar-oh-my/)
2. [Python proxy server](https://ledinhcuong99.medium.com/build-simple-proxy-server-in-python-365bda288a52)
3. [K8s Core API](https://github.com/salsify/k8s-python/blob/master/kubernetes/docs/CoreV1Api.md)
4. [K8s Apps API](https://github.com/salsify/k8s-python/blob/master/kubernetes/docs/AppsV1Api.md)

### Vertical scaling-related info
5. [Container restart policy](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#restart-policy)
6. [Resize CPU and Memory Resources assigned to Containers](https://kubernetes.io/docs/tasks/configure-pod-container/resize-container-resources/)
7. [Kubernetes 1.27: In-place Resource Resize for Kubernetes Pods (alpha)](https://kubernetes.io/blog/2023/05/12/in-place-pod-resize-alpha/)
