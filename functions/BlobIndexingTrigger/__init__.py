import logging
import grequests
import requests
import json
import time
import os
import xml.etree.ElementTree as ET
import threading
import queue
import re
import logging
from video_indexer_tools.video_indexer_tools import processVideo

import azure.functions as func

def runIndexer():

    api_version="2020-06-30"
    key = "D52DA06B07D3A48F345EEC85B21FAA5D"
    service = "dtdvss"
    indexer= "development-container-irn"
    runIndexerURL=f"https://{service}.search.windows.net/indexers/{indexer}/run?api-version={api_version}"
    res = requests.post(runIndexerURL,headers={"api-key":key})
    return res

def main(event: func.EventGridEvent):

    data = event.get_json()
    url = data['url']
    logging.info(f'Processing {url}')
    processVideo(url,False)
    result = runIndexer()
    logging.info(f"indexer result {result}")
