import json
import jinja2 
import requests
import logging
import subprocess


def checkErrors(url, res):
    if(res == None):
        return
    if(res.status_code >= 200 and res.status_code <300):
        try:
            content = res.content.decode("utf-8")
            if(len(content) > 0):
                data =  json.loads(content)
                if("error" in data):
                    logging.error(f"Error calling {url} error: {data}")
        except ValueError:
                logging.error(f"Error calling {url} content: {res.content.decode('utf-8')}")

    else:
        logging.error(f"Error calling {url} status code: {res.status_code} {res.content.decode('utf-8')}")
        


def createTemplateEnvironment():
    templateLoader = jinja2.FileSystemLoader(searchpath="library/templates")
    templateEnv = jinja2.Environment(loader=templateLoader)
    return templateEnv 

def createEventSubscriptionJSON(indexingFunctionIdentifier, searchServiceKey, serviceName,indexerName, indexName):
    env = createTemplateEnvironment()
    template = env.get_template('create_event_subscription.json')
    data = {
        "function_id": indexingFunctionIdentifier,
        "search_service_key": searchServiceKey,
        "service_name": serviceName,
        "indexer_name": indexerName,
        "index_name": indexName
    }
    return template.render(data)

def createEventSubscription(token, subscriptionId, indexingFunctionIdentifier,eventSubscriptionName,storageAccountResourceGroup,storageAccount, searchServiceKey, serviceName,indexerName, indexName):
    createEventSubscriptionURL=f"https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{storageAccountResourceGroup}/providers/Microsoft.Storage/storageAccounts/{storageAccount}/providers/Microsoft.EventGrid/eventSubscriptions/{eventSubscriptionName}?api-version=2021-06-01-preview"
    headers= {"Authorization":f"Bearer {token}", "Content-Type": "application/json"}
    eventSubscriptionJson = createEventSubscriptionJSON(indexingFunctionIdentifier, searchServiceKey, serviceName,indexerName, indexName)
    res = requests.put(createEventSubscriptionURL,data=eventSubscriptionJson,headers=headers)
    checkErrors(createEventSubscriptionURL, res)
    return json.loads(res.content.decode("utf-8"))

def getEventSubscription(token, subscriptionId, eventSubscriptionName,storageAccountResourceGroup,storageAccount):
    getEventSubscriptionURL=f"https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{storageAccountResourceGroup}/providers/Microsoft.Storage/storageAccounts/{storageAccount}/providers/Microsoft.EventGrid/eventSubscriptions/{eventSubscriptionName}?api-version=2021-06-01-preview"
    headers= {"Authorization":f"Bearer {token}", "Content-Type": "application/json"}
    res = requests.get(getEventSubscriptionURL,headers=headers)
    checkErrors(getEventSubscriptionURL,res)
    return json.loads(res.content.decode("utf-8"))

def getEventSubscriptionDeliveryAttributes(token, subscriptionId, eventSubscriptionName,storageAccountResourceGroup,storageAccount):
    getEventSubscriptionURL=f"https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{storageAccountResourceGroup}/providers/Microsoft.Storage/storageAccounts/{storageAccount}/providers/Microsoft.EventGrid/eventSubscriptions/{eventSubscriptionName}/getDeliveryAttributes?api-version=2021-06-01-preview"
    headers= {"Authorization":f"Bearer {token}", "Content-Type": "application/json"}
    res = requests.post(getEventSubscriptionURL,headers=headers)
    checkErrors(getEventSubscriptionURL,res)
    return json.loads(res.content.decode("utf-8"))

def putEventSubscriptionDeliveryAttributes(token, subscriptionId, eventSubscriptionName,storageAccountResourceGroup,storageAccount):
    data = {
        "value": [
            {
            "name": "header1",
            "type": "Static",
            "properties": {
                "value": "NormalValue",
                "isSecret": False
            }
          }
        ]
    }
    getEventSubscriptionURL=f"https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{storageAccountResourceGroup}/providers/Microsoft.Storage/storageAccounts/{storageAccount}/providers/Microsoft.EventGrid/eventSubscriptions/{eventSubscriptionName}/setDeliveryAttributes?api-version=2021-06-01-preview"
    headers= {"Authorization":f"Bearer {token}", "Content-Type": "application/json"}
    res = requests.post(getEventSubscriptionURL,data=data,headers=headers)
    checkErrors(getEventSubscriptionURL,res)
    #return json.loads(res.content.decode("utf-8"))
    return res.content.decode("utf-8")




def createSystemTopicJSON(subscriptionId,resourceGroupName,storageAccountName,topicName):
    env = createTemplateEnvironment()
    template = env.get_template('create_system_topic.json')
    data = {
        "topic_name": topicName,
        "storage_account": storageAccountName,
        "subscription_id": subscriptionId,
        "resource_group": resourceGroupName
    }
    return template.render(data)

def createSystemTopic(token, subscriptionId, resourceGroupName, storageAccountName,topicName, apiVersion):
    createSystemTopicURL=f"https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.EventGrid/systemTopics/{topicName}?api-version={apiVersion}"
    headers= {"Authorization":f"Bearer {token}", "Content-Type": "application/json"}
    systemTopicJson = createSystemTopicJSON(subscriptionId,resourceGroupName,storageAccountName,topicName)
    res = requests.put(createSystemTopicURL,data=systemTopicJson,headers=headers)
    checkErrors(createSystemTopicURL, res)
    return json.loads(res.content.decode("utf-8"))


def createDatasourceJSON(datasource_name,accountName,accountKey,container):
    env = createTemplateEnvironment()
    template = env.get_template('create_datasource.json')
    data = {
        "datasource_name": datasource_name,
        "account_name": accountName,
        "account_key": accountKey,
        "container": container
    }
    return template.render(data)

def createDatasource(token, subscriptionId, serviceName, serviceKey,storageGroup,account,container,datasourceName):
    storageAccountKeys = getStorageAccountKeys(token,subscriptionId,storageGroup, account, "2021-04-01" )
    if(not ("keys" in storageAccountKeys)):
        logging.error(storageAccountKeys)
        raise Exception(storageAccountKeys)
    key = storageAccountKeys["keys"][0]["value"]
    datasourceJson = createDatasourceJSON(datasourceName,account,key,container)
    headers= {"api-key": serviceKey, "Content-Type": "application/json"}
    createDatasourceURL=f"https://{serviceName}.search.windows.net/datasources/{datasourceName}?api-version=2020-06-30"
    res = requests.put(createDatasourceURL,data=datasourceJson,headers=headers)
    checkErrors(createDatasourceURL, res)

def createIndexJSON(indexName):
    env = createTemplateEnvironment()
    template = env.get_template('create_index.json')
    data = {
        "index_name": indexName
    }
    return template.render(data)


def createIndex(serviceName, serviceKey,indexName):
    indexJson = createIndexJSON(indexName)
    headers= {"api-key": serviceKey, "Content-Type": "application/json"}
    createIndexURL=f"https://{serviceName}.search.windows.net/indexes/{indexName}?api-version=2020-06-30"
    res = requests.put(createIndexURL,data=indexJson,headers=headers)
    checkErrors(createIndexURL, res)

def createIndexerJSON(indexerName, datasourceName, targetIndex, skillsetName):
    env = createTemplateEnvironment()
    template = env.get_template('create_indexer.json')
    data = {
        "indexer_name": indexerName,
        "datasource_name": datasourceName,
        "target_index": targetIndex,
        "skillset_name": skillsetName
    }
    return template.render(data)


def createIndexer(serviceName, serviceKey,indexerName, datasourceName, targetIndex, skillsetName):
    indexerJson = createIndexerJSON(indexerName, datasourceName, targetIndex, skillsetName)
    headers= {"api-key": serviceKey, "Content-Type": "application/json"}
    createIndexerURL=f"https://{serviceName}.search.windows.net/indexers/{indexerName}?api-version=2020-06-30"
    res = requests.put(createIndexerURL,data=indexerJson,headers=headers)
    checkErrors(createIndexerURL,res)


def createSkillsetJSON(skillsetName,functionApp):
    env = createTemplateEnvironment()
    template = env.get_template('create_skillset.json')
    data = {
        "skillset_name": skillsetName,
        "function_app":functionApp
    }
    return template.render(data)


def createSkillset(serviceName, serviceKey,skillsetName,functionApp):
    skillsetJson = createSkillsetJSON(skillsetName,functionApp)
    headers= {"api-key": serviceKey, "Content-Type": "application/json"}
    createIndexURL=f"https://{serviceName}.search.windows.net/skillsets/{skillsetName}?api-version=2020-06-30"
    res = requests.put(createIndexURL,data=skillsetJson,headers=headers)
    checkErrors(createIndexURL, res)

def createSearchService(token, subscriptionId, resourceGroupName, searchServiceName,apiVersion):
    createSearchServiceURL=f"https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Search/searchServices/{searchServiceName}?api-version={apiVersion}"
    headers= {"Authorization":f"Bearer {token}", "Content-Type": "application/json"}
    data={
        "location":"eastus",
        "sku": {
            "name": "basic"
        }
    }
    res = requests.put(createSearchServiceURL,data=json.dumps(data),headers=headers)
    checkErrors(res, createSearchServiceURL)
    return json.loads(res.content.decode("utf-8"))

def createResourceGroup(token, subscriptionId, resourceGroupName):
    createSearchServiceURL=f"https://management.azure.com/subscriptions/{subscriptionId}/resourcegroups/{resourceGroupName}?api-version=2021-04-01"
    headers= {"Authorization":f"Bearer {token}", "Content-Type": "application/json"}
    data={
        "location":"eastus",
    }
    res = requests.put(createSearchServiceURL,data=json.dumps(data),headers=headers)
    checkErrors(createSearchServiceURL, res)
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
    checkErrors(url, res)
    response=json.loads(res.content.decode("utf-8"))
    return response

def getSearchServiceKeys(token, subscriptionId, resourceGroupName, searchServiceName,apiVersion):
    getKeysURL=f"https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Search/searchServices/{searchServiceName}/listAdminKeys?api-version={apiVersion}"
    headers= {"Authorization":f"Bearer {token}", "Content-Type": "application/json"}
    res = requests.post(getKeysURL,headers=headers)
    checkErrors(getKeysURL, res)
    return json.loads(res.content.decode("utf-8"))

def getStorageAccountKeys(token, subscriptionId, resourceGroupName, accountName,apiVersion):
    getKeysURL=f"https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Storage/storageAccounts/{accountName}/listKeys?api-version={apiVersion}"
    headers= {"Authorization":f"Bearer {token}", "Content-Type": "application/json"}
    res = requests.post(getKeysURL,headers=headers)
    checkErrors(getKeysURL, res)
    return json.loads(res.content.decode("utf-8"))

def listSystemTopics(token, subscriptionId,resourceGroupName):
    listEventsURL=f"https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.EventGrid/systemTopics?api-version=2021-06-01-preview"
    headers= {"Authorization":f"Bearer {token}", "Content-Type": "application/json"}
    res = requests.get(listEventsURL,headers=headers)
    checkErrors(listEventsURL, res)
    return json.loads(res.content.decode("utf-8"))

def checkFunctionExists(token, subscriptionId,resourceGroupName,functionName):
    listFunctionsURL=f"https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Web/sites/{functionName}?api-version=2015-08-01"
    headers= {"Authorization":f"Bearer {token}", "Content-Type": "application/json"}
    res = requests.get(listFunctionsURL,headers=headers)
    checkErrors(listFunctionsURL, res)
    result = json.loads(res.content.decode("utf-8"))
    if ("error" in result):
        return False
    else:
        return result["properties"]["state"] == "Running"

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

def setWebAppParameters(subscriptionId, resourceGroup, webApp, searchServiceKey,searchFunctionIdentifier):
    command=f"webapp config appsettings set --subscription {subscriptionId} -g {resourceGroup} -n {webApp} --settings DT_SEARCH_SERVICE_KEY={searchServiceKey} DT_ACS_WRAPPER_FUNCTION_URL={searchFunctionIdentifier}"
    run_az_command(command)



def createCompleteIndex(token, container_to_index_info,serviceName, resourceGroup,functionApp, webApp):

    subscriptionId = container_to_index_info["subscriptionId"]
    storageAccountGroup = container_to_index_info["storageAccountGroup"]
    storageAccount = container_to_index_info["storageAccount"]
    container = container_to_index_info["container"]

    datasourceName=f"{container}-dsn"
    indexName=f"{container}-in"
    skillsetName=f"{container}-ssn"
    indexerName=f"{container}-irn"
    eventSubscriptionName=f"{container}-esn"

    searchServiceKeys = getSearchServiceKeys(token,subscriptionId ,resourceGroup, serviceName, "2020-08-01" )
    if("primaryKey" in searchServiceKeys):
        searchServiceKey = searchServiceKeys["primaryKey"]
    else:
        raise Exception(searchServiceKeys)
    storageAccountKeys = getStorageAccountKeys(token, subscriptionId,storageAccountGroup, storageAccount, "2021-04-01" )
    createDatasource(token, subscriptionId, serviceName, searchServiceKey,storageAccountGroup,storageAccount,container,datasourceName)
    createIndex(serviceName, searchServiceKey,indexName)
    createSkillset(serviceName, searchServiceKey,skillsetName,functionApp)
    createIndexer(serviceName, searchServiceKey,indexerName, datasourceName,indexName,skillsetName)

    indexingFunctionIdentifier=f"/subscriptions/{subscriptionId}/resourceGroups/{resourceGroup}/providers/Microsoft.Web/sites/{functionApp}/functions/BlobIndexingTrigger"
    createEventSubscription(token, subscriptionId, indexingFunctionIdentifier,eventSubscriptionName,storageAccountGroup,storageAccount, searchServiceKey, serviceName,indexerName, indexName)

    searchFunctionIdentifier=f"/subscriptions/{subscriptionId}/resourceGroups/{resourceGroup}/providers/Microsoft.Web/sites/{functionApp}/functions/ACSSearchAPIWrapper"
    setWebAppParameters(subscriptionId, resourceGroup, webApp, searchServiceKey,searchFunctionIdentifier)

    
