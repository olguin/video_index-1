import logging
import grequests
import requests
import json
import time
import os
import xml.etree.ElementTree as ET
import threading
import queue
import re
import logging
from shared_code.video_indexer_tools import processVideo as processVideo
from shared_code.config_reader import Configuration as Configuration 

import azure.functions as func

def getSearchServiceKeys(token, subscriptionId, resourceGroupName, searchServiceName,apiVersion):
    getKeysURL=f"https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Search/searchServices/{searchServiceName}/listAdminKeys?api-version={apiVersion}"
    headers= {"Authorization":f"Bearer {token}", "Content-Type": "application/json"}
    res = requests.post(getKeysURL,headers=headers)
    return json.loads(res.content.decode("utf-8"))

def getToken(clientId,clientPassword,tenant):
    data = {
        "grant_type":"client_credentials",
        "client_id": clientId,
        "client_secret": clientPassword,
        "resource": "https://management.azure.com/"
    }
    url=f"https://login.microsoftonline.com/{tenant}/oauth2/token"
    res = requests.post(url,data=data)
    response=json.loads(res.content.decode("utf-8"))
    return response


def runIndexer():
    clientId = os.getenv("APP_ID")
    tenant = os.getenv("TENANT")
    password = os.getenv("PASSWORD")
    token = getToken(clientId, password, tenant)['access_token']

    prefix =  os.getenv("PREFIX")
    resourceGroup =  os.getenv("GROUP")
    subscriptionId = os.getenv("SUBSCRIPTION")
    container = os.getenv("CONTAINER")

    serviceName = f'{prefix}ss'
    searchServiceKeys = getSearchServiceKeys(token,subscriptionId ,resourceGroup, serviceName, "2020-08-01" )
    if("primaryKey" in searchServiceKeys):
        searchServiceKey = searchServiceKeys["primaryKey"]
    else:
        raise Exception(searchServiceKeys)

    indexerName=f"{container}-irn"
    runIndexerURL=f"https://{serviceName}.search.windows.net/indexers/{indexerName}/run?api-version=2020-06-30"
    res = requests.post(runIndexerURL,headers={"api-key":searchServiceKey})
    return res

def deleteVideo(url):
    None

def main(event: func.EventGridEvent):

    data = event.get_json()
    url = data['url']
    action = data['api']
    logging.info(f'Action {action}')
    logging.info(f'Processing {url}')
    if(action == "DeleteBlob"):
        deleteVideo(url)
    else:
        processVideo(url,Configuration(os.path.dirname(url)), False)
    result = runIndexer()
    logging.info(f"indexer result {result}")
