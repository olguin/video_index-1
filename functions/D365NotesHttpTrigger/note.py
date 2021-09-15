
from dataclasses import dataclass
import requests
import logging


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
    def find(cls, rest_api_prefix: str, rest_headers: str, note_id: str, error_messages: dict) -> "Note":
        try:
            params = {'note_id': note_id}
            note_web_api_query = rest_api_prefix + \
                (Note.NOTE_ENDPOINT.format(**params))
            note_res = requests.get(note_web_api_query, headers=rest_headers)

            a_note = Note.from_dict(note_id, note_res.json())

            return a_note
        except Exception as ex:
            logging.error(f"NOTE - find NOTE EXCEPTION:{ex}")
            error_messages["Note.find"] = str(ex)
            return None

    def has_video_attachment(self) -> bool:
        return self.object_type == "msdyn_workorder" and self.is_document and "video" in self.mime_type
