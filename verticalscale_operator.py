#!/usr/bin/env python3
import kopf
import kubernetes.config as k8s_config
import kubernetes.client as k8s_client
import logging
import os
from pprint import pprint
import requests

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

logger = logging.getLogger("vertical_scale")

def handlingException(api_call):
    try: 
        return(api_call)
    except k8s_client.rest.ApiException as e:
        logger.error("Exception: %s\n" % e)

def updateResourcesPod(pod_name, new_pod_data):
    return api_core_instance.patch_namespaced_pod(name=pod_name, namespace=namespace, body=new_pod_data)


def createDictContainerResources(pod, cpu_req, cpu_lim, mem_req, mem_lim):
    #TODO: Search of container index given app name. Not thinking that it is going to be always the container 0
    pod.spec.containers[0].resources = {'limits': {'cpu': '%s' % cpu_lim,
                                                   'memory': '%s' % mem_lim},
                                        'requests': {'cpu': '%s' % cpu_req,
                                                     'memory': '%s' % mem_req}}
    return pod

def getPod():
    """
    Returns: First pod in the namespace specified in the global variable as a V1Pod object
    """
    return api_core_instance.list_namespaced_pod(namespace=namespace, pretty=pretty).items[0]

def verticalScale(cpu_req, cpu_lim, mem_req, mem_lim):
    """
    Perform vertical scaling of the first container of the first pod in the global variable namespace
    Args:
        cpu_req: cpu request
        cpu_lim: cpu limit
        mem_req: memory request
        mem_lim: memory limit
    Returns:
        Nothing
    """
    pod = getPod()
    pod_name = pod.metadata.name
    dict_container_resources = createDictContainerResources(pod, cpu_req, cpu_lim, mem_req, mem_lim)
    #pprint(new_data)
    updateResourcesPod(pod_name,dict_container_resources)
    logger.info("App container resources modified")
    logger.info("New resources: cpu_req: %s, cpu_lim: %s, mem_req: %s, and mem_lim: %s" % (cpu_req, cpu_lim, mem_req, mem_lim))

def getContainersPort():
    pod = getPod()
    port = pod.spec.containers[0].ports[0].container_port
    logger.info(("Container port is: %d" % (port)))
    return port

def deletePod():
    # TODO: Not used so far. Maybe is useful in the future.
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

def isInZeroState():
    [cpu_req, cpu_lim, mem_req, mem_lim] = getContainerResources(getPod())
    if (cpu_req =='1m' and cpu_lim == '1m' and mem_req == '1Mi' and mem_lim == "1Mi"):
        logger.debug("in Zero state")
        return True
    else: 
        logger.debug("NOT in Zero state")
        return False

def isContainerReady():
    pod = getPod()
    return pod.status.container_statuses[0].ready

def getDefaultConfigContainer():
    deployment_name = "prime-numbers"
    deployment = api_apps_instance.read_namespaced_deployment(deployment_name, namespace, pretty=pretty)
    pod = deployment.spec.template
    return getContainerResources(pod)
