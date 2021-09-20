import os
import json
import subprocess
import time
import logging
import requests
import datetime
import hmac
import hashlib
import base64
from library.video_index_creator import *

def enable_skip_videos(storage_account_name,storage_account_key ):
    api_version = '2018-03-28'
    request_time = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    data = "<StorageServiceProperties><DefaultServiceVersion>2012-02-12</DefaultServiceVersion></StorageServiceProperties>"
    content_len = str(len(data))

    string_params = {
        'verb': 'PUT',
        'Content-Encoding': '',
        'Content-Language': '',
        'Content-Length': content_len,
        'Content-MD5': '',
        'Content-Type': 'application/xml',
        'Date': '',
        'If-Modified-Since': '',
        'If-Match': '',
        'If-None-Match': '',
        'If-Unmodified-Since': '',
        'Range': '',
        'CanonicalizedHeaders': 'x-ms-date:' + request_time + '\nx-ms-version:' + api_version + '\n',
        'CanonicalizedResource': '/' + storage_account_name + '/\ncomp:properties\nrestype:service'
    }

    string_to_sign = (string_params['verb'] + '\n'
                    + string_params['Content-Encoding'] + '\n'
                    + string_params['Content-Language'] + '\n'
                    + string_params['Content-Length'] + '\n'
                    + string_params['Content-MD5'] + '\n'
                    + string_params['Content-Type'] + '\n'
                    + string_params['Date'] + '\n'
                    + string_params['If-Modified-Since'] + '\n'
                    + string_params['If-Match'] + '\n'
                    + string_params['If-None-Match'] + '\n'
                    + string_params['If-Unmodified-Since'] + '\n'
                    + string_params['Range'] + '\n'
                    + string_params['CanonicalizedHeaders']
                    + string_params['CanonicalizedResource'])

    signed_string = base64.b64encode(hmac.new(base64.b64decode(storage_account_key), msg=string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()).decode()

    headers = {
        'x-ms-date' : request_time,
        'x-ms-version' : api_version,
        'Content-Type': 'application/xml',
        'Content-Length': content_len,
        'Authorization' : ('SharedKey ' + storage_account_name + ':' + signed_string)
    }

    url = ('https://' + storage_account_name + '.blob.core.windows.net/?restype=service&comp=properties')
    data = "<StorageServiceProperties><DefaultServiceVersion>2012-02-12</DefaultServiceVersion></StorageServiceProperties>"


    r = requests.put(url, headers = headers, data=data)

    return r

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
    storageAccount = container_to_index_info["storageAccount"]
    container=container_to_index_info["container"]
    pwd = os.getcwd()

    appId = security_info["appId"]
    password = security_info["password"]
    tenant = security_info["tenant"]
    build_bicep_command = f"deployment sub create -f {pwd}/infrastructure/main.bicep --subscription {subscriptionId} --parameters prefix={prefix} location={location} appid={appId} password={password} tenant={tenant} storage_account={storageAccount} container={container} --location {location} --query properties.outputs"
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

    enable_skip_videos(container_to_index_info["storageAccount"], container_to_index_info["storageAccountKey"])

    createCompleteIndex(token, container_to_index_info,searchService,resourceGroup,functionApp)


def getDvConfig():


    security_info = { 
        "appId": "26a41b49-d23f-4524-8ae7-7f6222919847",
        "password": "WFTKC_fNkwq6Nh.Yylg-es2yilXLWziVsw",
        "tenant": "639be87d-9250-4b32-afb6-3ec84932b34b"
    }

    container_to_index_info = {
        "subscriptionId": "898225fb-0fa0-4180-82b0-c3c103ade9a4",
        "storageAccount": "developmentsc",
        "storageAccountGroup": "development-rg",
        "container": "development-container",
        "storageAccountKey": 'hUOM+L7VbCfqbUsmrBGsDgb/XvQhT9Ok+LSvlr0NPUZ+xzoS9RKwMQlVRmDvobFC6A2VohcZumCp/XjJOXDlYg=='
    }

    prefix="dtdv"
    return prefix, container_to_index_info, security_info

def getDemoConfig():
    security_info = { 
        "appId": "26a41b49-d23f-4524-8ae7-7f6222919847",
        "password": "WFTKC_fNkwq6Nh.Yylg-es2yilXLWziVsw",
        "tenant": "639be87d-9250-4b32-afb6-3ec84932b34b"
    }


    container_to_index_info = {
        "subscriptionId": "898225fb-0fa0-4180-82b0-c3c103ade9a4",
        "storageAccount": "demosc",
        "storageAccountGroup": "demo-rg",
        "container": "demo-container",
        "storageAccountKey": 'ueblVx4vh0U8qMMMPXOK6mq6auwKya0tEFsS1DU6UoRh1HDMMRlG5hyqT2XY1IyC8FiADfRcDbjhk7V2idBEoA=='
    }

    prefix="dtdemo"
    return prefix, container_to_index_info, security_info

prefix, container_to_index_info, security_info = getDvConfig()
print(f"deploying to {prefix}")
location="eastus"
buildInfrastructure(security_info, container_to_index_info, prefix, location)

