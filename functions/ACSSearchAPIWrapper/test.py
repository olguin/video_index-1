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
        return self.alwaysIncludedSection(section)

    def alwaysIncludedSection(self, section):
        return section in ["header", "path"]



params = {
  "key": "F106F0B370973EC836AB0BB3CFBF7346",
  "api_version":"2020-06-30",
  "search": "*",
  "service": "dtdemoss",
  "index":  "demo-container-in",
  #"id": "YmFyY29kZS10ZXN0aW5nLm1wNA2",
  "container": "https://demosc.blob.core.windows.net/demo-container"
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
