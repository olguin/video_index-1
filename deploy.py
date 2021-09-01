import os
import json
import subprocess
import time
import logging
from library.video_index_creator import *

def run_az_command(command):
    print(command)
    command = f"az {command}"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, cwd="functions")
    output, error = process.communicate()
    if(error == None):
        return json.loads(output)
    else:
        logging.error(f'Error running az {error} {output}')
        raise Exception(error)

def deployFunctions(functionApp):
    command = f"func azure functionapp publish {functionApp} --python"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, cwd="functions")
    output, error = process.communicate()
    if(error != None):
        logging.error(f'Error deploying functions {error} {output}')
        raise Exception(error)

def buildInfrastructure(security_info, container_to_index_info, prefix, location):
    subscriptionId = container_to_index_info["subscriptionId"]
    pwd = os.getcwd()

    build_bicep_command = f"deployment sub create -f {pwd}/infrastructure/main.bicep --subscription {subscriptionId} --parameters prefix={prefix} location={location} --location {location} --query properties.outputs"
    result_dict = run_az_command(build_bicep_command)

    searchService = result_dict["searchService"]["value"]
    functionApp = result_dict["videoIndexFunctionApp"]["value"]
    resourceGroup = result_dict["resourceGroup"]["value"]
    print(searchService)
    print(functionApp)
    print(resourceGroup)
    token = getToken(security_info["appId"], security_info["password"], security_info["tenant"])["access_token"]
    while not (checkFunctionExists(token, subscriptionId,resourceGroup,functionApp)):
        print("waiting for function app creation")
        time.sleep(5)

    #deployFunctions(functionApp)

    createCompleteIndex(token, container_to_index_info,searchService,resourceGroup,functionApp)


#security_info = {
#    "appId": "26a41b49-d23f-4524-8ae7-7f6222919847",
#    "password": "Hn~6QCdRy9pyRFqxNUul.SKIqCrEXG.Uq8",
#    "tenant": "639be87d-9250-4b32-afb6-3ec84932b34b"
#}

security_info = {
  "appId": "26a41b49-d23f-4524-8ae7-7f6222919847",
  "password": "Iq-0pCY1CbrwgD_710_qEeMQqe5UmrC4BQ",
  "tenant": "639be87d-9250-4b32-afb6-3ec84932b34b"
}

#container_to_index_info = {
#    "subscriptionId": "5b541c4d-ec9c-4e4e-a6d4-e95ce20e55ef",
#    "storageAccount": "videosearch",
#    "storageAccountGroup": "video-search-rg",
#    "container": "videosearchcontainer",
#}

container_to_index_info = {
    "subscriptionId": "898225fb-0fa0-4180-82b0-c3c103ade9a4",
    "storageAccount": "developmentsc",
    "storageAccountGroup": "development-rg",
    "container": "development-container",
}


prefix="dtdv"
location="eastus"
buildInfrastructure(security_info, container_to_index_info, prefix, location)

