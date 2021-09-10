import json
from wrapper import *

class Configuration():

    def read_configuration(self, container_url):
            return None


    def getLanguage(self):
        return "en"

    def filterSectionsByConfigInRecord(self, record):
        None


    def isSectionEnabled(self, section):
        return True

    def alwaysIncludedSection(self, section):
        return section in ["header", "path"]



params = {
  "key": "D52DA06B07D3A48F345EEC85B21FAA5D",
  "api_version":"2020-06-30",
  "search": "id: YmFyY29kZS10ZXN0aW5nLm1wNA2",
  #"search": "barcode",
  "service": "dtdemoss",
  "index":  "development-container-in",
  "container": "/home/lorenzo/src/video_index/test_data/no_barcodes.json"
}

config = {
        "services": {
            "video": [ "metadata", "barcode", "ocr", "labels",  "transcript"]
        }
    }
#result = test_search(service,index,key,api_version,{"search": search})
result = search_from_json(params, Configuration())
#print(result)
print(json.dumps(result))
