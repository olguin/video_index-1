from D365NotesHttpTrigger.notes_trigger_function import NotesTriggerFunction

import azure.functions as func
import json
import os
import logging

from shared_code.oauth_client import OauthClient


def main(req: func.HttpRequest) -> func.HttpResponse:

    req_body = req.get_json()
    note_id = req_body["PrimaryEntityId"]
    crm_organization_URI = None
    logging.info(f"ENTERING Notes Trigger WITH NOTE_ID:{note_id} ")

    try:

        crm_organization_URI = os.environ["CRM_BASE_URL"]
        if crm_organization_URI is None or crm_organization_URI == "":
            crm_organization_URI = "https://doubletime.crm.dynamics.com"

        logging.info(f"BASE CRM URL:{crm_organization_URI}")
        crm_auth_token_result = OauthClient.get_oauth_token_response(os.environ["AUTH_TOKEN_ENDPOINT"], crm_organization_URI)

        if crm_auth_token_result.status_code != 200:
            error_message = f"Note Http Trigger - OAUTH ERROR - Http Status code: {crm_auth_token_result.status_code}, Http Error:{crm_auth_token_result.text}"
            logging.info(error_message)
            return func.HttpResponse(json.dumps(error_message, ensure_ascii=False), mimetype="application/json",  status_code=crm_auth_token_result.status_code)

        oauth_token = crm_auth_token_result.json()["token"]

        return NotesTriggerFunction.copy_note_attachment_to_blob_container(crm_organization_URI, note_id, oauth_token)
    except Exception as ex:
        logging.error(
            f"Error in Note Http Trigger init method - EXCEPTION:{ex}")
        func.HttpResponse(json.dumps(f"Error in Note Http Trigger:{ex}", ensure_ascii=False), mimetype="application/json", status_code = 401)
