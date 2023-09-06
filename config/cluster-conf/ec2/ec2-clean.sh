#!/bin/bash

# Drain node
kubectl drain $hostname --ignore-daemonsets --delete-emptydir-data --force

read -p "Is this the master node? [y/n]" answer
if [[ $answer = y ]] ; then
  sudo kubeadm reset --cri-socket=unix:///var/run/containerd/containerd.sock
  #sudo kubeadm reset --cri-socket=unix:///var/run/cri-dockerd.sock
fi

sudo rm -rf /etc/kubernetes /var/lib/kubelet /var/lib/etcd /etc/cni/net.d
sudo kill -9 $(ps aux | grep kubelet | grep -v grep| awk '{print $2}')
sudo iptables
sudo iptables -t nat -F
sudo iptables -t mangle -F
sudo iptables -X