import responses
import json
from shared_code.acs_wrapper import *
from shared_code.configuration_file import ConfigurationFile as ConfigurationFile
import pytest

def get_index_url(params):
    return f"https://{params['service']}.search.windows.net/indexes/{params['index']}/docs/search?api-version={params['api_version']}"

def assertEqual(expected, received):
    assert expected == received

def add_search_response(params, response):
    responses.add(**{
        'method'         : responses.POST,
        'url'            : get_index_url(params),
        'body'           : json.dumps(response),
        'status'         : 200,
        'content_type'   : 'application/json',
        'adding_headers' : {'X-Foo': 'Bar'}
        })

@responses.activate
def testMetadataNotMatchingSearch():
    params = {
    "key": "any_key",
    "api_version":"2020-06-30",
    "search": "not matching",
    "service": "any_service",
    "index":  "any_index",
    "container": "any_container"
    }

    config = {
            "services": {
                "video": [ "metadata", "barcode", "ocr", "labels",  "transcript"]
            }
        }

    index_response = """
        {
        "@odata.context": "https://dtdemoss.search.windows.net/indexes('demo-container-in')/$metadata#docs(*)",
        "value": [
            {
                "@search.score": 1,
                "id": "dGVzdF92aWRlby5NT1Y1",
                "path": "https://demosc.blob.core.windows.net/demo-container/test_video.MOV",
                "content": "",
                "barcodes": [],
                "transcripts": [],
                "ocr": [],
                "keywords": [],
                "topics": [],
                "faces": [],
                "labels": [],
                "brands": [],
                "header": {
                    "owner": "harcoded owner",
                    "creation_date": "Mon, 13 Sep 2021 14:43:27 GMT",
                    "name": "test_video.MOV",
                    "description": "some_description",
                    "thumbnail": "https://api.videoindexer.ai/eastus/Accounts/87ab56c8-906e-4fd4-be73-8cf6949b37c4/Videos/19f5ad50c4/Thumbnails/e52749e2-5211-4452-b412-56c4db8796d9"
                },
                "metadata": [
                    {
                        "key": "Work_Order",
                        "value": "00500"
                    }
                ]
            }
        ]
        }
    """

    add_search_response(params, json.loads(index_response))
    result = search_from_json(params, ConfigurationFile(config, "file_name"))
    assert ("value" in result)
    records = result["value"]
    assertEqual(1, len(records))
    metadata = records[0]["metadata"]
    assertEqual(1, len(metadata))
    assertEqual("Work_Order", metadata[0]["key"])
    assertEqual("00500", metadata[0]["value"])
    match_count = records[0]["match_count"]
    assertEqual(1, len(match_count))
    assertEqual(0, match_count["metadata"])

@responses.activate
def testMetadataMatchingSearch():
    params = {
    "key": "any_key",
    "api_version":"2020-06-30",
    "search": "text",
    "service": "any_service",
    "index":  "any_index",
    "container": "any_container"
    }

    config = {
            "services": {
                "video": [ "metadata", "barcode", "ocr", "labels",  "transcript"]
            }
        }

    index_response = """
        {
        "@odata.context": "https://dtdemoss.search.windows.net/indexes('demo-container-in')/$metadata#docs(*)",
        "value": [
            {
                "@search.score": 1,
                "@search.highlights" : {
                    "metadata/value" : [
                        "<em>text</em>"
                    ]
                },
                "id": "dGVzdF92aWRlby5NT1Y1",
                "path": "https://demosc.blob.core.windows.net/demo-container/test_video.MOV",
                "content": "",
                "barcodes": [],
                "transcripts": [],
                "ocr": [],
                "keywords": [],
                "topics": [],
                "faces": [],
                "labels": [],
                "brands": [],
                "header": {
                    "owner": "harcoded owner",
                    "creation_date": "Mon, 13 Sep 2021 14:43:27 GMT",
                    "name": "test_video.MOV",
                    "description": "some_description",
                    "thumbnail": "https://api.videoindexer.ai/eastus/Accounts/87ab56c8-906e-4fd4-be73-8cf6949b37c4/Videos/19f5ad50c4/Thumbnails/e52749e2-5211-4452-b412-56c4db8796d9"
                },
                "metadata": [
                    {
                        "key": "Work_Order",
                        "value": "text"
                    },
                    {
                        "key": "Work_Order_Description",
                        "value": "A description"
                    }
                ]
            }
        ]
        }
    """

    add_search_response(params, json.loads(index_response))
    result = search_from_json(params, ConfigurationFile(config,"file_name"))
    assert ("value" in result)
    records = result["value"]
    assertEqual(1, len(records))
    metadata = records[0]["metadata"]
    assertEqual(2, len(metadata))
    assertEqual("Work_Order", metadata[0]["key"])
    assertEqual("<em>text</em>", metadata[0]["value"])
    assertEqual("Work_Order_Description", metadata[1]["key"])
    assertEqual("A description", metadata[1]["value"])
    match_count = records[0]["match_count"]
    assertEqual(1, len(match_count))
    assertEqual(1, match_count["metadata"])

@responses.activate
def testHeaderMatchingSearch():
    params = {
    "key": "any_key",
    "api_version":"2020-06-30",
    "search": "text",
    "service": "any_service",
    "index":  "any_index",
    "container": "any_container"
    }

    config = {
            "services": {
                "video": [ "metadata", "barcode", "ocr", "labels",  "transcript"]
            }
        }

    index_response = """
        {
        "@odata.context": "https://dtdemoss.search.windows.net/indexes('demo-container-in')/$metadata#docs(*)",
        "value": [
            {
                "@search.score": 1,
                "@search.highlights" : {
                    "header/owner" : [
                        "<em>John</em> Owner"
                    ]
                },
                "id": "dGVzdF92aWRlby5NT1Y1",
                "path": "https://demosc.blob.core.windows.net/demo-container/test_video.MOV",
                "content": "",
                "barcodes": [],
                "transcripts": [],
                "ocr": [],
                "keywords": [],
                "topics": [],
                "faces": [],
                "labels": [],
                "brands": [],
                "header": {
                    "owner": "John Owner",
                    "creation_date": "Mon, 13 Sep 2021 14:43:27 GMT",
                    "name": "test_video.MOV",
                    "description": "some_description",
                    "thumbnail": "https://api.videoindexer.ai/eastus/Accounts/87ab56c8-906e-4fd4-be73-8cf6949b37c4/Videos/19f5ad50c4/Thumbnails/e52749e2-5211-4452-b412-56c4db8796d9"
                },
                "metadata": [
                    {
                        "key": "Work_Order",
                        "value": "text"
                    },
                    {
                        "key": "Work_Order_Description",
                        "value": "A description"
                    }
                ]
            }
        ]
        }
    """

    add_search_response(params, json.loads(index_response))
    result = search_from_json(params, ConfigurationFile(config,"file_name"))
    assert ("value" in result)
    records = result["value"]
    assertEqual(1, len(records))
    metadata = records[0]["metadata"]
    assertEqual(2, len(metadata))
    assertEqual("Work_Order", metadata[0]["key"])
    assertEqual("text", metadata[0]["value"])
    assertEqual("Work_Order_Description", metadata[1]["key"])
    assertEqual("A description", metadata[1]["value"])
    match_count = records[0]["match_count"]
    assertEqual(2, len(match_count))
    assertEqual(0, match_count["metadata"])
    assertEqual(1, match_count["header"])
    header = records[0]["header"]
    assertEqual("<em>John</em> Owner", header["owner"])


@responses.activate
def testSectionMatchingSearch():
    params = {
    "key": "any_key",
    "api_version":"2020-06-30",
    "search": "text",
    "service": "any_service",
    "index":  "any_index",
    "container": "any_container"
    }

    config = {
            "services": {
                "video": [ "metadata", "barcode", "ocr", "labels",  "transcript"]
            }
        }

    index_response = """
        {
        "@odata.context": "https://dtdemoss.search.windows.net/indexes('demo-container-in')/$metadata#docs(*)",
        "value": [
            {
                "@search.score": 1,
                "@search.highlights" : {
                    "labels/text" : [
                        "<em>cup</em>"
                    ]
                },
                "id": "dGVzdF92aWRlby5NT1Y1",
                "path": "https://demosc.blob.core.windows.net/demo-container/test_video.MOV",
                "content": "",
                "barcodes": [],
                "transcripts": [],
                "ocr": [],
                "keywords": [],
                "topics": [],
                "faces": [],
                "labels" : [
                    {
                    "text" : "cup",
                    "timestamps" : [
                        {
                            "end" : "0:00:09",
                            "start" : "0:00:00"
                        }
                    ]
                    },
                    {
                    "text" : "indoor",
                    "timestamps" : [
                        {
                            "end" : "0:00:09",
                            "start" : "0:00:00"
                        }
                    ]
                    }
                    ],
                "brands": [],
                "header": {
                    "owner": "John Owner",
                    "creation_date": "Mon, 13 Sep 2021 14:43:27 GMT",
                    "name": "test_video.MOV",
                    "description": "some_description",
                    "thumbnail": "https://api.videoindexer.ai/eastus/Accounts/87ab56c8-906e-4fd4-be73-8cf6949b37c4/Videos/19f5ad50c4/Thumbnails/e52749e2-5211-4452-b412-56c4db8796d9"
                },
                "metadata": [
                    {
                        "key": "Work_Order",
                        "value": "text"
                    },
                    {
                        "key": "Work_Order_Description",
                        "value": "A description"
                    }
                ]
            }
        ]
        }
    """

    add_search_response(params, json.loads(index_response))
    result = search_from_json(params, ConfigurationFile(config,"file_name"))
    assert ("value" in result)
    records = result["value"]
    assertEqual(1, len(records))
    metadata = records[0]["metadata"]
    assertEqual(2, len(metadata))
    assertEqual("Work_Order", metadata[0]["key"])
    assertEqual("text", metadata[0]["value"])
    assertEqual("Work_Order_Description", metadata[1]["key"])
    assertEqual("A description", metadata[1]["value"])
    match_count = records[0]["match_count"]
    assertEqual(2, len(match_count))
    assertEqual(0, match_count["metadata"])
    assertEqual(1, match_count["labels"])

    labels = records[0]["labels"]
    assertEqual(1, len(labels))
    assertEqual("<em>cup</em>", labels[0]["text"])

@responses.activate
def testSectionMatchingSearchWithTimestamps():
    params = {
    "key": "any_key",
    "api_version":"2020-06-30",
    "search": "text",
    "service": "any_service",
    "index":  "any_index",
    "container": "any_container"
    }

    config = {
            "services": {
                "video": [ "metadata", "barcode", "ocr", "labels",  "transcript"]
            }
        }

    index_response = """
        {
        "@odata.context": "https://dtdemoss.search.windows.net/indexes('demo-container-in')/$metadata#docs(*)",
        "value": [
            {
                "@search.score": 1,
                "@search.highlights" : {
                    "labels/text" : [
                        "<em>cup</em>"
                    ]
                },
                "id": "dGVzdF92aWRlby5NT1Y1",
                "path": "https://demosc.blob.core.windows.net/demo-container/test_video.MOV",
                "content": "",
                "barcodes": [],
                "transcripts": [],
                "ocr": [],
                "keywords": [],
                "topics": [],
                "faces": [],
                "labels" : [
                    {
                    "text" : "cup",
                    "timestamps" : [
                        {
                            "end" : "0:00:09",
                            "start" : "0:00:00"
                        },
                        {
                            "end" : "0:00:15",
                            "start" : "0:00:11"
                        }
                    ]
                    },
                    {
                    "text" : "indoor",
                    "timestamps" : [
                        {
                            "end" : "0:00:09",
                            "start" : "0:00:00"
                        }
                    ]
                    }
                    ],
                "brands": [],
                "header": {
                    "owner": "John Owner",
                    "creation_date": "Mon, 13 Sep 2021 14:43:27 GMT",
                    "name": "test_video.MOV",
                    "description": "some_description",
                    "thumbnail": "https://api.videoindexer.ai/eastus/Accounts/87ab56c8-906e-4fd4-be73-8cf6949b37c4/Videos/19f5ad50c4/Thumbnails/e52749e2-5211-4452-b412-56c4db8796d9"
                },
                "metadata": [
                    {
                        "key": "Work_Order",
                        "value": "text"
                    },
                    {
                        "key": "Work_Order_Description",
                        "value": "A description"
                    }
                ]
            }
        ]
        }
    """

    add_search_response(params, json.loads(index_response))
    result = search_from_json(params, ConfigurationFile(config,"file_name"))
    assert ("value" in result)
    records = result["value"]
    assertEqual(1, len(records))
    metadata = records[0]["metadata"]
    assertEqual(2, len(metadata))
    assertEqual("Work_Order", metadata[0]["key"])
    assertEqual("text", metadata[0]["value"])
    assertEqual("Work_Order_Description", metadata[1]["key"])
    assertEqual("A description", metadata[1]["value"])
    match_count = records[0]["match_count"]
    assertEqual(2, len(match_count))
    assertEqual(0, match_count["metadata"])
    assertEqual(2, match_count["labels"])

    labels = records[0]["labels"]
    assertEqual(1, len(labels))
    assertEqual("<em>cup</em>", labels[0]["text"])

@responses.activate
def testSectionMatchingSearchDisabledSection():
    params = {
    "key": "any_key",
    "api_version":"2020-06-30",
    "search": "text",
    "service": "any_service",
    "index":  "any_index",
    "container": "any_container"
    }

    config = {
            "services": {
                "video": [ "metadata", "barcode", "ocr", "transcript"]
            }
        }

    index_response = """
        {
        "@odata.context": "https://dtdemoss.search.windows.net/indexes('demo-container-in')/$metadata#docs(*)",
        "value": [
            {
                "@search.score": 1,
                "@search.highlights" : {
                    "labels/text" : [
                        "<em>cup</em>"
                    ]
                },
                "id": "dGVzdF92aWRlby5NT1Y1",
                "path": "https://demosc.blob.core.windows.net/demo-container/test_video.MOV",
                "content": "",
                "barcodes": [],
                "transcripts": [],
                "ocr": [],
                "keywords": [],
                "topics": [],
                "faces": [],
                "labels" : [
                    {
                    "text" : "cup",
                    "timestamps" : [
                        {
                            "end" : "0:00:09",
                            "start" : "0:00:00"
                        },
                        {
                            "end" : "0:00:15",
                            "start" : "0:00:11"
                        }
                    ]
                    },
                    {
                    "text" : "indoor",
                    "timestamps" : [
                        {
                            "end" : "0:00:09",
                            "start" : "0:00:00"
                        }
                    ]
                    }
                    ],
                "brands": [],
                "header": {
                    "owner": "John Owner",
                    "creation_date": "Mon, 13 Sep 2021 14:43:27 GMT",
                    "name": "test_video.MOV",
                    "description": "some_description",
                    "thumbnail": "https://api.videoindexer.ai/eastus/Accounts/87ab56c8-906e-4fd4-be73-8cf6949b37c4/Videos/19f5ad50c4/Thumbnails/e52749e2-5211-4452-b412-56c4db8796d9"
                },
                "metadata": [
                    {
                        "key": "Work_Order",
                        "value": "text"
                    },
                    {
                        "key": "Work_Order_Description",
                        "value": "A description"
                    }
                ]
            }
        ]
        }
    """

    add_search_response(params, json.loads(index_response))
    result = search_from_json(params, ConfigurationFile(config, "file_name"))
    assert ("value" in result)
    records = result["value"]

    assert not ("labels" in records[0])
    assert ("header" in records[0])
    assert ("path" in records[0])
    assert ("id" in records[0])

    match_count = records[0]["match_count"]
    assertEqual(1, len(match_count))
    assertEqual(0, match_count["metadata"])

@responses.activate
def testSearchMatchingById():
    params = {
    "key": "any_key",
    "api_version":"2020-06-30",
    "search": "not matching",
    "service": "any_service",
    "index":  "any_index",
    "container": "any_container"
    }

    config = {
            "services": {
                "video": [ "metadata", "barcode", "ocr", "labels",  "transcript"]
            }
        }

    index_response = """
        {
        "@odata.context": "https://dtdemoss.search.windows.net/indexes('demo-container-in')/$metadata#docs(*)",
        "value": [
            {
                "@search.score": 1,
                "id": "12345",
                "path": "https://demosc.blob.core.windows.net/demo-container/test_video.MOV",
                "content": "",
                "barcodes": [],
                "transcripts": [],
                "ocr": [],
                "keywords": [],
                "topics": [],
                "faces": [],
                "labels": [],
                "brands": [],
                "header": {
                    "owner": "harcoded owner",
                    "creation_date": "Mon, 13 Sep 2021 14:43:27 GMT",
                    "name": "test_video.MOV",
                    "description": "some_description",
                    "thumbnail": "https://api.videoindexer.ai/eastus/Accounts/87ab56c8-906e-4fd4-be73-8cf6949b37c4/Videos/19f5ad50c4/Thumbnails/e52749e2-5211-4452-b412-56c4db8796d9"
                },
                "metadata": [
                    {
                        "key": "Work_Order",
                        "value": "00500"
                    }
                ]
            },
            {
                "@search.score": 1,
                "id": "dGVzdF92aWRlby5NT1Y1",
                "path": "https://demosc.blob.core.windows.net/demo-container/another_test_video.MOV",
                "content": "",
                "barcodes": [],
                "transcripts": [],
                "ocr": [],
                "keywords": [],
                "topics": [],
                "faces": [],
                "labels": [],
                "brands": [],
                "header": {
                    "owner": "harcoded owner",
                    "creation_date": "Mon, 13 Sep 2021 14:43:27 GMT",
                    "name": "test_video.MOV",
                    "description": "some_description",
                    "thumbnail": "https://api.videoindexer.ai/eastus/Accounts/87ab56c8-906e-4fd4-be73-8cf6949b37c4/Videos/19f5ad50c4/Thumbnails/e52749e2-5211-4452-b412-56c4db8796d9"
                },
                "metadata": [
                    {
                        "key": "Work_Order",
                        "value": "00501"
                    }
                ]
            }

        ]
        }
    """

    add_search_response(params, json.loads(index_response))
    result = search_from_json(params, ConfigurationFile(config, "file_name"))
    assert ("value" in result)
    records = result["value"]
    assertEqual(2, len(records))

    add_search_response(params, json.loads(index_response))
    params["id"] = "12345"
    result = search_from_json(params, ConfigurationFile(config, "file_name"))
    assert ("value" in result)
    records = result["value"]
    assertEqual(1, len(records))
    assertEqual("12345", records[0]["id"])

@responses.activate
def testSectionMatchingSearchById():
    params = {
    "key": "any_key",
    "api_version":"2020-06-30",
    "search": "text",
    "service": "any_service",
    "index":  "any_index",
    "id":  "12345",
    "container": "any_container"
    }

    config = {
            "services": {
                "video": [ "metadata", "barcode", "ocr", "labels",  "transcript"]
            }
        }

    index_response = """
        {
        "@odata.context": "https://dtdemoss.search.windows.net/indexes('demo-container-in')/$metadata#docs(*)",
        "value": [
            {
                "@search.score": 1,
                "@search.highlights" : {
                    "labels/text" : [
                        "<em>cup</em>"
                    ]
                },
                "id": "12345",
                "path": "https://demosc.blob.core.windows.net/demo-container/test_video.MOV",
                "content": "",
                "barcodes": [],
                "transcripts": [],
                "ocr": [],
                "keywords": [],
                "topics": [],
                "faces": [],
                "labels" : [
                    {
                    "text" : "cup",
                    "timestamps" : [
                        {
                            "end" : "0:00:09",
                            "start" : "0:00:00"
                        }
                    ]
                    },
                    {
                    "text" : "indoor",
                    "timestamps" : [
                        {
                            "end" : "0:00:09",
                            "start" : "0:00:00"
                        }
                    ]
                    }
                    ],
                "brands": [],
                "header": {
                    "owner": "John Owner",
                    "creation_date": "Mon, 13 Sep 2021 14:43:27 GMT",
                    "name": "test_video.MOV",
                    "description": "some_description",
                    "thumbnail": "https://api.videoindexer.ai/eastus/Accounts/87ab56c8-906e-4fd4-be73-8cf6949b37c4/Videos/19f5ad50c4/Thumbnails/e52749e2-5211-4452-b412-56c4db8796d9"
                },
                "metadata": [
                    {
                        "key": "Work_Order",
                        "value": "text"
                    },
                    {
                        "key": "Work_Order_Description",
                        "value": "A description"
                    }
                ]
            }
        ]
        }
    """

    add_search_response(params, json.loads(index_response))
    result = search_from_json(params, ConfigurationFile(config, "file_name"))
    assert ("value" in result)
    records = result["value"]
    assertEqual(1, len(records))
    metadata = records[0]["metadata"]
    assertEqual(2, len(metadata))
    assertEqual("Work_Order", metadata[0]["key"])
    assertEqual("text", metadata[0]["value"])
    assertEqual("Work_Order_Description", metadata[1]["key"])
    assertEqual("A description", metadata[1]["value"])
    match_count = records[0]["match_count"]
    print(match_count)
    assertEqual(0, match_count["metadata"])
    assertEqual(1, match_count["labels"])

    labels = records[0]["labels"]
    assertEqual(2, len(labels))
    assertEqual("<em>cup</em>", labels[0]["text"])
    assertEqual("indoor", labels[1]["text"])

@responses.activate
def testSectionMatchingSearchBywildCard():
    params = {
    "key": "any_key",
    "api_version":"2020-06-30",
    "search": "*",
    "service": "any_service",
    "index":  "any_index",
    "id":  "12345",
    "container": "any_container"
    }

    config = {
            "services": {
                "video": [ "metadata", "barcodes", "ocr", "labels",  "transcripts"]
            }
        }

    index_response = """
        {
        "@odata.context": "https://dtdemoss.search.windows.net/indexes('demo-container-in')/$metadata#docs(*)",
        "value": [
            {
                "@search.score": 1,
                "id": "12345",
                "path": "https://demosc.blob.core.windows.net/demo-container/test_video.MOV",
                "content": "",
                "barcodes": [],
                "transcripts": [],
                "ocr": [],
                "keywords": [],
                "topics": [],
                "faces": [],
                "labels" : [
                    {
                    "text" : "cup",
                    "timestamps" : [
                        {
                            "end" : "0:00:09",
                            "start" : "0:00:00"
                        }
                    ]
                    },
                    {
                    "text" : "indoor",
                    "timestamps" : [
                        {
                            "end" : "0:00:09",
                            "start" : "0:00:00"
                        }
                    ]
                    }
                    ],
                "brands": [],
                "header": {
                    "owner": "John Owner",
                    "creation_date": "Mon, 13 Sep 2021 14:43:27 GMT",
                    "name": "test_video.MOV",
                    "description": "some_description",
                    "thumbnail": "https://api.videoindexer.ai/eastus/Accounts/87ab56c8-906e-4fd4-be73-8cf6949b37c4/Videos/19f5ad50c4/Thumbnails/e52749e2-5211-4452-b412-56c4db8796d9"
                },
                "metadata": [
                    {
                        "key": "Work_Order",
                        "value": "text"
                    },
                    {
                        "key": "Work_Order_Description",
                        "value": "A description"
                    }
                ]
            }
        ]
        }
    """

    add_search_response(params, json.loads(index_response))
    result = search_from_json(params, ConfigurationFile(config, "file_name"))
    assert ("value" in result)
    records = result["value"]
    assertEqual(1, len(records))
    metadata = records[0]["metadata"]
    assertEqual(2, len(metadata))
    assertEqual("Work_Order", metadata[0]["key"])
    assertEqual("text", metadata[0]["value"])
    assertEqual("Work_Order_Description", metadata[1]["key"])
    assertEqual("A description", metadata[1]["value"])
    match_count = records[0]["match_count"]
    assertEqual(2, match_count["metadata"])
    assertEqual(2, match_count["labels"])
    assertEqual(0, match_count["ocr"])

    labels = records[0]["labels"]
    assertEqual(2, len(labels))
    assertEqual("cup", labels[0]["text"])
    assertEqual("indoor", labels[1]["text"])

