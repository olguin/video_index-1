import logging
import azure.functions as func
import json
import traceback
from QrScanner.extract_barcodes import *
from shared_code.configuration_file import ConfigurationFile as ConfigurationFile

from datetime import datetime


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        json_data = json.dumps(req.get_json())
        values = json.loads(json_data)['values']
        video_file_path = values[0]["data"]["video_file_path"]
        record_id = values[0]["recordId"]
        config = ConfigurationFile.get_json_file_from_url(os.path.dirname(video_file_path))
        return func.HttpResponse(json.dumps(extract_barcodes(video_file_path, record_id, config), ensure_ascii=False), mimetype="application/json")
    except Exception:
        return func.HttpResponse(traceback.format_exc())
