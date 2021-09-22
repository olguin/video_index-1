import requests
import json
import time
import os
import xml.etree.ElementTree as ET
import threading
import queue
import re
import traceback
import logging

def getAccountAccessToken(apiUrl,location,accountId, apiKey):
    tokenUrl = f"{apiUrl}/auth/{location}/Accounts/{accountId}/AccessToken?allowEdit=true"
    res = requests.get(tokenUrl, headers={"Ocp-Apim-Subscription-Key":apiKey})
    return res.content.decode("utf-8").replace('"','')

def listVideos():
    apiUrl , accountId , location , apiKey = getConnectionProperties()

    accountAccessToken  = getAccountAccessToken(apiUrl,location,accountId, apiKey)

    listVideosUrl=f"https://api.videoindexer.ai/{location}/Accounts/{accountId}/Videos?accessToken={accountAccessToken}"
    res = requests.get(listVideosUrl)
    result = json.loads(res.content.decode("utf-8"))
    return result

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
    if("access_token" in response):
        return response['access_token']
    else:
        raise Exception(response)

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

def runIndexer():
    token = getToken()

    prefix =  os.getenv("PREFIX")
    container = os.getenv("CONTAINER")

    serviceName = f'{prefix}ss'
    searchServiceKey = getSearchServiceKey(token,serviceName, "2020-08-01" )
    indexerName=f"{container}-irn"
    runIndexerURL=f"https://{serviceName}.search.windows.net/indexers/{indexerName}/run?api-version=2020-06-30"
    res = requests.post(runIndexerURL,headers={"api-key":searchServiceKey})
    return json.loads(res.content.decode("utf-8"))


def getIndexerState():
    token = getToken()

    prefix =  os.getenv("PREFIX")
    container = os.getenv("CONTAINER")

    serviceName = f'{prefix}ss'
    searchServiceKey = getSearchServiceKey(token,serviceName, "2020-08-01" )
    indexerName=f"{container}-irn"
    getStatusIndexerURL=f"https://{serviceName}.search.windows.net/indexers/{indexerName}/status?api-version=2020-06-30"
    res = requests.get(getStatusIndexerURL,headers={"api-key":searchServiceKey})
    return json.loads(res.content.decode("utf-8"))


def videosStillProcessing():
    videos = listVideos()
    for video in videos["results"]:
        if(video["state"] != "Processed"):
            return True
    return False

def checkVideoIsUploaded(apiUrl,location,accountId, apiKey,accountAccessToken, videoUrl):
    checkUploadedVideoURL = f"{apiUrl}/{location}/Accounts/{accountId}/Videos/GetIdByExternalId?externalId={videoUrl}&accessToken={accountAccessToken}"
    res = requests.get(checkUploadedVideoURL)
    if (res.status_code == 404):
        return False, None
    else:
        return True, json.loads(res.content.decode("utf-8"))

def uploadVideo(apiUrl,location,accountId, apiKey,accountAccessToken, videoUrl):
    video_name = os.path.basename(videoUrl)
    uploadVideoURL = f"{apiUrl}/{location}/Accounts/{accountId}/Videos?accessToken={accountAccessToken}&name={video_name}&description=some_description&privacy=public&partition=some_partition&externalId={videoUrl}&videoUrl={videoUrl}"
    res = requests.post(uploadVideoURL)
    video=json.loads(res.content.decode("utf-8"))
    if(not "id" in video):
        raise Exception(json.dumps(video))
    return video["id"]

def getVideoToken(apiUrl,location,accountId, apiKey,accountAccessToken, videoId):
    videoTokenRequestURL = f"{apiUrl}/auth/{location}/Accounts/{accountId}/Videos/{videoId}/AccessToken?allowEdit=true"
    res = requests.get(videoTokenRequestURL, headers={"Ocp-Apim-Subscription-Key":apiKey})
    return res.content.decode("utf-8").replace('"','')

def getVideoProcessingStatus(apiUrl,location,accountId, apiKey,accountAccessToken, videoId, videoAccessToken):
    videoResultUrl = f"{apiUrl}/{location}/Accounts/{accountId}/Videos/{videoId}/Index?accessToken={videoAccessToken}&language=English"
    res = requests.get(videoResultUrl)
    return json.loads(res.content.decode("utf-8"))

def getVideoData(apiUrl,location,accountId, apiKey,accountAccessToken, videoId, videoAccessToken):
    finish = False
    while( not finish):
        processingResult = getVideoProcessingStatus(apiUrl,location,accountId, apiKey,accountAccessToken, videoId, videoAccessToken)
        print(processingResult)
        processingState = processingResult["state"]
        print(processingState)

        if (processingState != "Uploaded" and processingState != "Processing"):
            return processingResult
            finish = True
        else:
            time.sleep(50);

def formatTimestamp(timestamp):
    return re.sub(r"\..*$","",timestamp)

def getTimestamps(record):
    timestamps = []
    if('appearances' in record):
        appearances = record["appearances"]
    else:
        appearances = record["instances"]
    for appearance in appearances:
        if( "startTime" in appearance):
                start = appearance["startTime"]
                end = appearance["endTime"]
        else:
                start = appearance["start"]
                end = appearance["end"]
        timestamps.append({
                    "start": formatTimestamp(start),
                    "end": formatTimestamp(end)
                })
    return timestamps


def getSimpleRecords(records, name_map):
    processed_records = []
    if(records == None):
        return processed_records
    for record in records:
        processed_record = {}
        for from_name_field, to_name_field in name_map.items():
            if from_name_field in record:
                processed_record[to_name_field] = record[from_name_field]
            else:
                processed_record[to_name_field] = None
        processed_record["timestamps"] = getTimestamps(record)
        processed_records.append(processed_record)
    return processed_records

def getFaces(processingResult):
    return getSimpleRecords(processingResult["summarizedInsights"].get("faces"),{"name": "text"})

def getLabels(processingResult):
    return getSimpleRecords(processingResult["summarizedInsights"].get("labels"), {"name": "text"})

def getBrands(processingResult):
    return getSimpleRecords(processingResult["summarizedInsights"].get("brands"), {"name": "text", "referenceId": "reference", "referenceUrl": "referenceURL", "description": "description"})

def getTopics(processingResult):
    return getSimpleRecords(processingResult["videos"][0]["insights"].get("topics"), {"name": "text", "referenceId": "reference", "referenceUrl": "referenceURL", "referenceType": "referenceType"})

def getKeywords(processingResult):
    return getSimpleRecords(processingResult["summarizedInsights"].get("keywords"), {"name": "text"})

def getOCR(processingResult):
    return getSimpleRecords(processingResult["videos"][0]["insights"].get("ocr"), {"text": "text"})

def getTranscripts(processingResult):
    return getSimpleRecords(processingResult["videos"][0]["insights"].get("transcript"), {"text": "text"})

def getHeader(processingResult, videoUrl, location, accountId, videoId):
    res = requests.head(f"{videoUrl}?comp=metadata")
    headers = res.headers
    if(processingResult != None):
        thumbnailId = processingResult["summarizedInsights"]["thumbnailId"]
        thumbnail = f"https://api.videoindexer.ai/{location}/Accounts/{accountId}/Videos/{videoId}/Thumbnails/{thumbnailId}"
        name = processingResult["name"]
        description = processingResult["description"]
    else:
        thumbnail = ""
        name = videoUrl
        description = ""

    return {
        "creation_date": headers["Last-Modified"],
        "owner": "harcoded owner",
        "thumbnail": thumbnail,
        "name": name,
        "description": description
    }

def getMetadata(processingResult, videoUrl, location, accountId, videoId):
    res = requests.head(f"{videoUrl}?comp=metadata")
    headers = res.headers
    metadata = [{"key": header[10:],"value": value} for header, value in headers.items() if header.startswith('x-ms-meta-')]
    return metadata

def getConnectionProperties():
    apiUrl = os.getenv("DT_API_URL", "https://api.videoindexer.ai");
    location = os.getenv("DT_LOCATION", "eastus"); 
    accountId = os.getenv("DT_ACCOUNT_ID", "a25c2c8a-c8b4-4f3f-a4c1-91e3ae4e36e9"); 
    apiKey = os.getenv("DT_API_KEY", "07c7c290cc37428a95c9093484ec38b2"); 
    logging.info(f"Account ID {accountId}")

    return apiUrl , accountId , location , apiKey

def processVideo(videoUrl, configuration , forceUpload=False):
    try:
        apiUrl , accountId , location , apiKey = getConnectionProperties()

        accountAccessToken  = getAccountAccessToken(apiUrl,location,accountId, apiKey)

        if(forceUpload):
            videoAlreadyUploaded = False
        else:
            videoAlreadyUploaded, videoId = checkVideoIsUploaded(apiUrl,location,accountId, apiKey,accountAccessToken, videoUrl)

        if (not videoAlreadyUploaded):
            videoId = uploadVideo(apiUrl,location,accountId, apiKey,accountAccessToken, videoUrl)

        videoAccessToken = getVideoToken(apiUrl,location,accountId, apiKey,accountAccessToken, videoId)

        processingResult = getVideoData(apiUrl,location,accountId, apiKey,accountAccessToken, videoId, videoAccessToken)
    except Exception as e:
        logging.error(traceback.format_exc())
        logging.error(e)
        processingResult = None

    return formatForSkill(configuration, processingResult, videoUrl, location, accountId, videoId)

def formatForSkill(configuration, processingResult, videoUrl, location, accountId, videoId):
    if(processingResult != None):
        faces = getFaces(processingResult)
        labels = getLabels(processingResult)
        keywords = getKeywords(processingResult)
        ocr = getOCR(processingResult)
        transcripts = getTranscripts(processingResult)
        brands = getBrands(processingResult)
        topics = getTopics(processingResult)
    else:
        faces = []
        labels = []
        keywords = []
        ocr = []
        transcripts = []
        brands = []
        topics = []

    header = getHeader(processingResult, videoUrl, location, accountId, videoId)
    metadata = getMetadata(processingResult, videoUrl, location, accountId, videoId)

    result = {
            "transcripts": transcripts,
            "ocr": ocr,
            "keywords": keywords, 
            "topics": topics,
            "faces": faces,
            "labels": labels,
            "brands": brands,
            "header": header,
            "metadata": metadata
    }

    configuration.filterSectionsByConfigInRecord(result)
    
    return result

def isVideo(videoUrl):
    upperurl = videoUrl.upper()
    filename, extension = os.path.splitext(upperurl)
    return extension in [".MP4", ".MOV"]

def scan_all_videos(storageAccount, container):
    apiUrl , accountId , location , apiKey = getConnectionProperties()

    accountAccessToken  = getAccountAccessToken(apiUrl,location,accountId, apiKey)

    listVideosInContainerURL = f"https://{storageAccount}.blob.core.windows.net/{container}?restype=container&comp=list"
    res = requests.get(listVideosInContainerURL)
    root = ET.fromstring(res.content.decode("utf-8"))
    alreadyProcessedVideoIds = []
    newVideoIds = []
    for item in root.findall('.//Url'):
        videoUrl=item.text
        if(isVideo(videoUrl)):
            videoAlreadyUploaded, videoId = checkVideoIsUploaded(apiUrl,location,accountId, apiKey,accountAccessToken, videoUrl)
            if (not videoAlreadyUploaded):
                videoId = uploadVideo(apiUrl,location,accountId, apiKey,accountAccessToken, videoUrl)
                alreadyProcessedVideoIds.append(videoId)
            else:
                newVideoIds.append(videoId)
    return {
        "processed_videos": newVideoIds,
        "already_processed_videos": alreadyProcessedVideoIds
    }


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
    token = getToken()
    prefix =  os.getenv("PREFIX")
    serviceName = f'{prefix}ss'
    searchServiceKey = getSearchServiceKey(token,serviceName, "2020-08-01" )
    recordId = findRecord(token,searchServiceKey,url)
    res = deleteRecord(token,searchServiceKey,recordId)
    logging.info(f"deleted index data for video {url} {res}")
    return res



