#!/bin/bash

# Deleting old resources
kubectl delete -f "config/crd/bases"
kubectl delete -f "config/permissions"
kubectl delete -f "config/storage"
kubectl delete -f "application/deployment.yaml"
kubectl delete -f "application/service.yaml"