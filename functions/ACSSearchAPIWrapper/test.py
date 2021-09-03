import json
from wrapper import *

params = {
  "key": "D52DA06B07D3A48F345EEC85B21FAA5D",
  "api_version":"2020-06-30",
  "search": "engine",
  "service": "dtdvss",
  "index":  "development-container-in",
  "container": "/home/lorenzo/src/video_index/test_data/no_barcodes.json"
}

config = {
        "services": {
            "video": [ "metadata", "barcode", "ocr", "labels",  "transcript"]
        }
    }
#result = test_search(service,index,key,api_version,{"search": search})
result = search_from_json(params, config)
#print(result)
print(json.dumps(result))
