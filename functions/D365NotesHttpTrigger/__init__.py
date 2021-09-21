from requests.models import Response
from shared_code.configuration_file import ConfigurationFile
import azure.functions as func
import requests
import json
import os
import logging
import datetime


from D365NotesHttpTrigger.note import Note
from shared_code.oauth_client import OauthClient


def main(req: func.HttpRequest) -> func.HttpResponse:
   
    req_body = req.get_json()
    note_id = req_body["PrimaryEntityId"]
    crm_organization_URI = None
    logging.info(f"ENTERING WITH NOTE_ID!!!!!!!!!!!!!!!!!!!!!!!!:{note_id} 2002")

    try:
       
        crm_organization_URI = os.environ["CRM_BASE_URL"]
        if crm_organization_URI is None or crm_organization_URI =="":
            crm_organization_URI= "https://doubletime.crm.dynamics.com"

        logging.info(f"BASE CRM URL:{crm_organization_URI}")
        crm_auth_token_result = OauthClient.get_oauth_token_response(os.environ["AUTH_TOKEN_ENDPOINT"], crm_organization_URI)

        if crm_auth_token_result.status_code != 200:           
            error_message = f"Note Http Trigger - OAUTH ERROR - Http Status code: {crm_auth_token_result.status_code}, Http Error:{crm_auth_token_result.text}"
            logging.info(error_message)
            return func.HttpResponse(json.dumps(error_message, ensure_ascii=False), mimetype="application/json",  status_code=crm_auth_token_result.status_code)

        oauth_token = crm_auth_token_result.json()["token"]
        
        return copy_note_attachment_to_blob_container(crm_organization_URI, note_id, oauth_token)
    except Exception as ex:
        logging.error(f"Error in Note Http Trigger init method - EXCEPTION:{ex}")
        func.HttpResponse(json.dumps(f"Error in Note Http Trigger:{ex}", ensure_ascii=False),
                          mimetype="application/json",  status_code=401)


def copy_note_attachment_to_blob_container(crm_organization_URI:str, note_id:str, oauth_token:str) -> Response:
    try:
        storage_account_name = os.environ["STORAGE_ACCOUNT_NAME"]
        storage_container = os.environ["STORAGE_CONTAINER"]
        crm_request_headers = {
            'Authorization': 'Bearer ' + oauth_token,
            'OData-MaxVersion': '4.0',
            'OData-Version': '4.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json; charset=utf-8',
            'Prefer': 'odata.maxpagesize=500',
            'Prefer': 'odata.include-annotations=OData.Community.Display.V1.FormattedValue'
        }

        file_request_headers = {
           'Authorization': 'Bearer ' + oauth_token,
           'Content-Type': 'application/octet-stream',
        }

        # full path to D365 Field Service REST api endpoint
        rest_api_URL: str = crm_organization_URI+'/api/data/v9.1'

        metadata_tags_values = {}

        if(oauth_token != ''):
            note: Note = Note.find(
                rest_api_URL, crm_request_headers, note_id)

        if note is not None:
            if note.has_video_attachment():         
                configuration_file = ConfigurationFile.load(storage_account_name, storage_container, os.environ["CONFIG_FILE"])          
                metadata_tags_values = configuration_file.get_metadata_values(crm_organization_URI, crm_request_headers,  note.asdict())
                note_video_content = note.download_attachment(rest_api_URL, file_request_headers)
                if note_video_content is None:
                   raise RuntimeError("Error downloading attachment.")

                note.upload_attachment_to_container(note_video_content, metadata_tags_values, storage_account_name, storage_container, os.environ["AUTH_TOKEN_ENDPOINT"])

       
        return func.HttpResponse(json.dumps(metadata_tags_values, ensure_ascii=False), mimetype="application/json",  status_code=200)
    except Exception as ex:
        error_message = f"Error on Http Note Trigger: {ex}"
        logging.error(error_message)
        return func.HttpResponse(json.dumps(error_message, ensure_ascii=False), mimetype="application/json",  status_code=400)



