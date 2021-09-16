import os
from indexing_tools import *

os.environ["SUBSCRIPTION"] =  "898225fb-0fa0-4180-82b0-c3c103ade9a4"
os.environ["GROUP"] =  "dtdemorg0uspklrodz4yzi"

os.environ["APP_ID"] =  "26a41b49-d23f-4524-8ae7-7f6222919847"
os.environ["TENANT"] =  "639be87d-9250-4b32-afb6-3ec84932b34b"
os.environ["PASSWORD"] =  "WFTKC_fNkwq6Nh.Yylg-es2yilXLWziVsw"

os.environ["PREFIX"] =  "dtdemo"
os.environ["CONTAINER"] =  "demo-container"

token = getToken()

prefix =  os.getenv("PREFIX")
serviceName = f'{prefix}ss'
searchServiceKey = getSearchServiceKey(token,serviceName, "2020-08-01" )
urls = ["https://demosc.blob.core.windows.net/demo-container/bThp4xkwewg_234_237.mp4", "https://demosc.blob.core.windows.net/demo-container/EA1D-uGDys4_405_408.mp4"]
for url in urls:
    recordId = findRecord(token,searchServiceKey, url)
    print(recordId)
    result = deleteRecord(token,searchServiceKey,recordId)
    print(result)
