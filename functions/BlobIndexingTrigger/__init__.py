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
from video_indexer_tools.video_indexer_tools import runIndexer

import azure.functions as func

def main(event: func.EventGridEvent):

    data = event.get_json()
    url = data['url']
    logging.info(f'Processing {url}')
    processVideo(url,False)
    runIndexer()
