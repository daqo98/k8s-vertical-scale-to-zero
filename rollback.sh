#!/bin/bash

# Deleting old resources
read -p "Choose the configuration to delete:" answer
echo "1. App"
echo "2. App + HPA"
echo "3. App + VerSca20"
echo "4. App + VerSca20 + HPA"

if [[ $answer = 1 ]]; then
    kubectl delete -f "app_alone"
elif [[ $answer = 2 ]]; then
    kubectl delete -f "app_and_HPA"
elif [[ $answer = 3 ]]; then
    kubectl delete -f "app_and_versca20"
elif [[ $answer = 4 ]]; then
    kubectl delete -f "app_and_versca20_and_HPA"
else
     echo "Run again the script and choose one of the options"
fi

kubectl delete -f "config/storage"
kubectl delete -f "config/permissions"