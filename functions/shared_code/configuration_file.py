from dataclasses import dataclass

from requests.models import Response
from shared_code.oauth_client import OauthClient
import logging
import datetime
import requests
import os
from functools import reduce
import operator


@dataclass
class ConfigurationFile:
    json_file_content:dict
    actual_file_name:str

    @classmethod 
    def load(cls, account_name:str, container:str, file_name:str) -> "ConfigurationFile":
        DEFAULT_FILE_NAME = "config.json"
        name_of_actual_file = DEFAULT_FILE_NAME
        if file_name is not None:
            name_of_actual_file = file_name
        file_content_response = ConfigurationFile.get_json_file_from_storage_container(account_name, container, name_of_actual_file)
        logging.info(f"ConfigurationFile - READING CONFIG FILE:{name_of_actual_file}")
            
        return cls(file_content_response.json(), name_of_actual_file )


    @classmethod 
    def get_json_file_from_storage_container(cls, account_name, container, file_name) -> Response:
        storage_resource = "https://storage.azure.com/"
        get_blob_result = None

        storage_auth_token_result = OauthClient.get_oauth_token_response(os.environ["AUTH_TOKEN_ENDPOINT"], storage_resource)

        if storage_auth_token_result.status_code != 200:          
            error_message = f"Http Status code: {storage_auth_token_result.status_code}, Http Error:{storage_auth_token_result.text}"
            logging.error(
            "Error on get_json_file_from_storage_container - "+error_message)
            raise RuntimeError(error_message)
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
               error_message = f"Http Status code: {get_blob_result.status_code}, Http Error:{get_blob_result.text}"
               logging.error(
                f"get_json_file_from_blog method - get Blob request - " + error_message)
        return get_blob_result
       
    def get_metadata_definition(self) -> list:
        if (self.json_file_content == None):
           raise RuntimeError("Error config file not loaded.")

        logging.info(f"CONTENT FILE JSON:{self.json_file_content}")
        return self.json_file_content["metadata"]


    def get_metadata_values(self, base_url: str, crm_request_headers: str,  note_dict: dict):
       metadata_tags_values = {}
       list_of_metadata_definition = self.get_metadata_definition()
       for metadata_definition in list_of_metadata_definition:
           tags_values = self.get_tags_from_definition(
           note_dict, metadata_definition, base_url, crm_request_headers)
           metadata_tags_values.update(tags_values)

       return metadata_tags_values



    def get_tags_from_definition(self, note_dict: dict, tags_definitions: dict, base_url: str, rest_headers: str):
       tags = {}
       try:
           query_key = tags_definitions["query_key"]
           record_id = note_dict[query_key]
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
                   tag_with_value = self.get_url_tag_value(
                       query_response_json, tag_key, record_url, base_url, tag_entity, tag_field)

               else:
                   tag_with_value = self.get_tag_value(
                       query_response_json, tag_key, tag_field)
               tags.update(tag_with_value)

       except Exception as ex:
           logging.error(f"Error in  get_tags_from_definition:{ex}")
           raise
       return tags


    def get_tag_value(self, query_json_response, tag_key, tag_field_path):
       field_path = tag_field_path.split("/")
       tag_value = self.get_from_dict(query_json_response, field_path)
       return {tag_key: tag_value}


    def get_url_tag_value(self, query_json_response, tag_key, record_url, base_url, tag_entity, tag_field_path):
       field_path = tag_field_path.split("/")

       tag_id_value = self.get_from_dict(query_json_response, field_path)
       record_url_to_replace = record_url
       format_params = {"base_url": base_url,
                     "ent_name": tag_entity, "ent_id": tag_id_value}
       record_url_to_replace = record_url_to_replace.format(**format_params)
       return {tag_key: record_url_to_replace}


    def get_from_dict(self, data_dict, field_path):
       return reduce(operator.getitem, field_path, data_dict)

    