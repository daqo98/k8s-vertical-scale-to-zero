#!/bin/bash

# Create kind cluster with its config
# kind create cluster --name k8s-playground --image=kindest/node:v1.27.3@sha256:3966ac761ae0136263ffdb6cfd4db23ef8a83cba8a463690e98317add2c9ba72 --config "config/cluster-conf/development-cluster.yaml"

# Deleting old resources
kubectl delete -f "config/crd/bases"
kubectl delete -f "config/permissions"
kubectl delete -f "config/storage"
kubectl delete -f "application/deployment.yaml"
kubectl delete -f "application/service.yaml"

# Install Custom Resource Definitions (CRDs)
kubectl apply -f "config/crd/bases"

# Install RBACs
kubectl apply -f "config/permissions"

# Install PV and PVC to store .csv of metrics-logger
kubectl apply -f "config/storage"

# Remove taint on the master or control-plane nodes to schedule pods on the Kubernetes control-plane node:
kubectl taint nodes --all node-role.kubernetes.io/master-
kubectl taint nodes --all  node-role.kubernetes.io/control-plane-

# Deploy app
kubectl apply -f "application/deployment.yaml"
kubectl apply -f "application/service.yaml"

kubectl port-forward service/prime-numbers 8080:80
# kubectl port-forward service/http-metrics 8000:8000
# Try a request: curl http://localhost:8080/prime/12 or curl http://<Node's_Public_IP>:31512/prime/12
## Locust workload: 
# cd $HOME/versca20
# pipenv install
# pipenv shell
# locust -f ~/versca20/locust_workload.py --headless --host=http://localhost:8080/prime/12