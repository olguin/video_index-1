from shared_code.configuration_file import ConfigurationFile
import azure.functions as func
import requests
import json
import os
import logging
import base64
import datetime


from D365NotesHttpTrigger.note import Note
from shared_code.oauth_client import OauthClient


def main(req: func.HttpRequest) -> func.HttpResponse:
    error_messages = {}
    req_body = req.get_json()
    note_id = req_body["PrimaryEntityId"]
    try:
        logging.info(
            f"NOTE HTTP trigger function processed a request with  note_id: {req_body['PrimaryEntityId']}.")
        crm_organization_URI = os.environ["CRM_BASE_URL"]
        if crm_organization_URI is None:
            crm_organization_URI= "https://doubletime.crm.dynamics.com"

        logging.info(f"BASE CRM URL:{crm_organization_URI}")
        crm_auth_token_result = OauthClient.get_oauth_token_response(os.environ["AUTH_TOKEN_ENDPOINT"], crm_organization_URI)

        if crm_auth_token_result.status_code != 200:
            error_messages['oauth_crm_request'] = f"Http Status code: {crm_auth_token_result.status_code}, Http Error:{crm_auth_token_result.text}"
            logging.info(f"OAUTH ERROR: {error_messages['oauth_crm_request']}")
            return func.HttpResponse(json.dumps(error_messages, ensure_ascii=False), mimetype="application/json",  status_code=crm_auth_token_result.status_code)

        oauth_token = crm_auth_token_result.json()["token"]
        return copy_note_attachment_to_blob_container(crm_organization_URI, note_id, oauth_token, error_messages)
    except Exception as ex:
        logging.error(f"NOTE After NOTE EXCEPTION:{ex}")
        error_messages["Main error"] = str(ex)
        func.HttpResponse(json.dumps(error_messages, ensure_ascii=False),
                          mimetype="application/json",  status_code=401)


def copy_note_attachment_to_blob_container(crm_organization_URI, note_id, oauth_token, error_messages):
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
    error_in_work_order_request = False

    # full path to D365 Field Service REST api endpoint
    rest_api_URL: str = crm_organization_URI+'/api/data/v9.1'

    metadata_tags_values = {}

    if(oauth_token != ''):
        note: Note = Note.find(
            rest_api_URL, crm_request_headers, note_id, error_messages)

    if note is not None:
        if note.has_video_attachment():

            configuration_file = ConfigurationFile.load(os.environ["STORAGE_ACCOUNT_NAME"], os.environ["STORAGE_CONTAINER"], os.environ["CONFIG_FILE"])
            
            metadata_tags_values = configuration_file.get_metadata_values(crm_organization_URI, crm_request_headers,  note.asDict)

            note_video_content = note.download_attachment(
                rest_api_URL, file_request_headers, error_messages)
            if note_video_content is None:
                return func.HttpResponse(json.dumps(error_messages, ensure_ascii=False), mimetype="application/json",  status_code=401)

            logging.info(
                f"ENV VARIABLES:{os.environ['STORAGE_ACCOUNT_NAME']}, {os.environ['STORAGE_CONTAINER']}")
            error_saving_attachment = save_update_note_attachment_to_storage_container(
                note, metadata_tags_values, note_video_content,  os.environ["STORAGE_ACCOUNT_NAME"], os.environ["STORAGE_CONTAINER"], error_messages)

    if note is None or error_in_work_order_request or error_saving_attachment:
        return func.HttpResponse(json.dumps(error_messages, ensure_ascii=False), mimetype="application/json",  status_code=401)
    else:
        return func.HttpResponse(json.dumps(metadata_tags_values, ensure_ascii=False), mimetype="application/json",  status_code=200)



def save_update_note_attachment_to_storage_container(note, metadata_tags, note_attachment, account_name, container, error_messages):
    storage_resource = "https://storage.azure.com/"
    meta_prefix = "x-ms-meta-"
    storage_auth_token_result = OauthClient.get_oauth_token_response(os.environ["AUTH_TOKEN_ENDPOINT"], storage_resource)

    if storage_auth_token_result.status_code != 200:
        error_messages['oauth_storage_request'] = f"Http Status code: {storage_auth_token_result.status_code}, Http Error:{storage_auth_token_result.text}"
        logging.error(
            f"OAUTH STORAGE ERROR: {error_messages['oauth_storage_request']}")
        return False

    date = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    metadata_header = {}
    for tag_key in metadata_tags.keys():
        metadata_header.update({meta_prefix+tag_key: metadata_tags[tag_key]})

    storage_request_headers = {
        'Authorization': 'Bearer ' + storage_auth_token_result.json()["token"],
        'Content-Type': 'application/octet-stream',
        'x-ms-version': '2020-10-02',
        'x-ms-date': f"{date}",
        'x-ms-blob-type': 'BlockBlob',
        'Content-Length': f"{len(note_attachment)}",
    }

    storage_request_headers.update(metadata_header)

    blob_storage_endpoint = f"https://{account_name}.blob.core.windows.net/{container}/{note['filename']}"

    put_blob_result = requests.put(
        blob_storage_endpoint, data=note_attachment, headers=storage_request_headers)

    logging.info(
        f"PUT STORAGE HTTP CODE: {put_blob_result.status_code}, RESPONSE:{put_blob_result.text}")
    if (put_blob_result.status_code != 201):
        error_messages[
            'save_update_note_attachment_to_storage_container'] = f"HTTP CODE: {put_blob_result.status_code} - ERROR:{put_blob_result.text}"
        logging.error(
            f"PUT STORAGE BLOB ERROR: {error_messages['save_update_note_attachment_to_storage_container']}")
        return False

    return True
