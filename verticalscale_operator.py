#!/usr/bin/env python3

import kopf
import kubernetes.config as k8s_config
import kubernetes.client as k8s_client
import requests
from pprint import pprint
import os

# Load Kubernetes config file
try:
    k8s_config.load_kube_config()
except k8s_config.ConfigException:
    k8s_config.load_incluster_config()

# Create an instance of the API class
api_core_instance = k8s_client.CoreV1Api()
api_apps_instance = k8s_client.AppsV1Api()
pretty = 'pretty_example'
namespace = "default"

def handlingException(api_call):
    try: 
        return(api_call)
    except k8s_client.rest.ApiException as e:
        print("Exception: %s\n" % e)

def update_resources_pod(name, new_data):
    return api_core_instance.patch_namespaced_pod(name=name, namespace=namespace, body=new_data)


def modifyContainerResources(pod, cpu_req, cpu_lim, mem_req, mem_lim):
    #TODO: Search of container index given app name. Not thinking that it is going to be always the container 0
    pod.spec.containers[0].resources = {'claims': None,
                                        'limits': {'cpu': '%s' % cpu_lim,
                                                   'memory': '%s' % mem_lim},
                                        'requests': {'cpu': '%s' % cpu_req,
                                                     'memory': '%s' % mem_req}}
    return pod

def getPod():
    return api_core_instance.list_namespaced_pod(namespace=namespace, pretty=pretty).items[0]

def verticalScale(cpu_req, cpu_lim, mem_req, mem_lim):
    pod = getPod()
    pod_name = pod.metadata.name
    new_data = modifyContainerResources(pod, cpu_req, cpu_lim, mem_req, mem_lim)
    #pprint(new_data)
    update_resources_pod(pod_name,new_data)
    print("App container resources modified")
    print("New resources: cpu_req: %s, cpu_lim: %s, mem_req: %s, and mem_lim: %s" % (cpu_req, cpu_lim, mem_req, mem_lim))

def getContainersPort():
    pod = getPod()
    port = pod.spec.containers[0].ports[0].container_port
    print("Container port is: " + str(port))
    return port

def deletePod():
    pod = getPod()
    podName = pod.metadata.name
    api_core_instance.delete_namespaced_pod(name=podName, namespace=namespace, body=k8s_client.V1DeleteOptions(), pretty=pretty)

def getContainerResources(pod):
    pod_resources = pod.spec.containers[0].resources
    cpu_req = pod_resources.requests['cpu']
    cpu_lim = pod_resources.limits['cpu']
    mem_req = pod_resources.requests['memory']
    mem_lim = pod_resources.limits['memory']
    resources = [cpu_req, cpu_lim, mem_req, mem_lim]
    return resources

def verifyInZeroState():
    [cpu_req, cpu_lim, mem_req, mem_lim] = getContainerResources(getPod())
    if (cpu_req =='1m' and cpu_lim == '1m' and mem_req == '1Mi' and mem_lim == "1Mi"):
        print("in Zero state")
        return True
    else: 
        print("NOT in Zero state")
        return False

def isContainerReady():
    pod = getPod()
    return pod.status.container_statuses[0].ready

def getDefaultConfigContainer():
    deployment_name = "prime-numbers"
    deployment = api_apps_instance.read_namespaced_deployment(deployment_name, namespace, pretty=pretty)
    pod = deployment.spec.template
    return getContainerResources(pod)



#verticalScale(10, 10, 10, 10)
#verticalScale(1, 1, 1, 1)

#verifyInZeroState()

#pprint(api_core_instance.list_namespaced_pod(namespace="default", pretty=pretty).items[0]) # Pod's info
#print(isContainerReady())
#print(getDefaultConfigContainer())
