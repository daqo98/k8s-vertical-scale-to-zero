#!/usr/bin/env python3

import kopf
import kubernetes.config as k8s_config
import kubernetes.client as k8s_client
import requests
from pprint import pprint
import os

try:
    k8s_config.load_kube_config()
except k8s_config.ConfigException:
    k8s_config.load_incluster_config()

# create an instance of the API class
api_instance = k8s_client.CoreV1Api()
""" name = 'prime-numbers' # str | name of the Pod
namespace = 'namespace_example' # str | object name and auth scope, such as for teams and projects
body = NULL # object |  """
pretty = 'pretty_example' # str | If 'true', then the output is pretty printed. (optional)

try: 
    #api_response = api_instance.patch_namespaced_pod(name, namespace, body, pretty=pretty)
    #api_response = api_instance.read_namespaced_pod(name="prime-numbers", namespace="default", pretty=pretty)
    api_response = k8s_client.AppsV1Api().read_namespaced_deployment(namespace="default", name="prime-numbers", pretty=pretty)
    pprint(api_response)
except k8s_client.rest.ApiException as e:
    print("Exception when calling CoreV1Api->patch_namespaced_pod: %s\n" % e)


#api_instance.read_namespaced_deployment(namespace="default",name=name)
