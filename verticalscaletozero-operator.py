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
pretty = 'pretty_example' # str | If 'true', then the output is pretty printed. (optional)


def handlingException(apiCall):
    try: 
        #api_response = api_instance.patch_namespaced_pod(name, namespace, body, pretty=pretty)
        podName = api_instance.list_namespaced_pod(namespace="default", pretty=pretty).items[0].metadata.name
        api_response = api_instance.read_namespaced_pod(name=podName, namespace="default", pretty=pretty)
        #api_response = k8s_client.AppsV1Api().read_namespaced_deployment(namespace="default", name="prime-numbers", pretty=pretty) # works
        return(api_response)
    except k8s_client.rest.ApiException as e:
        print("Exception when calling CoreV1Api->patch_namespaced_pod: %s\n" % e)

def update_resources_pod(namespace, name, new_data):
    api_instance = k8s_client.CoreV1Api()
    return api_instance.patch_namespaced_pod(name=name, namespace=namespace, body=new_data)


def modifyPodResources(pod, cpu_req, cpu_lim, mem_req, mem_lim):
    pod.spec.containers[0].resources = {'claims': None,
                                        'limits': {'cpu': '%sm' % cpu_lim,
                                                   'memory': '%sMi' % mem_lim},
                                        'requests': {'cpu': '%sm' % cpu_req,
                                                     'memory': '%sMi' % mem_req}}
    return pod

def verticalScale(cpu_req, cpu_lim, mem_req, mem_lim):
    namespace = "default"
    podName = api_instance.list_namespaced_pod(namespace="default", pretty=pretty).items[0].metadata.name
    api_response = api_instance.read_namespaced_pod_status(name=podName, namespace="default", pretty=pretty)
    new_data = modifyPodResources(api_response, cpu_req, cpu_lim, mem_req, mem_lim)
    pprint(new_data)
    update_resources_pod(namespace,podName,new_data) 

verticalScale(2, 2, 2, 2)