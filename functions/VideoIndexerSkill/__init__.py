import azure.functions as func
from shared_code.video_indexer_tools import processVideo as processVideo
import json
import logging
from shared_code.configuration_file import ConfigurationFile as Configuration 
import os


def main(req: func.HttpRequest) -> func.HttpResponse:
    json_data = json.dumps(req.get_json())
    values = json.loads(json_data)['values']
    video_file_path = values[0]["data"]["video_file_path"]
    record_id = values[0]["recordId"]

    videoInfo = processVideo(video_file_path, ConfigurationFile.get_json_file_from_url(os.path.dirname(video_file_path)))

    results = {}
    results["values"] = []
    record = {
            "recordId": record_id,
            "data": videoInfo
            }
    results["values"].append(record)
    logging.info(f'result {json.dumps(results,ensure_ascii=False)}')

    return func.HttpResponse(json.dumps(results,ensure_ascii=False), mimetype="application/json")
