import logging
import json
import traceback
import azure.functions as func
from shared_code.acs_wrapper import search_from_json as search_from_json 
from shared_code.config_reader import ConfigurationFile as Configuration 

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        parameters = req.get_json()
        logging.info(f'Python HTTP trigger function processed a request parameters{parameters}.')
        response = json.dumps(search_from_json(parameters, ConfigurationFile.get_json_file_from_url(parameters.get("container", None))))
        logging.info(f'Python HTTP trigger function processed a request response{response}.')
        return func.HttpResponse(response)
    except Exception:
        return func.HttpResponse(traceback.format_exc())

