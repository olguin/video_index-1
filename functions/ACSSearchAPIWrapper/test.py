from wrapper import *
import json

params = {
  "key": "2BE17B570160879C22C41F85F128BD53",
  "api_version":"2020-06-30",
  "search": "microsoft",
  "service": "dtdvss",
  "index":  "development-container-in"
}
#result = test_search(service,index,key,api_version,{"search": search})
result = search_from_json(params)
#print(result)
print(json.dumps(result))
