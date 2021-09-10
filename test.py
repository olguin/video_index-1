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

def listSC(token):
    getKeysURL=f"https://management.azure.com/providers/Microsoft.Web/sourcecontrols?api-version=2019-08-01"
    headers= {"Authorization":f"Bearer {token}", "Content-Type": "application/json"}
    res = requests.get(getKeysURL,headers=headers)
    return json.loads(res.content.decode("utf-8"))

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

subscriptionId = container_to_index_info["subscriptionId"]
storageAccountGroup = container_to_index_info["storageAccountGroup"]
storageAccount = container_to_index_info["storageAccount"]
container = container_to_index_info["container"]

datasourceName=f"{container}-dsn"
indexName=f"{container}-in"
skillsetName=f"{container}-ssn"
indexerName=f"{container}-irn"
eventSubscriptionName=f"{container}-esn"
prefix="dtdemo"
location="eastus"

token = getToken(security_info["appId"], security_info["password"], security_info["tenant"])["access_token"]
#result =getEventSubscriptionDeliveryAttributes(token, subscriptionId, eventSubscriptionName,storageAccountGroup,storageAccount)
#result=getEventSubscription(token, subscriptionId, eventSubscriptionName,storageAccountGroup,storageAccount)
prefix="dtdemo"
serviceName = f'{prefix}ss'
result= listSC(token)
print(json.dumps(result))



