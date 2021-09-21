import responses
import json
from shared_code.video_indexer_tools import *
from shared_code.config_reader import Configuration as Configuration
import pytest

def setConnectionProperties(apiUrl, location, accountId, apiKey):
    os.environ["DT_API_URL"] = apiUrl
    os.environ["DT_LOCATION"] = location
    os.environ["DT_ACCOUNT_ID"] = accountId
    os.environ["DT_API_KEY"] = apiKey


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
            "name": "-7rEi5VtC54_195_198.mp4",
            "id": "a703c9d6cf",
            "privacyMode": "Public",
            "duration": {
                "time": "0:00:03",
                "seconds": 3
            },
            "thumbnailVideoId": "a703c9d6cf",
            "thumbnailId": "6418b29c-8efb-4db3-afaa-f273302b5d72",
            "faces": [],
            "keywords": [],
            "sentiments": [],
            "emotions": [],
            "audioEffects": [],
            "labels": [],
            "framePatterns": [],
            "brands": [],
            "namedLocations": [],
            "namedPeople": [],
            "statistics": {
                "correspondenceCount": 0,
                "speakerTalkToListenRatio": {},
                "speakerLongestMonolog": {},
                "speakerNumberOfFragments": {},
                "speakerWordCount": {}
            },
            "topics": []
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
    configuration = Configuration(
        {
        "index_provider": "Azure",
        "field_service"  : "D365",
        "search_parameters": [ {"maximum_video_count_in_search_results": 100 }],
        "services" : {
                            "video": ["barcodes" , "brands" , "faces" , "header" , "keywords" , "labels" , "metadata" , "ocr" , "topics" , "transcripts" ]
                    },

            "metadata" : {},
            "language": "en"
        }
    )

    result  = processVideo(videoUrl, configuration)

