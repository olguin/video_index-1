import json
import os
from video_indexer_tools import *

os.environ["SUBSCRIPTION"] =  "898225fb-0fa0-4180-82b0-c3c103ade9a4"
os.environ["GROUP"] =  "dtdvrg0uspklrodz4yzi"

os.environ["APP_ID"] =  "26a41b49-d23f-4524-8ae7-7f6222919847"
os.environ["TENANT"] =  "639be87d-9250-4b32-afb6-3ec84932b34b"
os.environ["PASSWORD"] =  "WFTKC_fNkwq6Nh.Yylg-es2yilXLWziVsw"

os.environ["PREFIX"] =  "dtdv"
os.environ["CONTAINER"] =  "development-container"

#result = scan_all_videos("demosc", "demo-container")
result = runIndexer()
print(json.dumps(result))
