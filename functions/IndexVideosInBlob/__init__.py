import logging
import json
import os
import traceback
import azure.functions as func
from shared_code.video_indexer_tools import scan_all_videos as scan_all_videos 

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        storage_account = os.getenv("STORAGE_ACCOUNT_NAME")
        container = os.getenv("STORAGE_CONTAINER")
        response = json.dumps(scan_all_videos(storage_account, container))
        return func.HttpResponse(response)
    except Exception:
        return func.HttpResponse(traceback.format_exc())

