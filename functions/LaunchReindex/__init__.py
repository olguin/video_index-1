import logging
import json
import os
import traceback
import azure.functions as func
from shared_code.video_indexer_tools import runIndexer as runIndexer 

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        response = runIndexer()
        return func.HttpResponse(response)
    except Exception:
        return func.HttpResponse(traceback.format_exc())

