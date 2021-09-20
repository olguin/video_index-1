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

class Worker(threading.Thread):
    def __init__(self, q,forced, *args, **kwargs):
        self.q = q
        self.forced = forced
        super().__init__(*args, **kwargs)
    def run(self):
        while True:
            try:
                url = self.q.get(timeout=60)
                processVideo(url,self.forced)
            except queue.Empty:
                return
            # do whatever work you have to do on work
            self.q.task_done()

def getAccountAccessToken(apiUrl,location,accountId, apiKey):
    tokenUrl = f"{apiUrl}/auth/{location}/Accounts/{accountId}/AccessToken?allowEdit=true"
    res = requests.get(tokenUrl, headers={"Ocp-Apim-Subscription-Key":apiKey})
    return res.content.decode("utf-8").replace('"','')

def listVideos():
    apiUrl , accountId , location , apiKey = getConnectionProperties()

    accountAccessToken  = getAccountAccessToken(apiUrl,location,accountId, apiKey)

    listVideosUrl=f"https://api.videoindexer.ai/{location}/Accounts/{accountId}/Videos?accessToken={accountAccessToken}"
    req = grequests.get(listVideosUrl)
    res = grequests.map([req])[0]
    result = json.loads(res.content.decode("utf-8"))
    return result

def videosStillProcessing():
    videos = listVideos()
    for video in videos["results"]:
        if(video["state"] != "Processed"):
            return True
    return False

def removeVideo(apiUrl,location,accountId, apiKey,accountAccessToken, videoId):
    listVideosUrl=f"https://api.videoindexer.ai/{location}/Accounts/{accountId}/Videos/{videoId}?accessToken={accountAccessToken}"
    res = requests.delete(listVideosUrl)
    print(res)

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
    apiUrl = "https://api.videoindexer.ai";
    location = "eastus"; 
    accountId = "a25c2c8a-c8b4-4f3f-a4c1-91e3ae4e36e9"; 
    apiKey = "07c7c290cc37428a95c9093484ec38b2"; 
    logging.info(f"Account ID {accountId}")

    return apiUrl , accountId , location , apiKey

def removeVideos():
    apiUrl , accountId , location , apiKey = getConnectionProperties()

    accountAccessToken  = getAccountAccessToken(apiUrl,location,accountId, apiKey)

    videos = listVideos(apiUrl,location,accountId, apiKey,accountAccessToken)
    for video in videos["results"]:
        videoId = video["id"]
        removeVideo(apiUrl,location,accountId, apiKey,accountAccessToken, videoId)

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

def indexVideos(forced=False):
    q = queue.Queue()
    res = requests.get(f"https://dockerazurefuncblob.blob.core.windows.net/doubletime-video-inputs?restype=container&comp=list")
    root = ET.fromstring(res.content.decode("utf-8"))
    for item in root.findall('.//Url'):
        url=item.text
        print(f" queing{url}")
        q.put_nowait(url)

    for _ in range(12):
        Worker(q, forced).start()

    q.join()  # blocks until the queue is empty.

def get_video_info(configuration, videoUrl):
    apiUrl , accountId , location , apiKey = getConnectionProperties()

    accountAccessToken  = getAccountAccessToken(apiUrl,location,accountId, apiKey)

    videoAlreadyUploaded, videoId = checkVideoIsUploaded(apiUrl,location,accountId, apiKey,accountAccessToken, videoUrl)

    if(not videoAlreadyUploaded):
        print(f"Video {videoUrl} not uploaded for process yet")
        return

    videoAccessToken = getVideoToken(apiUrl,location,accountId, apiKey,accountAccessToken, videoId)

    video_data = getVideoData(apiUrl,location,accountId, apiKey,accountAccessToken, videoId, videoAccessToken)
    with open('/tmp/response.json', 'w', encoding='utf-8') as f:
        json.dump(video_data, f, ensure_ascii=False, indent=4) 

    processingResult = formatForSkill(configuration, video_data, videoUrl, location, accountId, videoId)
    with open('/tmp/formated_response.json', 'w', encoding='utf-8') as f:
        json.dump(processingResult, f, ensure_ascii=False, indent=4) 

