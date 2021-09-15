import azure.functions as func
import requests
import json
import os
import logging
import base64
import datetime
from functools import reduce
import operator
from D365NotesHttpTrigger.note import Note


def main(req: func.HttpRequest) -> func.HttpResponse:
    error_messages = {}
    req_body = req.get_json()
    note_id = req_body["PrimaryEntityId"]
    try:
        logging.info(
            f"NOTE HTTP trigger function processed a request with  note_id: {req_body['PrimaryEntityId']}.")
        crm_organization_URI = 'https://doubletime.crm.dynamics.com'
        crm_auth_token_result = get_oauth_token_response(crm_organization_URI)

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
    note_response = {}
    # full path to D365 Field Service REST api endpoint
    rest_api_URL: str = crm_organization_URI+'/api/data/v9.1'

    metadata_tags_values = {}

    if(oauth_token != ''):
        note: Note = Note.find(
            rest_api_URL, crm_request_headers, note_id, error_messages)

    if note is not None:
        if note.has_video_attachment():

            list_of_metadata_definition = get_metadata_definition(
                os.environ["STORAGE_ACCOUNT_NAME"], os.environ["STORAGE_CONTAINER"], os.environ["CONFIG_FILE"], error_messages)
            logging.info(
                f"LIST OF METADATA DEFINITIONS:{list_of_metadata_definition}")

            metadata_tags_values = get_metadata_values(
                crm_organization_URI, crm_request_headers, list_of_metadata_definition, note_response, error_messages)

            note_video_content = download_note_attachment(
                rest_api_URL, note_id, file_request_headers, error_messages)
            if note_video_content is None:
                return func.HttpResponse(json.dumps(error_messages, ensure_ascii=False), mimetype="application/json",  status_code=401)

            logging.info(
                f"ENV VARIABLES:{os.environ['STORAGE_ACCOUNT_NAME']}, {os.environ['STORAGE_CONTAINER']}")
            error_saving_attachment = save_update_note_attachment_to_storage_container(
                note_response, metadata_tags_values, note_video_content,  os.environ["STORAGE_ACCOUNT_NAME"], os.environ["STORAGE_CONTAINER"], error_messages)

    if note is None or error_in_work_order_request or error_saving_attachment:
        return func.HttpResponse(json.dumps(error_messages, ensure_ascii=False), mimetype="application/json",  status_code=401)
    else:
        return func.HttpResponse(json.dumps(metadata_tags_values, ensure_ascii=False), mimetype="application/json",  status_code=200)


def get_metadata_values(base_url, crm_request_headers, list_of_metadata_definition, note_response, error_messages):
    metadata_tags_values = {}

    for metadata_definition in list_of_metadata_definition:
        tags_values = get_tags_from_definition(
            note_response, metadata_definition, base_url, crm_request_headers, error_messages)
        metadata_tags_values.update(tags_values)

    return metadata_tags_values


def get_oauth_token_response(resource):
    auth_token_endpoint = os.environ["AUTH_TOKEN_ENDPOINT"]
    oauth_data_params = {'resource_id': f"{resource}"}
    auth_token_result = requests.post(
        auth_token_endpoint, json=oauth_data_params)
    return auth_token_result


def get_metadata_definition(account_name, container, file_name, error_messages):
    file_content_response = get_json_file_from_blog(
        account_name, container, file_name, error_messages)
    content_json = file_content_response.json()
    logging.info(f"CONTENT FILE JSON:{content_json}")
    return content_json["metadata"]


def get_json_file_from_blog(account_name, container, file_name, error_messages):
    storage_resource = "https://storage.azure.com/"
    get_blob_result = ""

    storage_auth_token_result = get_oauth_token_response(storage_resource)

    if storage_auth_token_result.status_code != 200:
        error_messages['get_json_file_from_blog-oauth_storage_request'] = f"Http Status code: {storage_auth_token_result.status_code}, Http Error:{storage_auth_token_result.text}"
        logging.error(
            f"get_json_file_from_blog  - OAUTH STORAGE ERROR: {error_messages['get_json_file_from_blog-oauth_storage_request']}")
    else:

        date = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        storage_request_headers = {
            'Authorization': 'Bearer ' + storage_auth_token_result.json()["token"],
            'Content-Type': 'application/json',
            'x-ms-version': '2020-10-02',
            'x-ms-date': f"{date}",
            'x-ms-blob-type': 'BlockBlob'
        }

        blob_storage_endpoint = f"https://{account_name}.blob.core.windows.net/{container}/{file_name}"
        get_blob_result = requests.get(
            blob_storage_endpoint, headers=storage_request_headers)
        if get_blob_result.status_code != 200:
            error_messages['get_json_file_from_blog'] = f"Http Status code: {get_blob_result.status_code}, Http Error:{get_blob_result.text}"
            logging.error(
                f"get_json_file_from_blog method - get Blob request : {error_messages['get_json_file_from_blog']}")
    return get_blob_result


def get_tags_from_definition(note_response, tags_definitions, base_url, rest_headers,  error_messages):
    tags = {}
    try:
        query_key = tags_definitions["query_key"]
        record_id = note_response[query_key]
        format_params = {"base_url": base_url, "query_key": record_id}
        object_rest_api_query = tags_definitions["query"].format(
            **format_params)

        record_url = tags_definitions["record_url"]

        query_response = requests.get(
            object_rest_api_query, headers=rest_headers)
        query_response_json = query_response.json()

        for tag_definition in tags_definitions["tags"]:

            tag_type = tag_definition.get("type")
            tag_key = tag_definition["tag"]
            tag_field = tag_definition["field"]

            if (tag_type is not None and tag_type == "URL"):
                tag_entity = tag_definition["entity"]
                tag_with_value = get_url_tag_value(
                    query_response_json, tag_key, record_url, base_url, tag_entity, tag_field)

            else:
                tag_with_value = get_tag_value(
                    query_response_json, tag_key, tag_field)
            tags.update(tag_with_value)

    except Exception as ex:
        logging.error(f"GET_TAGS_FOR_OBJECT EXCEPTION:{str(ex)}")
        error_messages["get_tags_from_definition"] = str(ex)
    return tags


def get_tag_value(query_json_response, tag_key, tag_field_path):
    field_path = tag_field_path.split("/")
    tag_value = get_from_dict(query_json_response, field_path)
    return {tag_key: tag_value}


def get_url_tag_value(query_json_response, tag_key, record_url, base_url, tag_entity, tag_field_path):
    field_path = tag_field_path.split("/")

    tag_id_value = get_from_dict(query_json_response, field_path)
    record_url_to_replace = record_url
    format_params = {"base_url": base_url,
                     "ent_name": tag_entity, "ent_id": tag_id_value}
    record_url_to_replace = record_url_to_replace.format(**format_params)
    return {tag_key: record_url_to_replace}


def get_from_dict(data_dict, field_path):
    return reduce(operator.getitem, field_path, data_dict)


def download_note_attachment(rest_api_prefix, note_id, rest_headers, error_messages):
    downloaded_file = None
    try:
        file_rest_api = rest_api_prefix + \
            f"/annotations({note_id})/documentbody/$value"
        file_rest_headers = dict(rest_headers)

        rest_response = requests.get(file_rest_api, headers=file_rest_headers)
        downloaded_file = bytearray(base64.b64decode(rest_response.content))
    except Exception as ex:
        logging.error(f"Error in download_note_attachment:{ex}")
        error_messages["download_note_attachment"] = f"  - Http Status code: {rest_response.status_code}, Http Error:{rest_response.text}"
        return error_messages["download_note_attachment"]

    return downloaded_file


def save_update_note_attachment_to_storage_container(note, metadata_tags, note_attachment, account_name, container, error_messages):
    storage_resource = "https://storage.azure.com/"
    meta_prefix = "x-ms-meta-"
    storage_auth_token_result = get_oauth_token_response(storage_resource)

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
