
from dataclasses import dataclass
import dataclasses
import requests
import logging
import base64
import datetime
import os
from shared_code.oauth_client import OauthClient


@dataclass
class Note:
    note_id: str
    is_document: bool
    object_type: str
    work_order_id: str
    mime_type: str
    created_on: str
    filesize: int
    filename: str
    created_by: str

    NOTE_ENDPOINT: str = "/annotations({note_id})?$select=isdocument,objecttypecode,_objectid_value,mimetype,createdon,filesize,filename&$expand=createdby($select=fullname)"
    ATTACHMENT_ENDPOINT: str = "/annotations({note_id})/documentbody/$value"
    STORAGE_RESOURCE: str = "https://storage.azure.com/"

    @classmethod
    def from_dict(cls, note_id, data: dict) -> "Note":
        return cls(note_id,
                   bool(data["isdocument"]),
                   data["objecttypecode"],
                   data["_objectid_value"],
                   data["mimetype"],
                   data["createdon"],
                   int(data["filesize"]),
                   data["filename"],
                   data["createdby"]["fullname"])

    @classmethod
    def find(cls, rest_api_prefix: str, rest_headers: str, note_id: str) -> "Note":
        try:
            logging.info(f"ENTERING FIND Note:{note_id}")
            params = {'note_id': note_id}
            note_web_api_query = rest_api_prefix + \
                (Note.NOTE_ENDPOINT.format(**params))
            logging.info(f"ENTERING FIND QUERY:{note_web_api_query}")
            note_res = requests.get(note_web_api_query, headers=rest_headers)
            logging.info(f"ENTERING FIND RESPONSE:{note_res.json()}")
            a_note = Note.from_dict(note_id, note_res.json())

            return a_note
        except Exception as ex:
            logging.error(f"Error in Note.find: Error:{ex}")
            raise

    def has_video_attachment(self) -> bool:
        return self.object_type == "msdyn_workorder" and self.is_document and "video" in self.mime_type

    def download_attachment(self, rest_api_prefix: str, rest_headers: str) -> bytearray:
        downloaded_file = None
        try:
            params = {'note_id': self.note_id}
            file_rest_api = rest_api_prefix + \
                Note.ATTACHMENT_ENDPOINT.format(**params)
            file_rest_headers = dict(rest_headers)

            rest_response = requests.get(file_rest_api, headers=file_rest_headers)
            downloaded_file = bytearray(base64.b64decode(rest_response.content))
        except Exception as ex:
            logging.error(f"Error in download_note_attachment:{ex}")
            raise

        return downloaded_file

    def upload_attachment_to_container(self, note_attachment, metadata_tags, account_name, container, oauth_endpoint) -> bool:
        storage_auth_token_result = OauthClient.get_oauth_token_response(oauth_endpoint, self.STORAGE_RESOURCE)

        if storage_auth_token_result.status_code != 200:
            logging.error(
                f"Error requesting Oauth token on upload_attachment_to_container - Status code: {storage_auth_token_result.status_code}, Http Error:{storage_auth_token_result.text}")
            raise RuntimeError(
                f"Error requesting Oauth token - Status code: {storage_auth_token_result.status_code}, Http Error:{storage_auth_token_result.text}")

        storage_auth_token = storage_auth_token_result.json()["token"]
        datetime_value = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        storage_request_headers = self.get_storage_request_header(len(note_attachment), metadata_tags, datetime_value, storage_auth_token)

        blob_storage_endpoint = f"https://{account_name}.blob.core.windows.net/{container}/{self.filename}"

        put_blob_result = requests.put(
            blob_storage_endpoint, data=note_attachment, headers=storage_request_headers)

        logging.info(
            f"PUT STORAGE HTTP CODE: {put_blob_result.status_code}, RESPONSE:{put_blob_result.text}")
        if (put_blob_result.status_code != 201):
            error_message = f"Error saving {self.filename} on {account_name}/{container} - Status code: {put_blob_result.status_code}, Http Error:{put_blob_result.text}"
            logging.error(error_message)
            raise RuntimeError(error_message)

        return True

    def get_storage_request_header(self, note_attachment_length: int, metadata_tags: dict, datetime_value: str, storage_auth_token):
        meta_prefix = "x-ms-meta-"

        metadata_header = {}
        for tag_key in metadata_tags.keys():
            metadata_header.update({meta_prefix+tag_key: metadata_tags[tag_key]})

        storage_request_headers = {
            'Authorization': 'Bearer ' + storage_auth_token,
            'Content-Type': 'application/octet-stream',
            'x-ms-version': '2020-10-02',
            'x-ms-date': f"{datetime_value}",
            'x-ms-blob-type': 'BlockBlob',
            'Content-Length': f"{note_attachment_length}",
        }

        storage_request_headers.update(metadata_header)
        return storage_request_headers

    def asdict(self) -> dict:
        return dataclasses.asdict(self)
