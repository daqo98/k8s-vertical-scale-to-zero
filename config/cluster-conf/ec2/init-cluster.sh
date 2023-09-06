#!/bin/bash

# Init kubeAdm cluster
sudo kubeadm init --config=$HOME/k8s-vertical-scale-to-zero/config/cluster-conf/ec2/kubeadm-cluster.yaml
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# Install Flannel as CNI add-on
kubectl apply -f ~/k8s-vertical-scale-to-zero/config/cluster-conf/ec2/kube-flannel.yml
sudo systemctl restart containerd.service

# Verify node is running
kubectl get nodes -o wide
