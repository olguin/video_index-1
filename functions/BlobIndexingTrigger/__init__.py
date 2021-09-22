import logging
import requests
import json
import time
import os
import xml.etree.ElementTree as ET
import threading
import queue
import re
import logging
from shared_code.video_indexer_tools import processVideo as processVideo
from shared_code.video_indexer_tools import videosStillProcessing as videosStillProcessing
from shared_code.video_indexer_tools import deleteVideo as deleteVideo
from shared_code.video_indexer_tools import runIndexer as runIndexer
from shared_code.configuration_file import ConfigurationFile as Configuration 

import azure.functions as func

def main(event: func.EventGridEvent):

    data = event.get_json()
    url = data['url']
    action = data['api']
    logging.info(f'Action {action}')
    logging.info(f'Processing {url}')
    if(action == "DeleteBlob"):
        deleteVideo(url)
    else:
        processVideo(url,ConfigurationFile.get_json_file_from_url(os.path.dirname(url)), False)

    if(videosStillProcessing()):
        logging.info(f"Skipping indexing because some videos are already being processed")
    else:
        result = runIndexer()
        logging.info(f"indexer result {result}")

