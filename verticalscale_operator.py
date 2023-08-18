#!/usr/bin/env python3
import kopf
import kubernetes.config as k8s_config
import kubernetes.client as k8s_client
from kubernetes.client.rest import ApiException
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
# TODO: Get App name either from a OS/env variable or using Kopf to detect updates on deployments and update the global vars
namespace = "default"
deployment_name = "prime-numbers"

logger = logging.getLogger("vertical_scale")

def handlingException(api_call):
    try: 
        return(api_call)
    except ApiException as e:
        logger.error("Exception: %s\n" % e)

def updateResourcesPod(pod_name, new_pod_data):
    return api_core_instance.patch_namespaced_pod(name=pod_name, namespace=namespace, body=new_pod_data)

def updateStatusResourcesPod(pod_name, new_pod_data):
    api_response = api_core_instance.patch_namespaced_pod_status(name=pod_name, namespace=namespace, body=new_pod_data)
    #pprint(api_response)
    return api_response


def createDictContainerResources(container_idx, cpu_req, cpu_lim, mem_req, mem_lim):
    #TODO: Search of container index given app name. Not thinking that it is going to be always the container 0
    dict_spec_container_resources = [{
                                    'op': 'replace', 'path': f'/spec/containers/{container_idx}/resources',
                                    'value': {
                                                'limits': {'cpu': '%s' % cpu_lim,'memory': '%s' % mem_lim},
                                                'requests': {'cpu': '%s' % cpu_req,'memory': '%s' % mem_req}
                                            }
                                    }]
    
    return dict_spec_container_resources


def createDictContainerStatusResources(container_status_idx, cpu_req, cpu_lim, mem_req, mem_lim):
    #TODO: Search of container index given app name. Not thinking that it is going to be always the container 0
    """ dict_status_container_resources = [{
                                    'op': 'replace', 'path': f'/status/containerStatuses/{container_status_idx}',
                                    'value': {
                                                'allocatedResources': {'cpu': '%s' % cpu_req,'memory': '%s' % mem_req},
                                                'resources': {'limits': {'cpu': '%s' % cpu_lim,'memory': '%s' % mem_lim},
                                                            'requests': {'cpu': '%s' % cpu_req,'memory': '%s' % mem_req}
                                                            }
                                                }}] """

    dict_status_container_resources = [{
                                    'op': 'replace', 'path': f'/status/containerStatuses/{container_status_idx}/allocatedResources',
                                    'value': {
                                                'cpu': '%s' % cpu_req,'memory': '%s' % mem_req,
                                                
                                                }}]

    return dict_status_container_resources


def getPod():
    """
    Returns: First pod in the namespace specified in the global variable as a V1Pod object
    """
    pods = api_core_instance.list_namespaced_pod(namespace=namespace, pretty=pretty)
    pod_idx = getPodIdx(pods)
    return pods.items[pod_idx]

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
    container_idx = getContainerIdx(pod, getAppName())
    # Update pod's spec
    dict_container_resources = createDictContainerResources(container_idx, cpu_req, cpu_lim, mem_req, mem_lim)
    updateResourcesPod(pod_name, dict_container_resources)
    # Update pod's status
    #container_status_idx = getContainerStatusIdx(pod, getAppName()) #TODO
    #dict_container_status_resources = createDictContainerStatusResources(container_status_idx, cpu_req, cpu_lim, mem_req, mem_lim)
    #updateStatusResourcesPod(pod_name,dict_container_status_resources)
    logger.info("App container resources modified")
    logger.info("New resources: cpu_req: %s, cpu_lim: %s, mem_req: %s, and mem_lim: %s" % (cpu_req, cpu_lim, mem_req, mem_lim))

def getContainersPort():
    pod = getPod()
    container_idx = getContainerIdx(pod, getAppName())
    port = pod.spec.containers[container_idx].ports[0].container_port
    logger.info(("Container port is: %d" % (port)))
    return port

def deletePod():
    # TODO: Not used so far. Maybe is useful in the future.
    pod = getPod()
    podName = pod.metadata.name
    api_core_instance.delete_namespaced_pod(name=podName, namespace=namespace, body=k8s_client.V1DeleteOptions(), pretty=pretty)

def getContainerResources(pod):
    container_idx = getContainerIdx(pod, getAppName())
    pod_resources = pod.spec.containers[container_idx].resources
    cpu_req = pod_resources.requests['cpu']
    cpu_lim = pod_resources.limits['cpu']
    mem_req = pod_resources.requests['memory']
    mem_lim = pod_resources.limits['memory']
    resources = [cpu_req, cpu_lim, mem_req, mem_lim]
    return resources

def isInZeroState(zeroStateDef):
    [cpu_req, cpu_lim, mem_req, mem_lim] = getContainerResources(getPod())
    logger.debug("cpu_req is:" + zeroStateDef.cpu_req)
    logger.debug("cpu_lim is:" + zeroStateDef.cpu_lim)
    logger.debug("mem_req is:" + zeroStateDef.mem_req)
    logger.debug("mem_lim is:" + zeroStateDef.mem_lim)
    if (cpu_req == zeroStateDef.cpu_req and cpu_lim == zeroStateDef.cpu_lim and mem_req == zeroStateDef.mem_req and mem_lim == zeroStateDef.mem_lim):
        logger.debug("in Zero state")
        return True
    else: 
        logger.debug("NOT in Zero state")
        return False

def isContainerReady():
    container_status = getContainerStatus()
    return container_status.ready

def getDefaultConfigContainer():
    deployment = api_apps_instance.read_namespaced_deployment(deployment_name, namespace, pretty=pretty)
    pod = deployment.spec.template
    return getContainerResources(pod)

def getContainerStatus():
    pod = getPod()
    container_status_idx = getContainerStatusIdx(pod, getAppName())
    return pod.status.container_statuses[container_status_idx]

def getAppName():
    # TODO: Get App name either from a OS/env variable or using Kopf to detect updates on deployments and update the global vars
    deployment = api_apps_instance.read_namespaced_deployment(deployment_name, namespace, pretty=pretty)
    app_name = deployment.spec.template.metadata.labels["app"]
    return app_name

def getContainerIdx(pod, container_name):
    for idx, container in enumerate(pod.spec.containers):
        if container.name == container_name:
            container_idx = idx
            break
    return container_idx

def getContainerStatusIdx(pod, container_name):
    for idx, container in enumerate(pod.status.container_statuses):
        if container.name == container_name:
            container_status_idx = idx
            break
    return container_status_idx

def getContainerRestartCount():
    container_status = getContainerStatus()
    return container_status.restart_count

def getPodIdx(pods):
    for idx, pod in enumerate(pods.items):
        if deployment_name in pod.metadata.name:
            pod_idx = idx
            break
    return pod_idx
    
#pprint(getPod()) # Pod's info

#verticalScale("250m", "250m", "128Mi", "128Mi")
#verticalScale("1m", "1m", "10Mi", "10Mi") # Seems to be the minimum acceptable
#verticalScale("10m", "10m", "10Mi", "10Mi") # Pablo's threshold
#verticalScale("5m", "5m", "5Mi", "5Mi")
#verticalScale("1m", "1m", "5Mi", "5Mi")
#verticalScale("1m", "1m", "1Mi", "1Mi")
#pprint(getContainerResources(getPod()))
#print("STATUSSSSSS")
#pprint(getContainerStatus()) # Container's status