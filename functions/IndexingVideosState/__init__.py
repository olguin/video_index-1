import logging
import json
from shared_code.video_indexer_tools import listVideos as listVideos
from shared_code.video_indexer_tools import getIndexerState as getIndexerState
import azure.functions as func
import traceback

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        response = {
            "videos": listVideos(),
            "indexer": getIndexerState()
        }
        return func.HttpResponse(json.dumps(response))
    except Exception:
        return func.HttpResponse(traceback.format_exc())



