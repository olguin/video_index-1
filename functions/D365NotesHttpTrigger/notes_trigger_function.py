import json
import logging
import azure.functions as func
from shared_code.configuration_file import ConfigurationFile
from D365NotesHttpTrigger.note import Note
import os


class NotesTriggerFunction:

    @classmethod
    def copy_note_attachment_to_blob_container(cls, crm_organization_URI: str, note_id: str, oauth_token: str) -> func.HttpResponse:
        try:
            storage_account_name = os.environ["DT_INDEXED_STORAGE_ACCOUNT_NAME"]
            storage_container = os.environ["DT_INDEXED_CONTAINER"]
            crm_request_headers = {
                'Authorization': 'Bearer ' + oauth_token,
                'OData-MaxVersion': '4.0',
                'OData-Version': '4.0',
                'Accept': 'application/json',
                'Content-Type': 'application/json; charset=utf-8',
                'Prefer': 'odata.include-annotations=OData.Community.Display.V1.FormattedValue'
            }

            file_request_headers = {
                'Authorization': 'Bearer ' + oauth_token,
                'Content-Type': 'application/octet-stream',
            }

            # full path to D365 Field Service REST api endpoint
            rest_api_URL: str = crm_organization_URI + '/api/data/v9.1'

            metadata_tags_values = {}

            if(oauth_token != ''):
                note: Note = Note.find(
                    rest_api_URL, crm_request_headers, note_id)

            if note is not None:
                if note.has_video_attachment():
                    configuration_file = ConfigurationFile.load(storage_account_name, storage_container, os.environ["DT_CONFIG_FILE"])
                    metadata_tags_values = configuration_file.get_metadata_values(crm_organization_URI, crm_request_headers, note.asdict())
                    note_video_content = note.download_attachment(rest_api_URL, file_request_headers)
                    if note_video_content is None:
                        raise RuntimeError("Error downloading attachment.")

                note.upload_attachment_to_container(note_video_content, metadata_tags_values, storage_account_name,
                                                    storage_container, os.environ["DT_AUTH_TOKEN_ENDPOINT"])

            return func.HttpResponse(json.dumps(metadata_tags_values, ensure_ascii=False), mimetype="application/json", status_code=200)
        except Exception as ex:
            error_message = f"Error on Http Note Trigger: {ex}"
            logging.error(error_message)
            return func.HttpResponse(json.dumps(error_message, ensure_ascii=False), mimetype="application/json", status_code=400)
