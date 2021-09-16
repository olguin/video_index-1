import requests
import json
import time
import os
import traceback
import logging

def getSearchServiceKey(token, searchServiceName,apiVersion):
    subscriptionId = os.getenv("SUBSCRIPTION")
    resourceGroupName =  os.getenv("GROUP")

    getKeysURL=f"https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Search/searchServices/{searchServiceName}/listAdminKeys?api-version={apiVersion}"
    headers= {"Authorization":f"Bearer {token}", "Content-Type": "application/json"}
    res = requests.post(getKeysURL,headers=headers)
    searchServiceKeys = json.loads(res.content.decode("utf-8"))
    if("primaryKey" in searchServiceKeys):
        return searchServiceKeys["primaryKey"]
    else:
        raise Exception(searchServiceKeys)


def getToken():
    clientId = os.getenv("APP_ID")
    tenant = os.getenv("TENANT")
    password = os.getenv("PASSWORD")
    data = {
        "grant_type":"client_credentials",
        "client_id": clientId,
        "client_secret": password,
        "resource": "https://management.azure.com/"
    }
    url=f"https://login.microsoftonline.com/{tenant}/oauth2/token"
    res = requests.post(url,data=data)
    response=json.loads(res.content.decode("utf-8"))
    return response['access_token']


def runIndexer():
    token = getToken()

    prefix =  os.getenv("PREFIX")
    container = os.getenv("CONTAINER")

    serviceName = f'{prefix}ss'
    searchServiceKey = getSearchServiceKey(token,serviceName, "2020-08-01" )
    indexerName=f"{container}-irn"
    runIndexerURL=f"https://{serviceName}.search.windows.net/indexers/{indexerName}/run?api-version=2020-06-30"
    res = requests.post(runIndexerURL,headers={"api-key":searchServiceKey})
    return res

def findRecord(token,searchServiceKey, url):
    prefix =  os.getenv("PREFIX")
    container = os.getenv("CONTAINER")

    serviceName = f'{prefix}ss'
    indexName=f"{container}-in"
    findRecordURL =f"https://{serviceName}.search.windows.net/indexes/{indexName}/docs/search?api-version=2020-06-30"
    data = {
        "search": f"path: \"{url}\"",
        "queryType": "full"
    }
    headers= {"api-key":searchServiceKey, "Content-Type": "application/json"}
    res = requests.post(findRecordURL ,headers=headers,data=json.dumps(data))
    record = json.loads(res.content.decode("utf-8"))
    return record["value"][0]["id"]

def deleteRecord(token,searchServiceKey, recordId):
    prefix =  os.getenv("PREFIX")
    container = os.getenv("CONTAINER")

    serviceName = f'{prefix}ss'
    indexName=f"{container}-in"
    deleteRecordURL =f"https://{serviceName}.search.windows.net/indexes/{indexName}/docs/index?api-version=2020-06-30"
    data = {
        "value": [
            {
            "@search.action": "delete",  
            "id": recordId
            }
        ]
    }
    headers= {"api-key":searchServiceKey, "Content-Type": "application/json"}
    res = requests.post(deleteRecordURL ,headers=headers,data=json.dumps(data))
    record = json.loads(res.content.decode("utf-8"))
    return record


def deleteVideo(url):
    try:
        token = getToken()
        prefix =  os.getenv("PREFIX")
        serviceName = f'{prefix}ss'
        searchServiceKey = getSearchServiceKey(token,serviceName, "2020-08-01" )
        recordId = findRecord(token,searchServiceKey,url)
        res = deleteRecord(token,searchServiceKey,recordId)
        logging.info(f"deleted index data for video {url} {res}")
    except Exception as e:
        logging.error(traceback.format_exc())
        logging.error(e)


