import responses
import json
from shared_code.video_indexer_tools import *
from shared_code.configuration_file import ConfigurationFile as ConfigurationFile
import pytest

def setConnectionProperties(apiUrl, location, accountId, apiKey):
    os.environ["DT_VIDEO_SCAN_API_URL"] = apiUrl
    os.environ["DT_LOCATION"] = location
    os.environ["DT_VIDEO_SCAN_ACCOUNT_ID"] = accountId
    os.environ["DT_VIDEO_SCAN_API_KEY"] = apiKey

def addSearchServiceKeyResponse(subscriptionId, groupId, searchService,apiVersion, key):
    os.environ["DT_SUBSCRIPTION"] = subscriptionId
    os.environ["DT_SEARCH_SERVICE_GROUP"] = groupId

    getKeysURL=f"https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{groupId}/providers/Microsoft.Search/searchServices/{searchService}/listAdminKeys?api-version={apiVersion}"
    keysResponse = {}
    if(key != None):
        keysResponse["primaryKey"] = key
    responses.add(**{
        'method'         : responses.POST,
        'url'            : getKeysURL,
        'body'           : json.dumps(keysResponse),
        'status'         : 200,
        'content_type'   : 'application/json',
        'adding_headers' : {'Last-Modified': '1999-01-02'}
        })


def addGetTokenResponse(appID , tenant , password , token):
    os.environ["DT_APP_ID"] = appID
    os.environ["DT_TENANT"] = tenant
    os.environ["DT_PASSWORD"] = password
    url=f"https://login.microsoftonline.com/{tenant}/oauth2/token"
    tokenResponse = {
    }
    if(token != None):
        tokenResponse["access_token"] = token

    responses.add(**{
        'method'         : responses.POST,
        'url'            : url,
        'body'           : json.dumps(tokenResponse),
        'status'         : 200,
        'content_type'   : 'application/json',
        'adding_headers' : {'Last-Modified': '1999-01-02'}
        })

def addListVideosResponse(apiUrl , accountId , location , apiKey, accountAccessToken, body):
    listVideosUrl=f"https://api.videoindexer.ai/{location}/Accounts/{accountId}/Videos?accessToken={accountAccessToken}"
    responses.add(**{
        'method'         : responses.GET,
        'url'            : listVideosUrl,
        'body'           : body,
        'status'         : 200,
        'content_type'   : 'application/json',
        'adding_headers' : {'Last-Modified': '1999-01-02'}
        })


def addHeaderResponse(videoUrl):
    headerUrl = f"{videoUrl}?comp=metadata"
    responses.add(**{
        'method'         : responses.HEAD,
        'url'            : headerUrl,
        'body'           : "{}",
        'status'         : 200,
        'content_type'   : 'application/json',
        'adding_headers' : {'Last-Modified': '1999-01-02'}
        })


def addAccountAccessResponse(token):
    apiUrl , accountId , location , apiKey = getConnectionProperties()
    tokenUrl = f"{apiUrl}/auth/{location}/Accounts/{accountId}/AccessToken?allowEdit=true"
    responses.add(**{
        'method'         : responses.GET,
        'url'            : tokenUrl,
        'body'           : token,
        'status'         : 200,
        'content_type'   : 'application/json',
        'adding_headers' : {'X-Foo': 'Bar'}
        })

def addCheckUploadVideoResponse(apiUrl , accountId , location , apiKey, accountAccessToken , videoUrl, status, body):
    checkUploadedVideoURL = f"{apiUrl}/{location}/Accounts/{accountId}/Videos/GetIdByExternalId?externalId={videoUrl}&accessToken={accountAccessToken}"
    responses.add(**{
        'method'         : responses.GET,
        'url'            : checkUploadedVideoURL,
        'body'           : body,
        'status'         : status,
        'content_type'   : 'application/json',
        'adding_headers' : {'X-Foo': 'Bar'}
        })

def addUploadVideoResponse(apiUrl , accountId , location , apiKey, accountAccessToken, videoUrl, body):
    video_name = os.path.basename(videoUrl)
    uploadVideoURL = f"{apiUrl}/{location}/Accounts/{accountId}/Videos?accessToken={accountAccessToken}&name={video_name}&description=some_description&privacy=public&partition=some_partition&externalId={videoUrl}&videoUrl={videoUrl}"
    responses.add(**{
        'method'         : responses.POST,
        'url'            : uploadVideoURL,
        'body'           : body,
        'status'         : 200,
        'content_type'   : 'application/json',
        'adding_headers' : {'X-Foo': 'Bar'}
        })

def addVideoTokenResponse(apiUrl , accountId , location , apiKey,accountAccessToken,videoId,token):
    videoTokenRequestURL = f"{apiUrl}/auth/{location}/Accounts/{accountId}/Videos/{videoId}/AccessToken?allowEdit=true"
    responses.add(**{
        'method'         : responses.GET,
        'url'            : videoTokenRequestURL,
        'body'           : token,
        'status'         : 200,
        'content_type'   : 'application/json',
        'adding_headers' : {'X-Foo': 'Bar'}
        })

def addVideoStatusResponse(apiUrl , accountId , location , apiKey, accountAccessToken, videoId, videoAccessToken, body):
    videoResultUrl = f"{apiUrl}/{location}/Accounts/{accountId}/Videos/{videoId}/Index?accessToken={videoAccessToken}&language=English"

    responses.add(**{
        'method'         : responses.GET,
        'url'            : videoResultUrl,
        'body'           : body,
        'status'         : 200,
        'content_type'   : 'application/json',
        'adding_headers' : {'X-Foo': 'Bar'}
        })




@responses.activate
def testGetAccountAccessToken():
    setConnectionProperties("https://dummyapi.com", "eastus", "123456", "ABCDEFGHI")
    addAccountAccessResponse("dummy_token")
    apiUrl , accountId , location , apiKey = getConnectionProperties()
    assert "dummy_token" == getAccountAccessToken(apiUrl,location,accountId, apiKey)

@responses.activate
def testCheckVideoIsUploaded():
    setConnectionProperties("https://dummyapi.com", "eastus", "123456", "ABCDEFGHI")
    apiUrl , accountId , location , apiKey = getConnectionProperties()
    accountAccessToken = "123456"
    videoUrl = "https://dummy/video.mp4"

    addCheckUploadVideoResponse(apiUrl , accountId , location , apiKey, accountAccessToken , videoUrl, 404, None)
    addCheckUploadVideoResponse(apiUrl , accountId , location , apiKey, accountAccessToken , videoUrl, 200, "{}")
    assert (False, None) == checkVideoIsUploaded(apiUrl,location,accountId, apiKey,accountAccessToken, videoUrl)
    assert (True, {}) == checkVideoIsUploaded(apiUrl,location,accountId, apiKey,accountAccessToken, videoUrl)

@responses.activate
def testUploadVideo():
    setConnectionProperties("https://dummyapi.com", "eastus", "123456", "ABCDEFGHI")
    apiUrl , accountId , location , apiKey = getConnectionProperties()
    accountAccessToken = "123456"
    videoUrl = "https://dummy/video.mp4"

    addUploadVideoResponse(apiUrl , accountId , location , apiKey, accountAccessToken, videoUrl,  '{"id": "id12345678"}')

    assert "id12345678"  == uploadVideo(apiUrl,location,accountId, apiKey,accountAccessToken, videoUrl)

@responses.activate
def testUploadVideoError():
    setConnectionProperties("https://dummyapi.com", "eastus", "123456", "ABCDEFGHI")
    apiUrl , accountId , location , apiKey = getConnectionProperties()
    accountAccessToken = "123456"
    videoUrl = "https://dummy/video.mp4"

    addUploadVideoResponse(apiUrl , accountId , location , apiKey, accountAccessToken, videoUrl,  '{"error": "error message"}')
    try: 
        uploadVideo(apiUrl,location,accountId, apiKey,accountAccessToken, videoUrl)
    except:
        #expected
        return
    pytest.fail("should have thrown exception")

@responses.activate
def testGetVideoToken():
    setConnectionProperties("https://dummyapi.com", "eastus", "123456", "ABCDEFGHI")
    apiUrl , accountId , location , apiKey = getConnectionProperties()
    accountAccessToken = "123456"
    videoId = "videoId1234"
    addVideoTokenResponse(apiUrl , accountId , location , apiKey,accountAccessToken,videoId,"dummyToken")
    assert "dummyToken"  == getVideoToken(apiUrl,location,accountId, apiKey,accountAccessToken, videoId)

@responses.activate
def testGetVideoProcessingStatus():
    setConnectionProperties("https://dummyapi.com", "eastus", "123456", "ABCDEFGHI")
    apiUrl , accountId , location , apiKey = getConnectionProperties()
    accountAccessToken = "123456"
    videoId = "videoId1234"
    videoAccessToken = "dummyToken"

    addVideoStatusResponse(apiUrl , accountId , location , apiKey, accountAccessToken, videoId, videoAccessToken, "{}")
    assert {}  == getVideoProcessingStatus(apiUrl,location,accountId, apiKey,accountAccessToken, videoId, videoAccessToken)

@responses.activate
def testGetVideoData():
    setConnectionProperties("https://dummyapi.com", "eastus", "123456", "ABCDEFGHI")
    apiUrl , accountId , location , apiKey = getConnectionProperties()
    accountAccessToken = "123456"
    videoId = "videoId1234"
    videoAccessToken = "dummyToken"
    addVideoStatusResponse(apiUrl , accountId , location , apiKey, accountAccessToken, videoId, videoAccessToken, '{"state": "Processed"}')
    assert {"state": "Processed"}  == getVideoData(apiUrl,location,accountId, apiKey,accountAccessToken, videoId, videoAccessToken)

@responses.activate
def testListVideos():
    setConnectionProperties("https://dummyapi.com", "eastus", "123456", "ABCDEFGHI")
    accountAccessToken = "dummy_token"
    addAccountAccessResponse(accountAccessToken)
    apiUrl , accountId , location , apiKey = getConnectionProperties()
    addListVideosResponse(apiUrl , accountId , location , apiKey, accountAccessToken, "{}")

    assert {} == listVideos()

@responses.activate
def testVideosStillProcessing():
    setConnectionProperties("https://dummyapi.com", "eastus", "123456", "ABCDEFGHI")
    accountAccessToken = "dummy_token"
    addAccountAccessResponse(accountAccessToken)
    apiUrl , accountId , location , apiKey = getConnectionProperties()
    responseWithVideosStillProcessing = {
        "results": [
            {
                "state": "Processed"
            },
            {
                "state": "Processing"
            },


        ]
    }
    addListVideosResponse(apiUrl , accountId , location , apiKey, accountAccessToken, json.dumps(responseWithVideosStillProcessing))
    responseWithAllVideosProcessed = {
        "results": [
            {
                "state": "Processed"
            },
            {
                "state": "Processed"
            },
        ]
    }
    addListVideosResponse(apiUrl , accountId , location , apiKey, accountAccessToken, json.dumps(responseWithAllVideosProcessed))


    assert True == videosStillProcessing()
    assert False == videosStillProcessing()

@responses.activate
def testGetToken():
    token = "dummyToken"
    addGetTokenResponse("1234", "5678", "ABCDE", token)

    assert token == getToken()

@responses.activate
def testGetTokenWithError():
    token = None
    try: 
        addGetTokenResponse("1234", "5678", "ABCDE", token)
        getToken()
    except:
        #expected
        return
    pytest.fail("should have thrown exception")
        


@responses.activate
def testSearchServiceKey():
    key = "dummy_key"
    searchService = "searchservice"
    apiVersion = "2020-08-01"
    addSearchServiceKeyResponse("subscriptionid", "groupid", searchService,apiVersion, key)

    assert key == getSearchServiceKey("dummy_token", searchService, apiVersion)

@responses.activate
def testSearchServiceKeyError():
    key = None
    searchService = "searchservice"
    apiVersion = "2020-08-01"
    addSearchServiceKeyResponse("subscriptionid", "groupid", searchService,apiVersion, key)

    try: 
        getSearchServiceKey("dummy_token", searchService, apiVersion)
    except:
        #expected
        return
    pytest.fail("should have thrown exception")


@responses.activate
def testRunIndexer():
    key = "dummy_key"
    apiVersion = "2020-08-01"
    prefix =  "my_prefix"
    os.environ["DT_PREFIX"] = prefix
    container =  "my_container"
    os.environ["DT_INDEXED_CONTAINER"] = container

    serviceName = f'{prefix}ss'
    indexerName=f"{container}-irn"

    addSearchServiceKeyResponse("subscriptionid", "groupid", serviceName,apiVersion, key)

    token = "dummyToken"
    addGetTokenResponse("1234", "5678", "ABCDE", token)


    runIndexerURL=f"https://{serviceName}.search.windows.net/indexers/{indexerName}/run?api-version=2020-06-30"
    responses.add(**{
        'method'         : responses.POST,
        'url'            : runIndexerURL,
        'body'           : "{}",
        'status'         : 200,
        'content_type'   : 'application/json',
        'adding_headers' : {'Last-Modified': '1999-01-02'}
        })


    assert {} == runIndexer()

@responses.activate
def testScanAllVideos():
    setConnectionProperties("https://dummyapi.com", "eastus", "123456", "ABCDEFGHI")
    apiUrl , accountId , location , apiKey = getConnectionProperties()
    accountAccessToken = "123456"
    addAccountAccessResponse(accountAccessToken)
    videoUrl1 = "https://dummy/video1.mp4"
    videoUrl2 = "https://dummy/video2.mp4"

    addCheckUploadVideoResponse(apiUrl , accountId , location , apiKey, accountAccessToken , videoUrl1, 404, None)
    addCheckUploadVideoResponse(apiUrl , accountId , location , apiKey, accountAccessToken , videoUrl2, 200, "{}")
    addUploadVideoResponse(apiUrl , accountId , location , apiKey, accountAccessToken, videoUrl1,  '{"id": "id12345678"}')

    storageAccount = "storage_account"
    container = "container"
    listVideosInContainerURL = f"https://{storageAccount}.blob.core.windows.net/{container}?restype=container&comp=list"
    videoListXML=f"""
        <Document>
            <Url>{videoUrl1}</Url>
            <Url>{videoUrl2}</Url>
        </Document>
    """
    responses.add(**{
        'method'         : responses.GET,
        'url'            : listVideosInContainerURL,
        'body'           : videoListXML,
        'status'         : 200,
        'content_type'   : 'application/json',
        'adding_headers' : {'Last-Modified': '1999-01-02'}
        })


    scan_all_videos(storageAccount, container)

@responses.activate
def testGetIndexerState():
    key = "dummy_key"
    apiVersion = "2020-08-01"
    prefix =  "my_prefix"
    os.environ["DT_PREFIX"] = prefix
    container =  "my_container"
    os.environ["DT_INDEXED_CONTAINER"] = container

    serviceName = f'{prefix}ss'
    indexerName=f"{container}-irn"

    addSearchServiceKeyResponse("subscriptionid", "groupid", serviceName,apiVersion, key)

    token = "dummyToken"
    addGetTokenResponse("1234", "5678", "ABCDE", token)


    getStatusIndexerURL=f"https://{serviceName}.search.windows.net/indexers/{indexerName}/status?api-version=2020-06-30"
    responses.add(**{
        'method'         : responses.GET,
        'url'            : getStatusIndexerURL,
        'body'           : "{}",
        'status'         : 200,
        'content_type'   : 'application/json',
        'adding_headers' : {'Last-Modified': '1999-01-02'}
        })


    assert {} == getIndexerState()

@responses.activate
def testFindRecord():
    key = "dummy_key"
    apiVersion = "2020-08-01"
    prefix =  "my_prefix"
    os.environ["DT_PREFIX"] = prefix
    container =  "my_container"
    os.environ["DT_INDEXED_CONTAINER"] = container

    serviceName = f'{prefix}ss'
    indexName=f"{container}-in"

    addSearchServiceKeyResponse("subscriptionid", "groupid", serviceName,apiVersion, key)

    token = "dummyToken"
    addGetTokenResponse("1234", "5678", "ABCDE", token)


    recordId = "123456"
    findRecordURL =f"https://{serviceName}.search.windows.net/indexes/{indexName}/docs/search?api-version=2020-06-30"
    findRecordResponse = {
        "value": [
            {
                "id": recordId
            }
        ]
    }
    responses.add(**{
        'method'         : responses.POST,
        'url'            : findRecordURL,
        'body'           : json.dumps(findRecordResponse),
        'status'         : 200,
        'content_type'   : 'application/json',
        'adding_headers' : {'Last-Modified': '1999-01-02'}
        })


    assert recordId == findRecord(token,key, "https://dummy_video.mp4")

@responses.activate
def testDeleteRecord():
    key = "dummy_key"
    apiVersion = "2020-08-01"
    prefix =  "my_prefix"
    os.environ["DT_PREFIX"] = prefix
    container =  "my_container"
    os.environ["DT_INDEXED_CONTAINER"] = container

    serviceName = f'{prefix}ss'
    indexName=f"{container}-in"

    addSearchServiceKeyResponse("subscriptionid", "groupid", serviceName,apiVersion, key)

    token = "dummyToken"
    addGetTokenResponse("1234", "5678", "ABCDE", token)


    deleteRecordURL =f"https://{serviceName}.search.windows.net/indexes/{indexName}/docs/index?api-version=2020-06-30"
    responses.add(**{
        'method'         : responses.POST,
        'url'            : deleteRecordURL,
        'body'           : "{}",
        'status'         : 200,
        'content_type'   : 'application/json',
        'adding_headers' : {'Last-Modified': '1999-01-02'}
        })


    assert {} == deleteRecord(token,key, "123456")

@responses.activate
def testDeleteVideo():
    key = "dummy_key"
    apiVersion = "2020-08-01"
    prefix =  "my_prefix"
    os.environ["DT_PREFIX"] = prefix
    container =  "my_container"
    os.environ["DT_INDEXED_CONTAINER"] = container

    serviceName = f'{prefix}ss'
    indexName=f"{container}-in"

    addSearchServiceKeyResponse("subscriptionid", "groupid", serviceName,apiVersion, key)

    token = "dummyToken"
    addGetTokenResponse("1234", "5678", "ABCDE", token)


    recordId = "123456"
    findRecordURL =f"https://{serviceName}.search.windows.net/indexes/{indexName}/docs/search?api-version=2020-06-30"
    findRecordResponse = {
        "value": [
            {
                "id": recordId
            }
        ]
    }
    responses.add(**{
        'method'         : responses.POST,
        'url'            : findRecordURL,
        'body'           : json.dumps(findRecordResponse),
        'status'         : 200,
        'content_type'   : 'application/json',
        'adding_headers' : {'Last-Modified': '1999-01-02'}
        })

    deleteRecordURL =f"https://{serviceName}.search.windows.net/indexes/{indexName}/docs/index?api-version=2020-06-30"
    responses.add(**{
        'method'         : responses.POST,
        'url'            : deleteRecordURL,
        'body'           : "{}",
        'status'         : 200,
        'content_type'   : 'application/json',
        'adding_headers' : {'Last-Modified': '1999-01-02'}
        })


    assert {} == deleteVideo("https://dummy_video.mp4")


@responses.activate
def testProcessVideo():
    setConnectionProperties("https://dummyapi.com", "eastus", "123456", "ABCDEFGHI")
    accountAccessToken = "dummy_token"
    addAccountAccessResponse(accountAccessToken)
    apiUrl , accountId , location , apiKey = getConnectionProperties()
    videoUrl = "https://dummy/video.mp4"
    addCheckUploadVideoResponse(apiUrl , accountId , location , apiKey, accountAccessToken , videoUrl, 404, "{}")
    videoId = "videoId1234"
    addUploadVideoResponse(apiUrl , accountId , location , apiKey, accountAccessToken, videoUrl,  json.dumps({"id": videoId}))
    addVideoTokenResponse(apiUrl , accountId , location , apiKey,accountAccessToken,videoId,"dummyToken")
    videoResponse = {
        "partition": "some_partition",
        "description": "some_description",
        "privacyMode": "Public",
        "state": "Processed",
        "accountId": "a25c2c8a-c8b4-4f3f-a4c1-91e3ae4e36e9",
        "id": "a703c9d6cf",
        "name": "-7rEi5VtC54_195_198.mp4",
        "userName": "Shao Fang",
        "created": "2021-09-16T20:38:47.62243+00:00",
        "isOwned": True,
        "isEditable": True,
        "isBase": True,
        "durationInSeconds": 3,
        "summarizedInsights": {
            "name": "barcode-testing.mp4",
            "id": "7ecb13e081",
            "privacyMode": "Public",
            "duration": {
                "time": "0:04:32",
                "seconds": 272
            },
            "thumbnailVideoId": "7ecb13e081",
            "thumbnailId": "5daac7a4-58e8-40b7-bbb0-ab71da05d543",
            "faces": [
                {
                    "videoId": "7ecb13e081",
                    "confidence": 0,
                    "description": None,
                    "title": None,
                    "thumbnailId": "77116c48-4fc3-4dce-8306-a85c24a9ccf0",
                    "seenDuration": 2.4,
                    "seenDurationRatio": 0.0088,
                    "id": 1010,
                    "name": "Unknown #1",
                    "appearances": [
                        {
                            "startTime": "0:01:27.733",
                            "endTime": "0:01:30.134",
                            "startSeconds": 87.7,
                            "endSeconds": 90.1
                        }
                    ]
                }
            ],
            "keywords": [
                {
                    "isTranscript": True,
                    "id": 1,
                    "name": "major types",
                    "appearances": [
                        {
                            "startTime": "0:01:11.82",
                            "endTime": "0:01:16.95",
                            "startSeconds": 71.8,
                            "endSeconds": 77
                        },
                        {
                            "startTime": "0:01:30.14",
                            "endTime": "0:01:34.934",
                            "startSeconds": 90.1,
                            "endSeconds": 94.9
                        },
                        {
                            "startTime": "0:02:38.95",
                            "endTime": "0:02:43.573",
                            "startSeconds": 159,
                            "endSeconds": 163.6
                        }
                    ]
                },
                {
                    "isTranscript": True,
                    "id": 2,
                    "name": "barcode technology",
                    "appearances": [
                        {
                            "startTime": "0:00:00",
                            "endTime": "0:00:05.134",
                            "startSeconds": 0,
                            "endSeconds": 5.1
                        },
                        {
                            "startTime": "0:00:10.01",
                            "endTime": "0:00:23.6",
                            "startSeconds": 10,
                            "endSeconds": 23.6
                        },
                        {
                            "startTime": "0:00:33",
                            "endTime": "0:00:35.8",
                            "startSeconds": 33,
                            "endSeconds": 35.8
                        },
                        {
                            "startTime": "0:00:39.88",
                            "endTime": "0:00:50.06",
                            "startSeconds": 39.9,
                            "endSeconds": 50.1
                        },
                        {
                            "startTime": "0:00:56",
                            "endTime": "0:01:08.64",
                            "startSeconds": 56,
                            "endSeconds": 68.6
                        },
                        {
                            "startTime": "0:01:11.82",
                            "endTime": "0:01:34.934",
                            "startSeconds": 71.8,
                            "endSeconds": 94.9
                        },
                        {
                            "startTime": "0:01:39.08",
                            "endTime": "0:01:50.65",
                            "startSeconds": 99.1,
                            "endSeconds": 110.6
                        },
                        {
                            "startTime": "0:01:56.4",
                            "endTime": "0:02:05.43",
                            "startSeconds": 116.4,
                            "endSeconds": 125.4
                        },
                        {
                            "startTime": "0:02:16.23",
                            "endTime": "0:02:28.86",
                            "startSeconds": 136.2,
                            "endSeconds": 148.9
                        },
                        {
                            "startTime": "0:02:38.95",
                            "endTime": "0:03:59.23",
                            "startSeconds": 159,
                            "endSeconds": 239.2
                        },
                        {
                            "startTime": "0:04:02.667",
                            "endTime": "0:04:30.734",
                            "startSeconds": 242.7,
                            "endSeconds": 270.7
                        }
                    ]
                },
                {
                    "isTranscript": True,
                    "id": 3,
                    "name": "barcode type",
                    "appearances": [
                        {
                            "startTime": "0:00:00",
                            "endTime": "0:00:05.134",
                            "startSeconds": 0,
                            "endSeconds": 5.1
                        },
                        {
                            "startTime": "0:00:10.01",
                            "endTime": "0:00:23.6",
                            "startSeconds": 10,
                            "endSeconds": 23.6
                        },
                        {
                            "startTime": "0:00:33",
                            "endTime": "0:00:35.8",
                            "startSeconds": 33,
                            "endSeconds": 35.8
                        },
                        {
                            "startTime": "0:00:39.88",
                            "endTime": "0:00:50.06",
                            "startSeconds": 39.9,
                            "endSeconds": 50.1
                        },
                        {
                            "startTime": "0:00:56",
                            "endTime": "0:01:08.64",
                            "startSeconds": 56,
                            "endSeconds": 68.6
                        },
                        {
                            "startTime": "0:01:11.82",
                            "endTime": "0:01:34.934",
                            "startSeconds": 71.8,
                            "endSeconds": 94.9
                        },
                        {
                            "startTime": "0:01:39.08",
                            "endTime": "0:01:50.65",
                            "startSeconds": 99.1,
                            "endSeconds": 110.6
                        },
                        {
                            "startTime": "0:01:56.4",
                            "endTime": "0:02:05.43",
                            "startSeconds": 116.4,
                            "endSeconds": 125.4
                        },
                        {
                            "startTime": "0:02:16.23",
                            "endTime": "0:02:28.86",
                            "startSeconds": 136.2,
                            "endSeconds": 148.9
                        },
                        {
                            "startTime": "0:02:38.95",
                            "endTime": "0:03:59.23",
                            "startSeconds": 159,
                            "endSeconds": 239.2
                        },
                        {
                            "startTime": "0:04:02.667",
                            "endTime": "0:04:30.734",
                            "startSeconds": 242.7,
                            "endSeconds": 270.7
                        }
                    ]
                },
                {
                    "isTranscript": True,
                    "id": 4,
                    "name": "smaller barcode",
                    "appearances": [
                        {
                            "startTime": "0:00:00",
                            "endTime": "0:00:05.134",
                            "startSeconds": 0,
                            "endSeconds": 5.1
                        },
                        {
                            "startTime": "0:00:10.01",
                            "endTime": "0:00:23.6",
                            "startSeconds": 10,
                            "endSeconds": 23.6
                        },
                        {
                            "startTime": "0:00:33",
                            "endTime": "0:00:35.8",
                            "startSeconds": 33,
                            "endSeconds": 35.8
                        },
                        {
                            "startTime": "0:00:39.88",
                            "endTime": "0:00:50.06",
                            "startSeconds": 39.9,
                            "endSeconds": 50.1
                        },
                        {
                            "startTime": "0:00:56",
                            "endTime": "0:01:08.64",
                            "startSeconds": 56,
                            "endSeconds": 68.6
                        },
                        {
                            "startTime": "0:01:11.82",
                            "endTime": "0:01:34.934",
                            "startSeconds": 71.8,
                            "endSeconds": 94.9
                        },
                        {
                            "startTime": "0:01:39.08",
                            "endTime": "0:01:50.65",
                            "startSeconds": 99.1,
                            "endSeconds": 110.6
                        },
                        {
                            "startTime": "0:01:56.4",
                            "endTime": "0:02:05.43",
                            "startSeconds": 116.4,
                            "endSeconds": 125.4
                        },
                        {
                            "startTime": "0:02:16.23",
                            "endTime": "0:02:28.86",
                            "startSeconds": 136.2,
                            "endSeconds": 148.9
                        },
                        {
                            "startTime": "0:02:38.95",
                            "endTime": "0:03:59.23",
                            "startSeconds": 159,
                            "endSeconds": 239.2
                        },
                        {
                            "startTime": "0:04:02.667",
                            "endTime": "0:04:30.734",
                            "startSeconds": 242.7,
                            "endSeconds": 270.7
                        }
                    ]
                },
                {
                    "isTranscript": True,
                    "id": 5,
                    "name": "barcode product",
                    "appearances": [
                        {
                            "startTime": "0:00:00",
                            "endTime": "0:00:05.134",
                            "startSeconds": 0,
                            "endSeconds": 5.1
                        },
                        {
                            "startTime": "0:00:10.01",
                            "endTime": "0:00:23.6",
                            "startSeconds": 10,
                            "endSeconds": 23.6
                        },
                        {
                            "startTime": "0:00:33",
                            "endTime": "0:00:35.8",
                            "startSeconds": 33,
                            "endSeconds": 35.8
                        },
                        {
                            "startTime": "0:00:39.88",
                            "endTime": "0:01:08.64",
                            "startSeconds": 39.9,
                            "endSeconds": 68.6
                        },
                        {
                            "startTime": "0:01:11.82",
                            "endTime": "0:01:34.934",
                            "startSeconds": 71.8,
                            "endSeconds": 94.9
                        },
                        {
                            "startTime": "0:01:39.08",
                            "endTime": "0:01:50.65",
                            "startSeconds": 99.1,
                            "endSeconds": 110.6
                        },
                        {
                            "startTime": "0:01:56.4",
                            "endTime": "0:02:05.43",
                            "startSeconds": 116.4,
                            "endSeconds": 125.4
                        },
                        {
                            "startTime": "0:02:16.23",
                            "endTime": "0:02:28.86",
                            "startSeconds": 136.2,
                            "endSeconds": 148.9
                        },
                        {
                            "startTime": "0:02:38.95",
                            "endTime": "0:03:59.23",
                            "startSeconds": 159,
                            "endSeconds": 239.2
                        },
                        {
                            "startTime": "0:04:02.667",
                            "endTime": "0:04:30.734",
                            "startSeconds": 242.7,
                            "endSeconds": 270.7
                        }
                    ]
                },
                {
                    "isTranscript": True,
                    "id": 6,
                    "name": "barcode label",
                    "appearances": [
                        {
                            "startTime": "0:00:00",
                            "endTime": "0:00:05.134",
                            "startSeconds": 0,
                            "endSeconds": 5.1
                        },
                        {
                            "startTime": "0:00:10.01",
                            "endTime": "0:00:23.6",
                            "startSeconds": 10,
                            "endSeconds": 23.6
                        },
                        {
                            "startTime": "0:00:33",
                            "endTime": "0:00:35.8",
                            "startSeconds": 33,
                            "endSeconds": 35.8
                        },
                        {
                            "startTime": "0:00:39.88",
                            "endTime": "0:00:50.06",
                            "startSeconds": 39.9,
                            "endSeconds": 50.1
                        },
                        {
                            "startTime": "0:00:56",
                            "endTime": "0:01:08.64",
                            "startSeconds": 56,
                            "endSeconds": 68.6
                        },
                        {
                            "startTime": "0:01:11.82",
                            "endTime": "0:01:34.934",
                            "startSeconds": 71.8,
                            "endSeconds": 94.9
                        },
                        {
                            "startTime": "0:01:39.08",
                            "endTime": "0:01:50.65",
                            "startSeconds": 99.1,
                            "endSeconds": 110.6
                        },
                        {
                            "startTime": "0:01:56.4",
                            "endTime": "0:02:05.43",
                            "startSeconds": 116.4,
                            "endSeconds": 125.4
                        },
                        {
                            "startTime": "0:02:16.23",
                            "endTime": "0:02:28.86",
                            "startSeconds": 136.2,
                            "endSeconds": 148.9
                        },
                        {
                            "startTime": "0:02:38.95",
                            "endTime": "0:03:59.23",
                            "startSeconds": 159,
                            "endSeconds": 239.2
                        },
                        {
                            "startTime": "0:04:02.667",
                            "endTime": "0:04:30.734",
                            "startSeconds": 242.7,
                            "endSeconds": 270.7
                        }
                    ]
                },
                {
                    "isTranscript": True,
                    "id": 7,
                    "name": "barcode teacher",
                    "appearances": [
                        {
                            "startTime": "0:00:00",
                            "endTime": "0:00:05.134",
                            "startSeconds": 0,
                            "endSeconds": 5.1
                        },
                        {
                            "startTime": "0:00:10.01",
                            "endTime": "0:00:23.6",
                            "startSeconds": 10,
                            "endSeconds": 23.6
                        },
                        {
                            "startTime": "0:00:33",
                            "endTime": "0:00:35.8",
                            "startSeconds": 33,
                            "endSeconds": 35.8
                        },
                        {
                            "startTime": "0:00:39.88",
                            "endTime": "0:00:50.06",
                            "startSeconds": 39.9,
                            "endSeconds": 50.1
                        },
                        {
                            "startTime": "0:00:56",
                            "endTime": "0:01:08.64",
                            "startSeconds": 56,
                            "endSeconds": 68.6
                        },
                        {
                            "startTime": "0:01:11.82",
                            "endTime": "0:01:34.934",
                            "startSeconds": 71.8,
                            "endSeconds": 94.9
                        },
                        {
                            "startTime": "0:01:39.08",
                            "endTime": "0:01:50.65",
                            "startSeconds": 99.1,
                            "endSeconds": 110.6
                        },
                        {
                            "startTime": "0:01:56.4",
                            "endTime": "0:02:05.43",
                            "startSeconds": 116.4,
                            "endSeconds": 125.4
                        },
                        {
                            "startTime": "0:02:16.23",
                            "endTime": "0:02:28.86",
                            "startSeconds": 136.2,
                            "endSeconds": 148.9
                        },
                        {
                            "startTime": "0:02:38.95",
                            "endTime": "0:03:59.23",
                            "startSeconds": 159,
                            "endSeconds": 239.2
                        },
                        {
                            "startTime": "0:04:02.667",
                            "endTime": "0:04:30.734",
                            "startSeconds": 242.7,
                            "endSeconds": 270.7
                        }
                    ]
                },
                {
                    "isTranscript": True,
                    "id": 8,
                    "name": "java component",
                    "appearances": [
                        {
                            "startTime": "0:02:43.682",
                            "endTime": "0:02:48.47",
                            "startSeconds": 163.7,
                            "endSeconds": 168.5
                        },
                        {
                            "startTime": "0:03:26.27",
                            "endTime": "0:03:38.11",
                            "startSeconds": 206.3,
                            "endSeconds": 218.1
                        },
                        {
                            "startTime": "0:03:44.99",
                            "endTime": "0:03:59.23",
                            "startSeconds": 225,
                            "endSeconds": 239.2
                        },
                        {
                            "startTime": "0:04:14.27",
                            "endTime": "0:04:23.7",
                            "startSeconds": 254.3,
                            "endSeconds": 263.7
                        }
                    ]
                },
                {
                    "isTranscript": True,
                    "id": 9,
                    "name": "barcode font",
                    "appearances": [
                        {
                            "startTime": "0:00:00",
                            "endTime": "0:00:05.134",
                            "startSeconds": 0,
                            "endSeconds": 5.1
                        },
                        {
                            "startTime": "0:00:10.01",
                            "endTime": "0:00:23.6",
                            "startSeconds": 10,
                            "endSeconds": 23.6
                        },
                        {
                            "startTime": "0:00:33",
                            "endTime": "0:00:35.8",
                            "startSeconds": 33,
                            "endSeconds": 35.8
                        },
                        {
                            "startTime": "0:00:39.88",
                            "endTime": "0:00:50.06",
                            "startSeconds": 39.9,
                            "endSeconds": 50.1
                        },
                        {
                            "startTime": "0:00:56",
                            "endTime": "0:01:08.64",
                            "startSeconds": 56,
                            "endSeconds": 68.6
                        },
                        {
                            "startTime": "0:01:11.82",
                            "endTime": "0:01:34.934",
                            "startSeconds": 71.8,
                            "endSeconds": 94.9
                        },
                        {
                            "startTime": "0:01:39.08",
                            "endTime": "0:01:50.65",
                            "startSeconds": 99.1,
                            "endSeconds": 110.6
                        },
                        {
                            "startTime": "0:01:56.4",
                            "endTime": "0:02:05.43",
                            "startSeconds": 116.4,
                            "endSeconds": 125.4
                        },
                        {
                            "startTime": "0:02:16.23",
                            "endTime": "0:02:28.86",
                            "startSeconds": 136.2,
                            "endSeconds": 148.9
                        },
                        {
                            "startTime": "0:02:38.95",
                            "endTime": "0:03:59.23",
                            "startSeconds": 159,
                            "endSeconds": 239.2
                        },
                        {
                            "startTime": "0:04:02.667",
                            "endTime": "0:04:30.734",
                            "startSeconds": 242.7,
                            "endSeconds": 270.7
                        }
                    ]
                },
                {
                    "isTranscript": True,
                    "id": 10,
                    "name": "font tool",
                    "appearances": [
                        {
                            "startTime": "0:02:38.95",
                            "endTime": "0:02:43.573",
                            "startSeconds": 159,
                            "endSeconds": 163.6
                        },
                        {
                            "startTime": "0:02:48.47",
                            "endTime": "0:03:03.1",
                            "startSeconds": 168.5,
                            "endSeconds": 183.1
                        },
                        {
                            "startTime": "0:03:08.067",
                            "endTime": "0:03:26.27",
                            "startSeconds": 188.1,
                            "endSeconds": 206.3
                        },
                        {
                            "startTime": "0:03:50.86",
                            "endTime": "0:03:59.23",
                            "startSeconds": 230.9,
                            "endSeconds": 239.2
                        },
                        {
                            "startTime": "0:04:14.27",
                            "endTime": "0:04:23.7",
                            "startSeconds": 254.3,
                            "endSeconds": 263.7
                        }
                    ]
                },
                {
                    "isTranscript": True,
                    "id": 11,
                    "name": "barcode applications",
                    "appearances": [
                        {
                            "startTime": "0:00:00",
                            "endTime": "0:00:05.134",
                            "startSeconds": 0,
                            "endSeconds": 5.1
                        },
                        {
                            "startTime": "0:00:10.01",
                            "endTime": "0:00:23.6",
                            "startSeconds": 10,
                            "endSeconds": 23.6
                        },
                        {
                            "startTime": "0:00:33",
                            "endTime": "0:00:35.8",
                            "startSeconds": 33,
                            "endSeconds": 35.8
                        },
                        {
                            "startTime": "0:00:39.88",
                            "endTime": "0:00:50.06",
                            "startSeconds": 39.9,
                            "endSeconds": 50.1
                        },
                        {
                            "startTime": "0:00:56",
                            "endTime": "0:01:08.64",
                            "startSeconds": 56,
                            "endSeconds": 68.6
                        },
                        {
                            "startTime": "0:01:11.82",
                            "endTime": "0:01:34.934",
                            "startSeconds": 71.8,
                            "endSeconds": 94.9
                        },
                        {
                            "startTime": "0:01:39.08",
                            "endTime": "0:01:50.65",
                            "startSeconds": 99.1,
                            "endSeconds": 110.6
                        },
                        {
                            "startTime": "0:01:56.4",
                            "endTime": "0:02:05.43",
                            "startSeconds": 116.4,
                            "endSeconds": 125.4
                        },
                        {
                            "startTime": "0:02:16.23",
                            "endTime": "0:02:28.86",
                            "startSeconds": 136.2,
                            "endSeconds": 148.9
                        },
                        {
                            "startTime": "0:02:38.95",
                            "endTime": "0:04:30.734",
                            "startSeconds": 159,
                            "endSeconds": 270.7
                        }
                    ]
                },
                {
                    "isTranscript": True,
                    "id": 12,
                    "name": "2d barcodes",
                    "appearances": [
                        {
                            "startTime": "0:00:33",
                            "endTime": "0:00:35.8",
                            "startSeconds": 33,
                            "endSeconds": 35.8
                        },
                        {
                            "startTime": "0:00:46.667",
                            "endTime": "0:00:47.6",
                            "startSeconds": 46.7,
                            "endSeconds": 47.6
                        },
                        {
                            "startTime": "0:00:56",
                            "endTime": "0:00:59.734",
                            "startSeconds": 56,
                            "endSeconds": 59.7
                        },
                        {
                            "startTime": "0:01:11.82",
                            "endTime": "0:01:26.6",
                            "startSeconds": 71.8,
                            "endSeconds": 86.6
                        },
                        {
                            "startTime": "0:01:39.08",
                            "endTime": "0:01:50.65",
                            "startSeconds": 99.1,
                            "endSeconds": 110.6
                        },
                        {
                            "startTime": "0:01:56.4",
                            "endTime": "0:02:05.43",
                            "startSeconds": 116.4,
                            "endSeconds": 125.4
                        },
                        {
                            "startTime": "0:02:48.47",
                            "endTime": "0:02:56.38",
                            "startSeconds": 168.5,
                            "endSeconds": 176.4
                        },
                        {
                            "startTime": "0:03:26.27",
                            "endTime": "0:03:58.934",
                            "startSeconds": 206.3,
                            "endSeconds": 238.9
                        },
                        {
                            "startTime": "0:04:08.56",
                            "endTime": "0:04:14.27",
                            "startSeconds": 248.6,
                            "endSeconds": 254.3
                        }
                    ]
                },
                {
                    "isTranscript": True,
                    "id": 13,
                    "name": "linear barcodes",
                    "appearances": [
                        {
                            "startTime": "0:00:33",
                            "endTime": "0:00:35.8",
                            "startSeconds": 33,
                            "endSeconds": 35.8
                        },
                        {
                            "startTime": "0:00:46.667",
                            "endTime": "0:00:47.6",
                            "startSeconds": 46.7,
                            "endSeconds": 47.6
                        },
                        {
                            "startTime": "0:00:56",
                            "endTime": "0:00:59.734",
                            "startSeconds": 56,
                            "endSeconds": 59.7
                        },
                        {
                            "startTime": "0:01:11.82",
                            "endTime": "0:01:26.6",
                            "startSeconds": 71.8,
                            "endSeconds": 86.6
                        },
                        {
                            "startTime": "0:01:30.14",
                            "endTime": "0:01:34.934",
                            "startSeconds": 90.1,
                            "endSeconds": 94.9
                        },
                        {
                            "startTime": "0:01:39.08",
                            "endTime": "0:01:46.4",
                            "startSeconds": 99.1,
                            "endSeconds": 106.4
                        },
                        {
                            "startTime": "0:01:56.4",
                            "endTime": "0:02:00.96",
                            "startSeconds": 116.4,
                            "endSeconds": 121
                        },
                        {
                            "startTime": "0:02:48.47",
                            "endTime": "0:02:56.38",
                            "startSeconds": 168.5,
                            "endSeconds": 176.4
                        },
                        {
                            "startTime": "0:03:26.27",
                            "endTime": "0:03:58.934",
                            "startSeconds": 206.3,
                            "endSeconds": 238.9
                        },
                        {
                            "startTime": "0:04:08.56",
                            "endTime": "0:04:14.27",
                            "startSeconds": 248.6,
                            "endSeconds": 254.3
                        }
                    ]
                },
                {
                    "isTranscript": True,
                    "id": 14,
                    "name": "data matrix",
                    "appearances": [
                        {
                            "startTime": "0:01:11.82",
                            "endTime": "0:01:16.95",
                            "startSeconds": 71.8,
                            "endSeconds": 77
                        },
                        {
                            "startTime": "0:01:35.088",
                            "endTime": "0:01:45.26",
                            "startSeconds": 95.1,
                            "endSeconds": 105.3
                        },
                        {
                            "startTime": "0:01:54.96",
                            "endTime": "0:01:56.4",
                            "startSeconds": 115,
                            "endSeconds": 116.4
                        },
                        {
                            "startTime": "0:02:00.96",
                            "endTime": "0:02:05.43",
                            "startSeconds": 121,
                            "endSeconds": 125.4
                        },
                        {
                            "startTime": "0:02:41.933",
                            "endTime": "0:02:43.8",
                            "startSeconds": 161.9,
                            "endSeconds": 163.8
                        },
                        {
                            "startTime": "0:03:07.6",
                            "endTime": "0:03:25.334",
                            "startSeconds": 187.6,
                            "endSeconds": 205.3
                        },
                        {
                            "startTime": "0:03:50.86",
                            "endTime": "0:03:59.23",
                            "startSeconds": 230.9,
                            "endSeconds": 239.2
                        },
                        {
                            "startTime": "0:04:14.27",
                            "endTime": "0:04:23.7",
                            "startSeconds": 254.3,
                            "endSeconds": 263.7
                        }
                    ]
                },
                {
                    "isTranscript": True,
                    "id": 15,
                    "name": "barcode components",
                    "appearances": [
                        {
                            "startTime": "0:00:00",
                            "endTime": "0:00:05.134",
                            "startSeconds": 0,
                            "endSeconds": 5.1
                        },
                        {
                            "startTime": "0:00:10.01",
                            "endTime": "0:00:23.6",
                            "startSeconds": 10,
                            "endSeconds": 23.6
                        },
                        {
                            "startTime": "0:00:33",
                            "endTime": "0:00:35.8",
                            "startSeconds": 33,
                            "endSeconds": 35.8
                        },
                        {
                            "startTime": "0:00:39.88",
                            "endTime": "0:00:50.06",
                            "startSeconds": 39.9,
                            "endSeconds": 50.1
                        },
                        {
                            "startTime": "0:00:56",
                            "endTime": "0:01:08.64",
                            "startSeconds": 56,
                            "endSeconds": 68.6
                        },
                        {
                            "startTime": "0:01:11.82",
                            "endTime": "0:01:34.934",
                            "startSeconds": 71.8,
                            "endSeconds": 94.9
                        },
                        {
                            "startTime": "0:01:39.08",
                            "endTime": "0:01:50.65",
                            "startSeconds": 99.1,
                            "endSeconds": 110.6
                        },
                        {
                            "startTime": "0:01:56.4",
                            "endTime": "0:02:05.43",
                            "startSeconds": 116.4,
                            "endSeconds": 125.4
                        },
                        {
                            "startTime": "0:02:16.23",
                            "endTime": "0:02:28.86",
                            "startSeconds": 136.2,
                            "endSeconds": 148.9
                        },
                        {
                            "startTime": "0:02:38.95",
                            "endTime": "0:03:59.23",
                            "startSeconds": 159,
                            "endSeconds": 239.2
                        },
                        {
                            "startTime": "0:04:02.667",
                            "endTime": "0:04:30.734",
                            "startSeconds": 242.7,
                            "endSeconds": 270.7
                        }
                    ]
                },
                {
                    "isTranscript": True,
                    "id": 16,
                    "name": "qr code",
                    "appearances": [
                        {
                            "startTime": "0:00:00",
                            "endTime": "0:00:05.134",
                            "startSeconds": 0,
                            "endSeconds": 5.1
                        },
                        {
                            "startTime": "0:00:10.01",
                            "endTime": "0:00:35.8",
                            "startSeconds": 10,
                            "endSeconds": 35.8
                        },
                        {
                            "startTime": "0:00:39.88",
                            "endTime": "0:00:50.06",
                            "startSeconds": 39.9,
                            "endSeconds": 50.1
                        },
                        {
                            "startTime": "0:00:56",
                            "endTime": "0:01:50.65",
                            "startSeconds": 56,
                            "endSeconds": 110.6
                        },
                        {
                            "startTime": "0:01:56.4",
                            "endTime": "0:02:12.33",
                            "startSeconds": 116.4,
                            "endSeconds": 132.3
                        },
                        {
                            "startTime": "0:02:16.23",
                            "endTime": "0:02:28.86",
                            "startSeconds": 136.2,
                            "endSeconds": 148.9
                        },
                        {
                            "startTime": "0:02:38.95",
                            "endTime": "0:04:30.734",
                            "startSeconds": 159,
                            "endSeconds": 270.7
                        }
                    ]
                },
                {
                    "isTranscript": True,
                    "id": 17,
                    "name": "barcode",
                    "appearances": [
                        {
                            "startTime": "0:00:00",
                            "endTime": "0:00:05.134",
                            "startSeconds": 0,
                            "endSeconds": 5.1
                        },
                        {
                            "startTime": "0:00:10.01",
                            "endTime": "0:00:23.6",
                            "startSeconds": 10,
                            "endSeconds": 23.6
                        },
                        {
                            "startTime": "0:00:33",
                            "endTime": "0:00:35.8",
                            "startSeconds": 33,
                            "endSeconds": 35.8
                        },
                        {
                            "startTime": "0:00:39.88",
                            "endTime": "0:00:50.06",
                            "startSeconds": 39.9,
                            "endSeconds": 50.1
                        },
                        {
                            "startTime": "0:00:56",
                            "endTime": "0:01:08.64",
                            "startSeconds": 56,
                            "endSeconds": 68.6
                        },
                        {
                            "startTime": "0:01:11.82",
                            "endTime": "0:01:34.934",
                            "startSeconds": 71.8,
                            "endSeconds": 94.9
                        },
                        {
                            "startTime": "0:01:39.08",
                            "endTime": "0:01:50.65",
                            "startSeconds": 99.1,
                            "endSeconds": 110.6
                        },
                        {
                            "startTime": "0:01:56.4",
                            "endTime": "0:02:05.43",
                            "startSeconds": 116.4,
                            "endSeconds": 125.4
                        },
                        {
                            "startTime": "0:02:16.23",
                            "endTime": "0:02:28.86",
                            "startSeconds": 136.2,
                            "endSeconds": 148.9
                        },
                        {
                            "startTime": "0:02:38.95",
                            "endTime": "0:03:59.23",
                            "startSeconds": 159,
                            "endSeconds": 239.2
                        },
                        {
                            "startTime": "0:04:02.667",
                            "endTime": "0:04:30.734",
                            "startSeconds": 242.7,
                            "endSeconds": 270.7
                        }
                    ]
                },
                {
                    "isTranscript": True,
                    "id": 18,
                    "name": "components",
                    "appearances": [
                        {
                            "startTime": "0:02:43.682",
                            "endTime": "0:02:48.47",
                            "startSeconds": 163.7,
                            "endSeconds": 168.5
                        },
                        {
                            "startTime": "0:03:26.27",
                            "endTime": "0:03:38.11",
                            "startSeconds": 206.3,
                            "endSeconds": 218.1
                        },
                        {
                            "startTime": "0:03:44.99",
                            "endTime": "0:03:59.23",
                            "startSeconds": 225,
                            "endSeconds": 239.2
                        }
                    ]
                },
                {
                    "isTranscript": True,
                    "id": 19,
                    "name": "barcodes",
                    "appearances": [
                        {
                            "startTime": "0:00:33",
                            "endTime": "0:00:35.8",
                            "startSeconds": 33,
                            "endSeconds": 35.8
                        },
                        {
                            "startTime": "0:00:46.667",
                            "endTime": "0:00:47.6",
                            "startSeconds": 46.7,
                            "endSeconds": 47.6
                        },
                        {
                            "startTime": "0:00:56",
                            "endTime": "0:00:59.734",
                            "startSeconds": 56,
                            "endSeconds": 59.7
                        },
                        {
                            "startTime": "0:01:11.82",
                            "endTime": "0:01:26.6",
                            "startSeconds": 71.8,
                            "endSeconds": 86.6
                        },
                        {
                            "startTime": "0:01:39.08",
                            "endTime": "0:01:46.4",
                            "startSeconds": 99.1,
                            "endSeconds": 106.4
                        },
                        {
                            "startTime": "0:02:48.47",
                            "endTime": "0:02:56.38",
                            "startSeconds": 168.5,
                            "endSeconds": 176.4
                        },
                        {
                            "startTime": "0:03:26.27",
                            "endTime": "0:03:58.934",
                            "startSeconds": 206.3,
                            "endSeconds": 238.9
                        },
                        {
                            "startTime": "0:04:08.56",
                            "endTime": "0:04:14.27",
                            "startSeconds": 248.6,
                            "endSeconds": 254.3
                        }
                    ]
                },
                {
                    "isTranscript": True,
                    "id": 21,
                    "name": "data",
                    "appearances": [
                        {
                            "startTime": "0:01:11.82",
                            "endTime": "0:01:16.95",
                            "startSeconds": 71.8,
                            "endSeconds": 77
                        },
                        {
                            "startTime": "0:01:35.088",
                            "endTime": "0:01:45.26",
                            "startSeconds": 95.1,
                            "endSeconds": 105.3
                        },
                        {
                            "startTime": "0:01:54.96",
                            "endTime": "0:01:56.4",
                            "startSeconds": 115,
                            "endSeconds": 116.4
                        },
                        {
                            "startTime": "0:02:00.96",
                            "endTime": "0:02:05.43",
                            "startSeconds": 121,
                            "endSeconds": 125.4
                        },
                        {
                            "startTime": "0:02:41.933",
                            "endTime": "0:02:43.8",
                            "startSeconds": 161.9,
                            "endSeconds": 163.8
                        },
                        {
                            "startTime": "0:03:07.6",
                            "endTime": "0:03:25.334",
                            "startSeconds": 187.6,
                            "endSeconds": 205.3
                        },
                        {
                            "startTime": "0:03:50.86",
                            "endTime": "0:03:59.23",
                            "startSeconds": 230.9,
                            "endSeconds": 239.2
                        },
                        {
                            "startTime": "0:04:14.27",
                            "endTime": "0:04:23.7",
                            "startSeconds": 254.3,
                            "endSeconds": 263.7
                        }
                    ]
                },
                {
                    "isTranscript": True,
                    "id": 22,
                    "name": "code 128",
                    "appearances": [
                        {
                            "startTime": "0:00:00",
                            "endTime": "0:00:05.134",
                            "startSeconds": 0,
                            "endSeconds": 5.1
                        },
                        {
                            "startTime": "0:00:10.01",
                            "endTime": "0:00:35.8",
                            "startSeconds": 10,
                            "endSeconds": 35.8
                        },
                        {
                            "startTime": "0:00:39.88",
                            "endTime": "0:00:50.06",
                            "startSeconds": 39.9,
                            "endSeconds": 50.1
                        },
                        {
                            "startTime": "0:00:56",
                            "endTime": "0:01:50.65",
                            "startSeconds": 56,
                            "endSeconds": 110.6
                        },
                        {
                            "startTime": "0:01:56.4",
                            "endTime": "0:02:12.33",
                            "startSeconds": 116.4,
                            "endSeconds": 132.3
                        },
                        {
                            "startTime": "0:02:16.23",
                            "endTime": "0:02:28.86",
                            "startSeconds": 136.2,
                            "endSeconds": 148.9
                        },
                        {
                            "startTime": "0:02:38.95",
                            "endTime": "0:04:30.734",
                            "startSeconds": 159,
                            "endSeconds": 270.7
                        }
                    ]
                },
                {
                    "isTranscript": True,
                    "id": 23,
                    "name": "code 39",
                    "appearances": [
                        {
                            "startTime": "0:00:00",
                            "endTime": "0:00:05.134",
                            "startSeconds": 0,
                            "endSeconds": 5.1
                        },
                        {
                            "startTime": "0:00:10.01",
                            "endTime": "0:00:35.8",
                            "startSeconds": 10,
                            "endSeconds": 35.8
                        },
                        {
                            "startTime": "0:00:39.88",
                            "endTime": "0:00:50.06",
                            "startSeconds": 39.9,
                            "endSeconds": 50.1
                        },
                        {
                            "startTime": "0:00:56",
                            "endTime": "0:01:50.65",
                            "startSeconds": 56,
                            "endSeconds": 110.6
                        },
                        {
                            "startTime": "0:01:56.4",
                            "endTime": "0:02:12.33",
                            "startSeconds": 116.4,
                            "endSeconds": 132.3
                        },
                        {
                            "startTime": "0:02:16.23",
                            "endTime": "0:02:28.86",
                            "startSeconds": 136.2,
                            "endSeconds": 148.9
                        },
                        {
                            "startTime": "0:02:38.95",
                            "endTime": "0:04:30.734",
                            "startSeconds": 159,
                            "endSeconds": 270.7
                        }
                    ]
                },
                {
                    "isTranscript": True,
                    "id": 24,
                    "name": "application",
                    "appearances": [
                        {
                            "startTime": "0:02:22.46",
                            "endTime": "0:02:48.47",
                            "startSeconds": 142.5,
                            "endSeconds": 168.5
                        },
                        {
                            "startTime": "0:03:35.63",
                            "endTime": "0:03:38.11",
                            "startSeconds": 215.6,
                            "endSeconds": 218.1
                        },
                        {
                            "startTime": "0:03:44.99",
                            "endTime": "0:04:08.56",
                            "startSeconds": 225,
                            "endSeconds": 248.6
                        },
                        {
                            "startTime": "0:04:14.27",
                            "endTime": "0:04:30.667",
                            "startSeconds": 254.3,
                            "endSeconds": 270.7
                        }
                    ]
                },
                {
                    "isTranscript": False,
                    "id": 20,
                    "name": "generate",
                    "appearances": [
                        {
                            "startTime": "0:03:45.4",
                            "endTime": "0:03:58.934",
                            "startSeconds": 225.4,
                            "endSeconds": 238.9
                        },
                        {
                            "startTime": "0:04:14.27",
                            "endTime": "0:04:30.667",
                            "startSeconds": 254.3,
                            "endSeconds": 270.7
                        }
                    ]
                },
                {
                    "isTranscript": False,
                    "id": 25,
                    "name": "tutorial",
                    "appearances": [
                        {
                            "startTime": "0:00:00",
                            "endTime": "0:00:10.01",
                            "startSeconds": 0,
                            "endSeconds": 10
                        }
                    ]
                },
                {
                    "isTranscript": False,
                    "id": 26,
                    "name": "barcoding",
                    "appearances": [
                        {
                            "startTime": "0:00:06.533",
                            "endTime": "0:00:21.067",
                            "startSeconds": 6.5,
                            "endSeconds": 21.1
                        },
                        {
                            "startTime": "0:00:55.32",
                            "endTime": "0:01:00.32",
                            "startSeconds": 55.3,
                            "endSeconds": 60.3
                        }
                    ]
                },
                {
                    "isTranscript": False,
                    "id": 27,
                    "name": "protocol",
                    "appearances": [
                        {
                            "startTime": "0:01:03.467",
                            "endTime": "0:01:08.64",
                            "startSeconds": 63.5,
                            "endSeconds": 68.6
                        }
                    ]
                },
                {
                    "isTranscript": False,
                    "id": 28,
                    "name": "spaces",
                    "appearances": [
                        {
                            "startTime": "0:01:03.467",
                            "endTime": "0:01:08.64",
                            "startSeconds": 63.5,
                            "endSeconds": 68.6
                        }
                    ]
                },
                {
                    "isTranscript": False,
                    "id": 29,
                    "name": "make",
                    "appearances": [
                        {
                            "startTime": "0:01:03.467",
                            "endTime": "0:01:08.64",
                            "startSeconds": 63.5,
                            "endSeconds": 68.6
                        }
                    ]
                },
                {
                    "isTranscript": False,
                    "id": 30,
                    "name": "kind",
                    "appearances": [
                        {
                            "startTime": "0:01:03.467",
                            "endTime": "0:01:08.64",
                            "startSeconds": 63.5,
                            "endSeconds": 68.6
                        }
                    ]
                }
            ],
            "sentiments": [
                {
                    "sentimentKey": "Negative",
                    "seenDurationRatio": 0.0364,
                    "appearances": [
                        {
                            "startTime": "0:00:31.11",
                            "endTime": "0:00:32.44",
                            "startSeconds": 31.1,
                            "endSeconds": 32.4
                        },
                        {
                            "startTime": "0:01:56.4",
                            "endTime": "0:01:59.804",
                            "startSeconds": 116.4,
                            "endSeconds": 119.8
                        },
                        {
                            "startTime": "0:02:28.86",
                            "endTime": "0:02:32.22",
                            "startSeconds": 148.9,
                            "endSeconds": 152.2
                        },
                        {
                            "startTime": "0:03:21.032",
                            "endTime": "0:03:22.89",
                            "startSeconds": 201,
                            "endSeconds": 202.9
                        }
                    ]
                },
                {
                    "sentimentKey": "Neutral",
                    "seenDurationRatio": 0.8415,
                    "appearances": [
                        {
                            "startTime": "0:00:10.01",
                            "endTime": "0:01:50.65",
                            "startSeconds": 10,
                            "endSeconds": 110.6
                        },
                        {
                            "startTime": "0:01:54.96",
                            "endTime": "0:01:56.4",
                            "startSeconds": 115,
                            "endSeconds": 116.4
                        },
                        {
                            "startTime": "0:01:59.868",
                            "endTime": "0:02:28.86",
                            "startSeconds": 119.9,
                            "endSeconds": 148.9
                        },
                        {
                            "startTime": "0:02:32.22",
                            "endTime": "0:02:58.72",
                            "startSeconds": 152.2,
                            "endSeconds": 178.7
                        },
                        {
                            "startTime": "0:03:02.245",
                            "endTime": "0:03:03.1",
                            "startSeconds": 182.2,
                            "endSeconds": 183.1
                        },
                        {
                            "startTime": "0:03:06.496",
                            "endTime": "0:03:28.65",
                            "startSeconds": 186.5,
                            "endSeconds": 208.6
                        },
                        {
                            "startTime": "0:03:32.564",
                            "endTime": "0:03:38.11",
                            "startSeconds": 212.6,
                            "endSeconds": 218.1
                        },
                        {
                            "startTime": "0:03:41.93",
                            "endTime": "0:03:44.99",
                            "startSeconds": 221.9,
                            "endSeconds": 225
                        },
                        {
                            "startTime": "0:03:48.973",
                            "endTime": "0:04:28.79",
                            "startSeconds": 229,
                            "endSeconds": 268.8
                        }
                    ]
                },
                {
                    "sentimentKey": "Positive",
                    "seenDurationRatio": 0.1301,
                    "appearances": [
                        {
                            "startTime": "0:00:05.17",
                            "endTime": "0:00:10.01",
                            "startSeconds": 5.2,
                            "endSeconds": 10
                        },
                        {
                            "startTime": "0:00:58.2",
                            "endTime": "0:01:00.32",
                            "startSeconds": 58.2,
                            "endSeconds": 60.3
                        },
                        {
                            "startTime": "0:02:19.66",
                            "endTime": "0:02:26.38",
                            "startSeconds": 139.7,
                            "endSeconds": 146.4
                        },
                        {
                            "startTime": "0:02:58.72",
                            "endTime": "0:03:06.431",
                            "startSeconds": 178.7,
                            "endSeconds": 186.4
                        },
                        {
                            "startTime": "0:03:28.65",
                            "endTime": "0:03:32.499",
                            "startSeconds": 208.6,
                            "endSeconds": 212.5
                        },
                        {
                            "startTime": "0:03:38.11",
                            "endTime": "0:03:41.93",
                            "startSeconds": 218.1,
                            "endSeconds": 221.9
                        },
                        {
                            "startTime": "0:03:44.99",
                            "endTime": "0:03:48.921",
                            "startSeconds": 225,
                            "endSeconds": 228.9
                        },
                        {
                            "startTime": "0:04:11.772",
                            "endTime": "0:04:14.27",
                            "startSeconds": 251.8,
                            "endSeconds": 254.3
                        }
                    ]
                }
            ],
            "emotions": [],
            "audioEffects": [
                {
                    "audioEffectKey": "Silence",
                    "seenDurationRatio": 0.0426,
                    "seenDuration": 11.6,
                    "appearances": [
                        {
                            "confidence": 1,
                            "startTime": "0:00:00",
                            "endTime": "0:00:05.2",
                            "startSeconds": 0,
                            "endSeconds": 5.2
                        },
                        {
                            "confidence": 1,
                            "startTime": "0:01:51.85",
                            "endTime": "0:01:55.05",
                            "startSeconds": 111.8,
                            "endSeconds": 115
                        },
                        {
                            "confidence": 1,
                            "startTime": "0:04:28.79",
                            "endTime": "0:04:32",
                            "startSeconds": 268.8,
                            "endSeconds": 272
                        }
                    ]
                }
            ],
            "labels": [
                {
                    "id": 2,
                    "name": "screenshot",
                    "appearances": [
                        {
                            "confidence": 0.9204,
                            "startTime": "0:00:00",
                            "endTime": "0:00:27.733",
                            "startSeconds": 0,
                            "endSeconds": 27.7
                        },
                        {
                            "confidence": 0.9937,
                            "startTime": "0:00:42.667",
                            "endTime": "0:01:23.2",
                            "startSeconds": 42.7,
                            "endSeconds": 83.2
                        },
                        {
                            "confidence": 0.9743,
                            "startTime": "0:01:27.467",
                            "endTime": "0:04:31.866",
                            "startSeconds": 87.5,
                            "endSeconds": 271.9
                        }
                    ]
                },
                {
                    "id": 1,
                    "name": "text",
                    "appearances": [
                        {
                            "confidence": 1,
                            "startTime": "0:00:00",
                            "endTime": "0:00:23.466",
                            "startSeconds": 0,
                            "endSeconds": 23.5
                        },
                        {
                            "confidence": 0.8565,
                            "startTime": "0:00:27.733",
                            "endTime": "0:00:29.866",
                            "startSeconds": 27.7,
                            "endSeconds": 29.9
                        },
                        {
                            "confidence": 0.92,
                            "startTime": "0:00:36.267",
                            "endTime": "0:00:38.4",
                            "startSeconds": 36.3,
                            "endSeconds": 38.4
                        },
                        {
                            "confidence": 0.9087,
                            "startTime": "0:00:42.667",
                            "endTime": "0:01:55.2",
                            "startSeconds": 42.7,
                            "endSeconds": 115.2
                        },
                        {
                            "confidence": 0.9999,
                            "startTime": "0:02:03.733",
                            "endTime": "0:04:31.866",
                            "startSeconds": 123.7,
                            "endSeconds": 271.9
                        }
                    ]
                },
                {
                    "id": 5,
                    "name": "design",
                    "appearances": [
                        {
                            "confidence": 0.9936,
                            "startTime": "0:00:08.533",
                            "endTime": "0:00:23.466",
                            "startSeconds": 8.5,
                            "endSeconds": 23.5
                        },
                        {
                            "confidence": 0.9924,
                            "startTime": "0:00:42.667",
                            "endTime": "0:00:53.333",
                            "startSeconds": 42.7,
                            "endSeconds": 53.3
                        },
                        {
                            "confidence": 0.9909,
                            "startTime": "0:00:57.6",
                            "endTime": "0:01:04",
                            "startSeconds": 57.6,
                            "endSeconds": 64
                        },
                        {
                            "confidence": 0.9983,
                            "startTime": "0:01:10.4",
                            "endTime": "0:01:14.666",
                            "startSeconds": 70.4,
                            "endSeconds": 74.7
                        },
                        {
                            "confidence": 0.9938,
                            "startTime": "0:01:18.933",
                            "endTime": "0:01:27.466",
                            "startSeconds": 78.9,
                            "endSeconds": 87.5
                        },
                        {
                            "confidence": 0.9926,
                            "startTime": "0:01:31.733",
                            "endTime": "0:01:50.933",
                            "startSeconds": 91.7,
                            "endSeconds": 110.9
                        },
                        {
                            "confidence": 0.999,
                            "startTime": "0:01:55.2",
                            "endTime": "0:02:01.6",
                            "startSeconds": 115.2,
                            "endSeconds": 121.6
                        },
                        {
                            "confidence": 0.9965,
                            "startTime": "0:02:05.867",
                            "endTime": "0:04:31.866",
                            "startSeconds": 125.9,
                            "endSeconds": 271.9
                        }
                    ]
                },
                {
                    "id": 6,
                    "name": "graphic",
                    "appearances": [
                        {
                            "confidence": 0.9889,
                            "startTime": "0:00:08.533",
                            "endTime": "0:00:23.466",
                            "startSeconds": 8.5,
                            "endSeconds": 23.5
                        },
                        {
                            "confidence": 0.9904,
                            "startTime": "0:00:42.667",
                            "endTime": "0:00:46.933",
                            "startSeconds": 42.7,
                            "endSeconds": 46.9
                        },
                        {
                            "confidence": 0.9928,
                            "startTime": "0:00:51.2",
                            "endTime": "0:00:53.333",
                            "startSeconds": 51.2,
                            "endSeconds": 53.3
                        },
                        {
                            "confidence": 0.9871,
                            "startTime": "0:00:57.6",
                            "endTime": "0:01:04",
                            "startSeconds": 57.6,
                            "endSeconds": 64
                        },
                        {
                            "confidence": 0.9934,
                            "startTime": "0:01:10.4",
                            "endTime": "0:01:14.666",
                            "startSeconds": 70.4,
                            "endSeconds": 74.7
                        },
                        {
                            "confidence": 0.992,
                            "startTime": "0:01:18.933",
                            "endTime": "0:01:23.2",
                            "startSeconds": 78.9,
                            "endSeconds": 83.2
                        },
                        {
                            "confidence": 0.9888,
                            "startTime": "0:01:31.733",
                            "endTime": "0:01:50.933",
                            "startSeconds": 91.7,
                            "endSeconds": 110.9
                        },
                        {
                            "confidence": 0.9941,
                            "startTime": "0:01:55.2",
                            "endTime": "0:02:01.6",
                            "startSeconds": 115.2,
                            "endSeconds": 121.6
                        },
                        {
                            "confidence": 0.9966,
                            "startTime": "0:02:05.867",
                            "endTime": "0:04:31.866",
                            "startSeconds": 125.9,
                            "endSeconds": 271.9
                        }
                    ]
                },
                {
                    "id": 20,
                    "name": "sign",
                    "appearances": [
                        {
                            "confidence": 0.9457,
                            "startTime": "0:00:42.667",
                            "endTime": "0:00:46.933",
                            "startSeconds": 42.7,
                            "endSeconds": 46.9
                        },
                        {
                            "confidence": 0.9668,
                            "startTime": "0:00:53.333",
                            "endTime": "0:01:10.4",
                            "startSeconds": 53.3,
                            "endSeconds": 70.4
                        },
                        {
                            "confidence": 0.9651,
                            "startTime": "0:01:14.667",
                            "endTime": "0:01:23.2",
                            "startSeconds": 74.7,
                            "endSeconds": 83.2
                        },
                        {
                            "confidence": 0.9576,
                            "startTime": "0:01:31.733",
                            "endTime": "0:01:33.866",
                            "startSeconds": 91.7,
                            "endSeconds": 93.9
                        },
                        {
                            "confidence": 0.9792,
                            "startTime": "0:01:40.267",
                            "endTime": "0:01:48.8",
                            "startSeconds": 100.3,
                            "endSeconds": 108.8
                        },
                        {
                            "confidence": 0.9509,
                            "startTime": "0:02:22.933",
                            "endTime": "0:02:42.133",
                            "startSeconds": 142.9,
                            "endSeconds": 162.1
                        },
                        {
                            "confidence": 0.9321,
                            "startTime": "0:03:07.733",
                            "endTime": "0:03:24.8",
                            "startSeconds": 187.7,
                            "endSeconds": 204.8
                        },
                        {
                            "confidence": 0.9227,
                            "startTime": "0:03:46.133",
                            "endTime": "0:03:58.933",
                            "startSeconds": 226.1,
                            "endSeconds": 238.9
                        },
                        {
                            "confidence": 0.9572,
                            "startTime": "0:04:18.133",
                            "endTime": "0:04:31.866",
                            "startSeconds": 258.1,
                            "endSeconds": 271.9
                        }
                    ]
                },
                {
                    "id": 4,
                    "name": "red",
                    "appearances": [
                        {
                            "confidence": 0.927,
                            "startTime": "0:00:06.4",
                            "endTime": "0:00:34.133",
                            "startSeconds": 6.4,
                            "endSeconds": 34.1
                        },
                        {
                            "confidence": 0.9396,
                            "startTime": "0:00:40.533",
                            "endTime": "0:00:42.666",
                            "startSeconds": 40.5,
                            "endSeconds": 42.7
                        },
                        {
                            "confidence": 0.9274,
                            "startTime": "0:00:51.2",
                            "endTime": "0:01:04",
                            "startSeconds": 51.2,
                            "endSeconds": 64
                        },
                        {
                            "confidence": 0.8795,
                            "startTime": "0:01:12.533",
                            "endTime": "0:01:23.2",
                            "startSeconds": 72.5,
                            "endSeconds": 83.2
                        },
                        {
                            "confidence": 0.9001,
                            "startTime": "0:01:33.867",
                            "endTime": "0:01:36",
                            "startSeconds": 93.9,
                            "endSeconds": 96
                        },
                        {
                            "confidence": 0.8871,
                            "startTime": "0:01:40.267",
                            "endTime": "0:01:42.4",
                            "startSeconds": 100.3,
                            "endSeconds": 102.4
                        },
                        {
                            "confidence": 0.8856,
                            "startTime": "0:01:50.933",
                            "endTime": "0:01:55.2",
                            "startSeconds": 110.9,
                            "endSeconds": 115.2
                        },
                        {
                            "confidence": 0.9319,
                            "startTime": "0:02:01.6",
                            "endTime": "0:02:05.866",
                            "startSeconds": 121.6,
                            "endSeconds": 125.9
                        },
                        {
                            "confidence": 0.9058,
                            "startTime": "0:02:48.533",
                            "endTime": "0:03:07.733",
                            "startSeconds": 168.5,
                            "endSeconds": 187.7
                        }
                    ]
                },
                {
                    "id": 25,
                    "name": "logo",
                    "appearances": [
                        {
                            "confidence": 0.9473,
                            "startTime": "0:01:10.4",
                            "endTime": "0:01:12.533",
                            "startSeconds": 70.4,
                            "endSeconds": 72.5
                        },
                        {
                            "confidence": 0.9003,
                            "startTime": "0:02:48.533",
                            "endTime": "0:03:09.866",
                            "startSeconds": 168.5,
                            "endSeconds": 189.9
                        },
                        {
                            "confidence": 0.8454,
                            "startTime": "0:03:22.667",
                            "endTime": "0:03:26.933",
                            "startSeconds": 202.7,
                            "endSeconds": 206.9
                        },
                        {
                            "confidence": 0.8785,
                            "startTime": "0:03:46.133",
                            "endTime": "0:04:18.133",
                            "startSeconds": 226.1,
                            "endSeconds": 258.1
                        },
                        {
                            "confidence": 0.8234,
                            "startTime": "0:04:30.933",
                            "endTime": "0:04:31.866",
                            "startSeconds": 270.9,
                            "endSeconds": 271.9
                        }
                    ]
                },
                {
                    "id": 42,
                    "name": "internet",
                    "appearances": [
                        {
                            "confidence": 0.9874,
                            "startTime": "0:02:14.4",
                            "endTime": "0:02:25.066",
                            "startSeconds": 134.4,
                            "endSeconds": 145.1
                        },
                        {
                            "confidence": 0.9889,
                            "startTime": "0:03:09.867",
                            "endTime": "0:03:26.933",
                            "startSeconds": 189.9,
                            "endSeconds": 206.9
                        },
                        {
                            "confidence": 0.9855,
                            "startTime": "0:03:46.133",
                            "endTime": "0:03:58.933",
                            "startSeconds": 226.1,
                            "endSeconds": 238.9
                        },
                        {
                            "confidence": 0.9905,
                            "startTime": "0:04:18.133",
                            "endTime": "0:04:30.933",
                            "startSeconds": 258.1,
                            "endSeconds": 270.9
                        }
                    ]
                },
                {
                    "id": 21,
                    "name": "font",
                    "appearances": [
                        {
                            "confidence": 0.9234,
                            "startTime": "0:00:42.667",
                            "endTime": "0:00:46.933",
                            "startSeconds": 42.7,
                            "endSeconds": 46.9
                        },
                        {
                            "confidence": 0.9407,
                            "startTime": "0:00:51.2",
                            "endTime": "0:00:53.333",
                            "startSeconds": 51.2,
                            "endSeconds": 53.3
                        },
                        {
                            "confidence": 0.9222,
                            "startTime": "0:01:01.867",
                            "endTime": "0:01:14.666",
                            "startSeconds": 61.9,
                            "endSeconds": 74.7
                        },
                        {
                            "confidence": 0.913,
                            "startTime": "0:01:18.933",
                            "endTime": "0:01:23.2",
                            "startSeconds": 78.9,
                            "endSeconds": 83.2
                        },
                        {
                            "confidence": 0.9126,
                            "startTime": "0:01:31.733",
                            "endTime": "0:01:33.866",
                            "startSeconds": 91.7,
                            "endSeconds": 93.9
                        },
                        {
                            "confidence": 0.9133,
                            "startTime": "0:01:38.133",
                            "endTime": "0:01:42.4",
                            "startSeconds": 98.1,
                            "endSeconds": 102.4
                        },
                        {
                            "confidence": 0.9093,
                            "startTime": "0:01:48.8",
                            "endTime": "0:01:50.933",
                            "startSeconds": 108.8,
                            "endSeconds": 110.9
                        },
                        {
                            "confidence": 0.912,
                            "startTime": "0:01:55.2",
                            "endTime": "0:02:01.6",
                            "startSeconds": 115.2,
                            "endSeconds": 121.6
                        },
                        {
                            "confidence": 0.9143,
                            "startTime": "0:03:22.667",
                            "endTime": "0:03:26.933",
                            "startSeconds": 202.7,
                            "endSeconds": 206.9
                        },
                        {
                            "confidence": 0.9109,
                            "startTime": "0:04:30.933",
                            "endTime": "0:04:31.866",
                            "startSeconds": 270.9,
                            "endSeconds": 271.9
                        }
                    ]
                },
                {
                    "id": 13,
                    "name": "clothing",
                    "appearances": [
                        {
                            "confidence": 0.9484,
                            "startTime": "0:00:32",
                            "endTime": "0:00:42.666",
                            "startSeconds": 32,
                            "endSeconds": 42.7
                        },
                        {
                            "confidence": 0.8779,
                            "startTime": "0:00:55.467",
                            "endTime": "0:01:01.866",
                            "startSeconds": 55.5,
                            "endSeconds": 61.9
                        },
                        {
                            "confidence": 0.901,
                            "startTime": "0:01:16.8",
                            "endTime": "0:01:18.933",
                            "startSeconds": 76.8,
                            "endSeconds": 78.9
                        },
                        {
                            "confidence": 0.9302,
                            "startTime": "0:01:27.467",
                            "endTime": "0:01:31.733",
                            "startSeconds": 87.5,
                            "endSeconds": 91.7
                        },
                        {
                            "confidence": 0.8869,
                            "startTime": "0:01:50.933",
                            "endTime": "0:01:55.2",
                            "startSeconds": 110.9,
                            "endSeconds": 115.2
                        },
                        {
                            "confidence": 0.9206,
                            "startTime": "0:02:01.6",
                            "endTime": "0:02:05.866",
                            "startSeconds": 121.6,
                            "endSeconds": 125.9
                        }
                    ]
                },
                {
                    "id": 7,
                    "name": "fabric",
                    "appearances": [
                        {
                            "confidence": 0.9642,
                            "startTime": "0:00:23.467",
                            "endTime": "0:00:25.6",
                            "startSeconds": 23.5,
                            "endSeconds": 25.6
                        },
                        {
                            "confidence": 0.968,
                            "startTime": "0:00:32",
                            "endTime": "0:00:34.133",
                            "startSeconds": 32,
                            "endSeconds": 34.1
                        },
                        {
                            "confidence": 0.9647,
                            "startTime": "0:00:40.533",
                            "endTime": "0:00:42.666",
                            "startSeconds": 40.5,
                            "endSeconds": 42.7
                        },
                        {
                            "confidence": 0.9645,
                            "startTime": "0:00:55.467",
                            "endTime": "0:01:01.866",
                            "startSeconds": 55.5,
                            "endSeconds": 61.9
                        },
                        {
                            "confidence": 0.9751,
                            "startTime": "0:01:16.8",
                            "endTime": "0:01:18.933",
                            "startSeconds": 76.8,
                            "endSeconds": 78.9
                        },
                        {
                            "confidence": 0.984,
                            "startTime": "0:01:50.933",
                            "endTime": "0:01:53.066",
                            "startSeconds": 110.9,
                            "endSeconds": 113.1
                        },
                        {
                            "confidence": 0.9748,
                            "startTime": "0:02:01.6",
                            "endTime": "0:02:05.866",
                            "startSeconds": 121.6,
                            "endSeconds": 125.9
                        }
                    ]
                },
                {
                    "id": 8,
                    "name": "maroon",
                    "appearances": [
                        {
                            "confidence": 0.9184,
                            "startTime": "0:00:23.467",
                            "endTime": "0:00:25.6",
                            "startSeconds": 23.5,
                            "endSeconds": 25.6
                        },
                        {
                            "confidence": 0.9151,
                            "startTime": "0:00:32",
                            "endTime": "0:00:34.133",
                            "startSeconds": 32,
                            "endSeconds": 34.1
                        },
                        {
                            "confidence": 0.9086,
                            "startTime": "0:00:40.533",
                            "endTime": "0:00:42.666",
                            "startSeconds": 40.5,
                            "endSeconds": 42.7
                        },
                        {
                            "confidence": 0.9124,
                            "startTime": "0:00:55.467",
                            "endTime": "0:01:01.866",
                            "startSeconds": 55.5,
                            "endSeconds": 61.9
                        },
                        {
                            "confidence": 0.9307,
                            "startTime": "0:01:50.933",
                            "endTime": "0:01:55.2",
                            "startSeconds": 110.9,
                            "endSeconds": 115.2
                        },
                        {
                            "confidence": 0.9239,
                            "startTime": "0:02:01.6",
                            "endTime": "0:02:05.866",
                            "startSeconds": 121.6,
                            "endSeconds": 125.9
                        }
                    ]
                },
                {
                    "id": 24,
                    "name": "typography",
                    "appearances": [
                        {
                            "confidence": 0.9909,
                            "startTime": "0:00:51.2",
                            "endTime": "0:00:53.333",
                            "startSeconds": 51.2,
                            "endSeconds": 53.3
                        },
                        {
                            "confidence": 0.9898,
                            "startTime": "0:01:10.4",
                            "endTime": "0:01:12.533",
                            "startSeconds": 70.4,
                            "endSeconds": 72.5
                        },
                        {
                            "confidence": 0.9854,
                            "startTime": "0:01:31.733",
                            "endTime": "0:01:42.4",
                            "startSeconds": 91.7,
                            "endSeconds": 102.4
                        },
                        {
                            "confidence": 0.9918,
                            "startTime": "0:01:55.2",
                            "endTime": "0:02:01.6",
                            "startSeconds": 115.2,
                            "endSeconds": 121.6
                        }
                    ]
                },
                {
                    "id": 43,
                    "name": "parallel",
                    "appearances": [
                        {
                            "confidence": 0.9029,
                            "startTime": "0:02:44.267",
                            "endTime": "0:02:46.4",
                            "startSeconds": 164.3,
                            "endSeconds": 166.4
                        },
                        {
                            "confidence": 0.9105,
                            "startTime": "0:03:26.933",
                            "endTime": "0:03:46.133",
                            "startSeconds": 206.9,
                            "endSeconds": 226.1
                        }
                    ]
                },
                {
                    "id": 9,
                    "name": "colorfulness",
                    "appearances": [
                        {
                            "confidence": 0.909,
                            "startTime": "0:00:23.467",
                            "endTime": "0:00:25.6",
                            "startSeconds": 23.5,
                            "endSeconds": 25.6
                        },
                        {
                            "confidence": 0.913,
                            "startTime": "0:00:32",
                            "endTime": "0:00:34.133",
                            "startSeconds": 32,
                            "endSeconds": 34.1
                        },
                        {
                            "confidence": 0.902,
                            "startTime": "0:00:40.533",
                            "endTime": "0:00:42.666",
                            "startSeconds": 40.5,
                            "endSeconds": 42.7
                        },
                        {
                            "confidence": 0.9133,
                            "startTime": "0:00:55.467",
                            "endTime": "0:01:01.866",
                            "startSeconds": 55.5,
                            "endSeconds": 61.9
                        },
                        {
                            "confidence": 0.9236,
                            "startTime": "0:01:50.933",
                            "endTime": "0:01:55.2",
                            "startSeconds": 110.9,
                            "endSeconds": 115.2
                        },
                        {
                            "confidence": 0.929,
                            "startTime": "0:02:01.6",
                            "endTime": "0:02:03.733",
                            "startSeconds": 121.6,
                            "endSeconds": 123.7
                        }
                    ]
                },
                {
                    "id": 41,
                    "name": "template",
                    "appearances": [
                        {
                            "confidence": 0.9898,
                            "startTime": "0:02:12.267",
                            "endTime": "0:02:14.4",
                            "startSeconds": 132.3,
                            "endSeconds": 134.4
                        },
                        {
                            "confidence": 0.9867,
                            "startTime": "0:02:46.4",
                            "endTime": "0:02:48.533",
                            "startSeconds": 166.4,
                            "endSeconds": 168.5
                        },
                        {
                            "confidence": 0.987,
                            "startTime": "0:03:07.733",
                            "endTime": "0:03:09.866",
                            "startSeconds": 187.7,
                            "endSeconds": 189.9
                        },
                        {
                            "confidence": 0.9855,
                            "startTime": "0:04:20.267",
                            "endTime": "0:04:30.933",
                            "startSeconds": 260.3,
                            "endSeconds": 270.9
                        }
                    ]
                },
                {
                    "id": 23,
                    "name": "rectangle",
                    "appearances": [
                        {
                            "confidence": 0.9068,
                            "startTime": "0:00:42.667",
                            "endTime": "0:00:44.8",
                            "startSeconds": 42.7,
                            "endSeconds": 44.8
                        },
                        {
                            "confidence": 0.9442,
                            "startTime": "0:01:10.4",
                            "endTime": "0:01:12.533",
                            "startSeconds": 70.4,
                            "endSeconds": 72.5
                        },
                        {
                            "confidence": 0.9327,
                            "startTime": "0:01:36",
                            "endTime": "0:01:40.266",
                            "startSeconds": 96,
                            "endSeconds": 100.3
                        },
                        {
                            "confidence": 0.9036,
                            "startTime": "0:02:10.133",
                            "endTime": "0:02:12.266",
                            "startSeconds": 130.1,
                            "endSeconds": 132.3
                        },
                        {
                            "confidence": 0.9248,
                            "startTime": "0:02:44.267",
                            "endTime": "0:02:46.4",
                            "startSeconds": 164.3,
                            "endSeconds": 166.4
                        }
                    ]
                },
                {
                    "id": 14,
                    "name": "person",
                    "appearances": [
                        {
                            "confidence": 0.9869,
                            "startTime": "0:00:34.133",
                            "endTime": "0:00:40.533",
                            "startSeconds": 34.1,
                            "endSeconds": 40.5
                        },
                        {
                            "confidence": 0.9859,
                            "startTime": "0:01:27.467",
                            "endTime": "0:01:31.733",
                            "startSeconds": 87.5,
                            "endSeconds": 91.7
                        }
                    ]
                },
                {
                    "id": 3,
                    "name": "player",
                    "appearances": [
                        {
                            "confidence": 0.9504,
                            "startTime": "0:00:06.4",
                            "endTime": "0:00:08.533",
                            "startSeconds": 6.4,
                            "endSeconds": 8.5
                        },
                        {
                            "confidence": 0.9564,
                            "startTime": "0:00:34.133",
                            "endTime": "0:00:40.533",
                            "startSeconds": 34.1,
                            "endSeconds": 40.5
                        }
                    ]
                },
                {
                    "id": 16,
                    "name": "human face",
                    "appearances": [
                        {
                            "confidence": 0.9714,
                            "startTime": "0:00:34.133",
                            "endTime": "0:00:40.533",
                            "startSeconds": 34.1,
                            "endSeconds": 40.5
                        },
                        {
                            "confidence": 0.9709,
                            "startTime": "0:01:27.467",
                            "endTime": "0:01:29.6",
                            "startSeconds": 87.5,
                            "endSeconds": 89.6
                        }
                    ]
                },
                {
                    "id": 27,
                    "name": "graphic design",
                    "appearances": [
                        {
                            "confidence": 0.9302,
                            "startTime": "0:01:10.4",
                            "endTime": "0:01:12.533",
                            "startSeconds": 70.4,
                            "endSeconds": 72.5
                        },
                        {
                            "confidence": 0.9854,
                            "startTime": "0:02:12.267",
                            "endTime": "0:02:14.4",
                            "startSeconds": 132.3,
                            "endSeconds": 134.4
                        },
                        {
                            "confidence": 0.9866,
                            "startTime": "0:03:07.733",
                            "endTime": "0:03:09.866",
                            "startSeconds": 187.7,
                            "endSeconds": 189.9
                        }
                    ]
                },
                {
                    "id": 15,
                    "name": "racket",
                    "appearances": [
                        {
                            "confidence": 0.9731,
                            "startTime": "0:00:34.133",
                            "endTime": "0:00:40.533",
                            "startSeconds": 34.1,
                            "endSeconds": 40.5
                        }
                    ]
                },
                {
                    "id": 17,
                    "name": "woman",
                    "appearances": [
                        {
                            "confidence": 0.951,
                            "startTime": "0:00:34.133",
                            "endTime": "0:00:40.533",
                            "startSeconds": 34.1,
                            "endSeconds": 40.5
                        }
                    ]
                },
                {
                    "id": 18,
                    "name": "dress",
                    "appearances": [
                        {
                            "confidence": 0.9288,
                            "startTime": "0:00:34.133",
                            "endTime": "0:00:40.533",
                            "startSeconds": 34.1,
                            "endSeconds": 40.5
                        }
                    ]
                },
                {
                    "id": 19,
                    "name": "female",
                    "appearances": [
                        {
                            "confidence": 0.9016,
                            "startTime": "0:00:34.133",
                            "endTime": "0:00:40.533",
                            "startSeconds": 34.1,
                            "endSeconds": 40.5
                        }
                    ]
                },
                {
                    "id": 44,
                    "name": "line",
                    "appearances": [
                        {
                            "confidence": 0.9009,
                            "startTime": "0:03:26.933",
                            "endTime": "0:03:31.2",
                            "startSeconds": 206.9,
                            "endSeconds": 211.2
                        },
                        {
                            "confidence": 0.9001,
                            "startTime": "0:03:44",
                            "endTime": "0:03:46.133",
                            "startSeconds": 224,
                            "endSeconds": 226.1
                        }
                    ]
                },
                {
                    "id": 39,
                    "name": "pattern",
                    "appearances": [
                        {
                            "confidence": 0.9093,
                            "startTime": "0:01:50.933",
                            "endTime": "0:01:53.066",
                            "startSeconds": 110.9,
                            "endSeconds": 113.1
                        },
                        {
                            "confidence": 0.9283,
                            "startTime": "0:02:10.133",
                            "endTime": "0:02:12.266",
                            "startSeconds": 130.1,
                            "endSeconds": 132.3
                        }
                    ]
                },
                {
                    "id": 10,
                    "name": "train",
                    "appearances": [
                        {
                            "confidence": 0.9923,
                            "startTime": "0:00:27.733",
                            "endTime": "0:00:32",
                            "startSeconds": 27.7,
                            "endSeconds": 32
                        }
                    ]
                },
                {
                    "id": 11,
                    "name": "vehicle",
                    "appearances": [
                        {
                            "confidence": 0.9632,
                            "startTime": "0:00:27.733",
                            "endTime": "0:00:32",
                            "startSeconds": 27.7,
                            "endSeconds": 32
                        }
                    ]
                },
                {
                    "id": 12,
                    "name": "land vehicle",
                    "appearances": [
                        {
                            "confidence": 0.9108,
                            "startTime": "0:00:27.733",
                            "endTime": "0:00:32",
                            "startSeconds": 27.7,
                            "endSeconds": 32
                        }
                    ]
                },
                {
                    "id": 28,
                    "name": "cup",
                    "appearances": [
                        {
                            "confidence": 0.9568,
                            "startTime": "0:01:23.2",
                            "endTime": "0:01:27.466",
                            "startSeconds": 83.2,
                            "endSeconds": 87.5
                        }
                    ]
                },
                {
                    "id": 29,
                    "name": "book",
                    "appearances": [
                        {
                            "confidence": 0.9633,
                            "startTime": "0:01:23.2",
                            "endTime": "0:01:27.466",
                            "startSeconds": 83.2,
                            "endSeconds": 87.5
                        }
                    ]
                },
                {
                    "id": 30,
                    "name": "computer",
                    "appearances": [
                        {
                            "confidence": 0.8773,
                            "startTime": "0:01:23.2",
                            "endTime": "0:01:27.466",
                            "startSeconds": 83.2,
                            "endSeconds": 87.5
                        }
                    ]
                },
                {
                    "id": 40,
                    "name": "illustration",
                    "appearances": [
                        {
                            "confidence": 0.9869,
                            "startTime": "0:02:10.133",
                            "endTime": "0:02:12.266",
                            "startSeconds": 130.1,
                            "endSeconds": 132.3
                        }
                    ]
                },
                {
                    "id": 32,
                    "name": "indoor",
                    "appearances": [
                        {
                            "confidence": 0.893,
                            "startTime": "0:01:25.333",
                            "endTime": "0:01:27.466",
                            "startSeconds": 85.3,
                            "endSeconds": 87.5
                        }
                    ]
                },
                {
                    "id": 33,
                    "name": "desk",
                    "appearances": [
                        {
                            "confidence": 0.843,
                            "startTime": "0:01:25.333",
                            "endTime": "0:01:27.466",
                            "startSeconds": 85.3,
                            "endSeconds": 87.5
                        }
                    ]
                },
                {
                    "id": 34,
                    "name": "kitchen appliance",
                    "appearances": [
                        {
                            "confidence": 0.823,
                            "startTime": "0:01:25.333",
                            "endTime": "0:01:27.466",
                            "startSeconds": 85.3,
                            "endSeconds": 87.5
                        }
                    ]
                },
                {
                    "id": 35,
                    "name": "microwave",
                    "appearances": [
                        {
                            "confidence": 0.8153,
                            "startTime": "0:01:25.333",
                            "endTime": "0:01:27.466",
                            "startSeconds": 85.3,
                            "endSeconds": 87.5
                        }
                    ]
                },
                {
                    "id": 22,
                    "name": "poster",
                    "appearances": [
                        {
                            "confidence": 0.9081,
                            "startTime": "0:00:42.667",
                            "endTime": "0:00:44.8",
                            "startSeconds": 42.7,
                            "endSeconds": 44.8
                        }
                    ]
                },
                {
                    "id": 26,
                    "name": "graphics",
                    "appearances": [
                        {
                            "confidence": 0.9372,
                            "startTime": "0:01:10.4",
                            "endTime": "0:01:12.533",
                            "startSeconds": 70.4,
                            "endSeconds": 72.5
                        }
                    ]
                },
                {
                    "id": 31,
                    "name": "keyboard",
                    "appearances": [
                        {
                            "confidence": 0.8829,
                            "startTime": "0:01:23.2",
                            "endTime": "0:01:25.333",
                            "startSeconds": 83.2,
                            "endSeconds": 85.3
                        }
                    ]
                },
                {
                    "id": 36,
                    "name": "man",
                    "appearances": [
                        {
                            "confidence": 0.9072,
                            "startTime": "0:01:27.467",
                            "endTime": "0:01:29.6",
                            "startSeconds": 87.5,
                            "endSeconds": 89.6
                        }
                    ]
                },
                {
                    "id": 37,
                    "name": "hair",
                    "appearances": [
                        {
                            "confidence": 0.8585,
                            "startTime": "0:01:27.467",
                            "endTime": "0:01:29.6",
                            "startSeconds": 87.5,
                            "endSeconds": 89.6
                        }
                    ]
                },
                {
                    "id": 38,
                    "name": "comb",
                    "appearances": [
                        {
                            "confidence": 0.8767,
                            "startTime": "0:01:36",
                            "endTime": "0:01:38.133",
                            "startSeconds": 96,
                            "endSeconds": 98.1
                        }
                    ]
                }
            ],
            "framePatterns": [
                {
                    "id": 1,
                    "name": "RollingCredits",
                    "appearances": [
                        {
                            "startTime": "0:03:45",
                            "endTime": "0:04:31",
                            "startSeconds": 225,
                            "endSeconds": 271
                        }
                    ]
                },
                {
                    "id": 2,
                    "name": "Black",
                    "appearances": [
                        {
                            "startTime": "0:00:23.8667",
                            "endTime": "0:00:23.9333",
                            "startSeconds": 23.9,
                            "endSeconds": 23.9
                        },
                        {
                            "startTime": "0:01:54.267",
                            "endTime": "0:02:00.8",
                            "startSeconds": 114.3,
                            "endSeconds": 120.8
                        }
                    ]
                }
            ],
            "brands": [
                {
                    "referenceId": "Java_(software_platform)",
                    "referenceUrl": "http://en.wikipedia.org/wiki/Java_(software_platform)",
                    "confidence": 1,
                    "description": "Java is a set of computer software and specifications developed by Sun Microsystems, which was later acquired by the Oracle Corporation, that provides a system for developing application software and deploying it in a cross-platform computing environment. Java is used in a wide variety of computing platforms from embedded devices and mobile phones to enterprise servers and supercomputers.",
                    "seenDuration": 13.5,
                    "id": 2,
                    "name": "Java",
                    "appearances": [
                        {
                            "startTime": "0:03:45.4",
                            "endTime": "0:03:58.934",
                            "startSeconds": 225.4,
                            "endSeconds": 238.9
                        }
                    ]
                },
                {
                    "referenceId": "ActiveX",
                    "referenceUrl": "http://en.wikipedia.org/wiki/ActiveX",
                    "confidence": 0.87,
                    "description": "ActiveX is a software framework created by Microsoft that adapts its earlier Component Object Model (COM) and Object Linking and Embedding (OLE) technologies for content downloaded from a network, particularly in the context of the World Wide Web. It was introduced in 1996 and is commonly used in its Windows operating system.",
                    "seenDuration": 9.3,
                    "id": 1,
                    "name": "ActiveX",
                    "appearances": [
                        {
                            "startTime": "0:03:26.27",
                            "endTime": "0:03:35.63",
                            "startSeconds": 206.3,
                            "endSeconds": 215.6
                        }
                    ]
                }
            ],
            "namedLocations": [],
            "namedPeople": [],
            "statistics": {
                "correspondenceCount": 0,
                "speakerTalkToListenRatio": {
                    "1": 1
                },
                "speakerLongestMonolog": {
                    "1": 258
                },
                "speakerNumberOfFragments": {
                    "1": 6
                },
                "speakerWordCount": {
                    "1": 640
                }
            },
            "topics": [
                {
                    "referenceUrl": "https://en.wikipedia.org/wiki/Category:Barcodes",
                    "iptcName": "Economy, Business and Finance/consumer goods",
                    "iabName": "Shopping",
                    "confidence": 1,
                    "id": 1,
                    "name": "Shopping/Barcodes",
                    "appearances": [
                        {
                            "startTime": "0:00:00",
                            "endTime": "0:04:30.734",
                            "startSeconds": 0,
                            "endSeconds": 270.7
                        }
                    ]
                },
                {
                    "referenceUrl": None,
                    "iptcName": "Education",
                    "iabName": "Education",
                    "confidence": 0.995,
                    "id": 2,
                    "name": "Education/Technology",
                    "appearances": [
                        {
                            "startTime": "0:00:00",
                            "endTime": "0:04:31.867",
                            "startSeconds": 0,
                            "endSeconds": 271.9
                        }
                    ]
                },
                {
                    "referenceUrl": None,
                    "iptcName": None,
                    "iabName": None,
                    "confidence": 0.8077,
                    "id": 3,
                    "name": "Barcode Scanners",
                    "appearances": [
                        {
                            "startTime": "0:01:39.08",
                            "endTime": "0:01:50.65",
                            "startSeconds": 99.1,
                            "endSeconds": 110.6
                        },
                        {
                            "startTime": "0:01:54.96",
                            "endTime": "0:02:16.23",
                            "startSeconds": 115,
                            "endSeconds": 136.2
                        }
                    ]
                },
                {
                    "referenceUrl": "https://en.wikipedia.org/wiki/Category:Automatic_identification_and_data_capture",
                    "iptcName": None,
                    "iabName": None,
                    "confidence": 0.6967,
                    "id": 5,
                    "name": "Automatic identification and data capture",
                    "appearances": [
                        {
                            "startTime": "0:00:00",
                            "endTime": "0:02:05.43",
                            "startSeconds": 0,
                            "endSeconds": 125.4
                        },
                        {
                            "startTime": "0:02:16.23",
                            "endTime": "0:04:30.734",
                            "startSeconds": 136.2,
                            "endSeconds": 270.7
                        }
                    ]
                },
                {
                    "referenceUrl": "https://en.wikipedia.org/wiki/Category:Monotype_typefaces",
                    "iptcName": None,
                    "iabName": None,
                    "confidence": 0.6906,
                    "id": 6,
                    "name": "Monotype typefaces",
                    "appearances": [
                        {
                            "startTime": "0:02:48.47",
                            "endTime": "0:02:58.72",
                            "startSeconds": 168.5,
                            "endSeconds": 178.7
                        }
                    ]
                },
                {
                    "referenceUrl": "https://en.wikipedia.org/wiki/Category:Windows_XP_typefaces",
                    "iptcName": None,
                    "iabName": None,
                    "confidence": 0.6898,
                    "id": 7,
                    "name": "Windows XP typefaces",
                    "appearances": [
                        {
                            "startTime": "0:02:48.47",
                            "endTime": "0:02:58.72",
                            "startSeconds": 168.5,
                            "endSeconds": 178.7
                        }
                    ]
                },
                {
                    "referenceUrl": None,
                    "iptcName": None,
                    "iabName": None,
                    "confidence": 0.6259,
                    "id": 8,
                    "name": "Barcode Readers",
                    "appearances": [
                        {
                            "startTime": "0:00:50.06",
                            "endTime": "0:01:16.95",
                            "startSeconds": 50.1,
                            "endSeconds": 77
                        },
                        {
                            "startTime": "0:01:39.08",
                            "endTime": "0:01:50.65",
                            "startSeconds": 99.1,
                            "endSeconds": 110.6
                        },
                        {
                            "startTime": "0:01:54.96",
                            "endTime": "0:03:07.28",
                            "startSeconds": 115,
                            "endSeconds": 187.3
                        },
                        {
                            "startTime": "0:03:44.99",
                            "endTime": "0:04:28.79",
                            "startSeconds": 225,
                            "endSeconds": 268.8
                        }
                    ]
                },
                {
                    "referenceUrl": None,
                    "iptcName": None,
                    "iabName": None,
                    "confidence": 0.568,
                    "id": 9,
                    "name": "Upc Barcodes",
                    "appearances": [
                        {
                            "startTime": "0:00:05.17",
                            "endTime": "0:01:20.95",
                            "startSeconds": 5.2,
                            "endSeconds": 81
                        },
                        {
                            "startTime": "0:02:05.43",
                            "endTime": "0:04:28.79",
                            "startSeconds": 125.4,
                            "endSeconds": 268.8
                        }
                    ]
                },
                {
                    "referenceUrl": None,
                    "iptcName": "Science and Technology/identification technology",
                    "iabName": "Technology & Computing",
                    "confidence": 0.5596,
                    "id": 10,
                    "name": "Technology/Rfid",
                    "appearances": [
                        {
                            "startTime": "0:00:10.01",
                            "endTime": "0:01:11.82",
                            "startSeconds": 10,
                            "endSeconds": 71.8
                        }
                    ]
                },
                {
                    "referenceUrl": None,
                    "iptcName": "economy, business and finance/computing and information technology",
                    "iabName": "Technology & Computing",
                    "confidence": 0.5149,
                    "id": 11,
                    "name": "Technology/Qr Codes",
                    "appearances": [
                        {
                            "startTime": "0:00:23.6",
                            "endTime": "0:01:23.18",
                            "startSeconds": 23.6,
                            "endSeconds": 83.2
                        },
                        {
                            "startTime": "0:02:00.96",
                            "endTime": "0:02:38.95",
                            "startSeconds": 121,
                            "endSeconds": 159
                        },
                        {
                            "startTime": "0:03:03.1",
                            "endTime": "0:03:35.63",
                            "startSeconds": 183.1,
                            "endSeconds": 215.6
                        },
                        {
                            "startTime": "0:03:44.99",
                            "endTime": "0:04:28.79",
                            "startSeconds": 225,
                            "endSeconds": 268.8
                        }
                    ]
                },
                {
                    "referenceUrl": None,
                    "iptcName": None,
                    "iabName": None,
                    "confidence": 0.4085,
                    "id": 12,
                    "name": "2d Barcodes",
                    "appearances": [
                        {
                            "startTime": "0:00:05.17",
                            "endTime": "0:01:23.18",
                            "startSeconds": 5.2,
                            "endSeconds": 83.2
                        },
                        {
                            "startTime": "0:02:05.43",
                            "endTime": "0:02:56.38",
                            "startSeconds": 125.4,
                            "endSeconds": 176.4
                        },
                        {
                            "startTime": "0:03:03.1",
                            "endTime": "0:04:28.79",
                            "startSeconds": 183.1,
                            "endSeconds": 268.8
                        }
                    ]
                }
            ]
        },
        "videos": [
            {
                "accountId": "a25c2c8a-c8b4-4f3f-a4c1-91e3ae4e36e9",
                "id": "a703c9d6cf",
                "state": "Processed",
                "moderationState": "OK",
                "reviewState": "None",
                "privacyMode": "Public",
                "processingProgress": "100%",
                "failureCode": "None",
                "failureMessage": "",
                "externalId": "https://demosc.blob.core.windows.net/demo-container/-7rEi5VtC54_195_198.mp4",
                "externalUrl": None,
                "metadata": None,
                "insights": {
                    "version": "1.0.0.0",
                    "duration": "0:00:03",
                    "sourceLanguage": "en-US",
                    "sourceLanguages": [
                        "en-US"
                    ],
                    "language": "en-US",
                    "languages": [
                        "en-US"
                    ],
                    "textualContentModeration": {
                        "id": 0,
                        "bannedWordsCount": 0,
                        "bannedWordsRatio": 0,
                        "instances": []
                    },
                    "statistics": {
                        "correspondenceCount": 0,
                        "speakerTalkToListenRatio": {},
                        "speakerLongestMonolog": {},
                        "speakerNumberOfFragments": {},
                        "speakerWordCount": {}
                    }
                },
                "thumbnailId": "6418b29c-8efb-4db3-afaa-f273302b5d72",
                "detectSourceLanguage": False,
                "languageAutoDetectMode": "None",
                "sourceLanguage": "en-US",
                "sourceLanguages": [
                    "en-US"
                ],
                "language": "en-US",
                "languages": [
                    "en-US"
                ],
                "indexingPreset": "Default",
                "linguisticModelId": "00000000-0000-0000-0000-000000000000",
                "personModelId": "00000000-0000-0000-0000-000000000000",
                "isAdult": False,
                "publishedUrl": "https://dtvideoindexer-usea.streaming.media.azure.net/f9010078-8cd4-4c8f-8805-f398956f295d/-7rEi5VtC54_195.ism/manifest(encryption=cbc)",
                "publishedProxyUrl": None,
                "viewToken": "Bearer=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cm46bWljcm9zb2Z0OmF6dXJlOm1lZGlhc2VydmljZXM6Y29udGVudGtleWlkZW50aWZpZXIiOiIxZWM4NmFmNi1kYzQ2LTRjOTYtOGE4MS03MjE2MWEyNDllODQiLCJuYmYiOjE2MzE4MjQ3NjMsImV4cCI6MTYzMTg2ODAyMywiaXNzIjoiaHR0cHM6Ly9icmVha2Rvd24ubWUiLCJhdWQiOiJCcmVha2Rvd25Vc2VyIn0.lGScopCcTMe9sHw7xch0Ao3Nzh1pnCyjTE_LiYHStWQ"
            }
        ],
        "videosRanges": [
            {
                "videoId": "a703c9d6cf",
                "range": {
                    "start": "0:00:00",
                    "end": "0:00:03"
                }
            }
        ]
    }
    addVideoStatusResponse(apiUrl , accountId , location , apiKey, accountAccessToken, videoId, "dummyToken", json.dumps(videoResponse))
    addHeaderResponse(videoUrl)
    configuration = ConfigurationFile(
        {
        "index_provider": "Azure",
        "field_service"  : "D365",
        "search_parameters": [ {"maximum_video_count_in_search_results": 100 }],
        "services" : {
                            "video": ["barcodes" , "brands" , "faces" , "header" , "keywords" , "labels" , "metadata" , "ocr" , "topics" , "transcripts" ]
                    },

            "metadata" : {},
            "language": "en"
        },
        "file_name"
    )

    result  = processVideo(videoUrl, configuration)

@responses.activate
def testProcessVideoNoResult():
    setConnectionProperties("https://dummyapi.com", "eastus", "123456", "ABCDEFGHI")
    accountAccessToken = "dummy_token"
    addAccountAccessResponse(accountAccessToken)
    apiUrl , accountId , location , apiKey = getConnectionProperties()
    videoUrl = "https://dummy/video.mp4"
    addCheckUploadVideoResponse(apiUrl , accountId , location , apiKey, accountAccessToken , videoUrl, 404, "{}")
    videoId = "videoId1234"
    addUploadVideoResponse(apiUrl , accountId , location , apiKey, accountAccessToken, videoUrl,  json.dumps({"id": videoId}))
    addVideoTokenResponse(apiUrl , accountId , location , apiKey,accountAccessToken,videoId,"dummyToken")
    videoResponse = None
    addVideoStatusResponse(apiUrl , accountId , location , apiKey, accountAccessToken, videoId, "dummyToken", json.dumps(videoResponse))
    addHeaderResponse(videoUrl)
    configuration = ConfigurationFile(
        {
        "index_provider": "Azure",
        "field_service"  : "D365",
        "search_parameters": [ {"maximum_video_count_in_search_results": 100 }],
        "services" : {
                            "video": ["barcodes" , "brands" , "faces" , "header" , "keywords" , "labels" , "metadata" , "ocr" , "topics" , "transcripts" ]
                    },

            "metadata" : {},
            "language": "en"
        },
        "file_name"
    )

    result  = processVideo(videoUrl, configuration)


