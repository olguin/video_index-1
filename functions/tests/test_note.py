import datetime
from D365NotesHttpTrigger.note import Note
import pytest
import uuid
import responses

import json
from http import HTTPStatus
import base64


@pytest.fixture()
def fake_note_with_video_attachment():
        """Fixture that returns a static D365 note  record in json format."""
        with open("tests/data/note_with_video_attach.json") as f:
            return json.load(f)

@pytest.fixture()
def fake_note_with_pdf_attachment():
        """Fixture that returns a static D365 note  record in json format."""
        with open("tests/data/note_with_pdf_attach.json") as f:
            return json.load(f)

@pytest.fixture()
def fake_attachment():
        """Fixture that returns base64 encoded file attachment"""
        return "AAAAFGZ0eXBxdCAgAAAAAHF0ICAAAAAId2lkZQHqCnxtZGF0ANBABwDmm8w+vmGhA3IrMS+Tn8XvKc8/2fXz51rjXl8gn8qvXBK9zHBbcz2awgSsYhBQTCTBCd02dEs0"


@responses.activate
def test_find_note(fake_note_with_video_attachment):
        """Test find process correctly note record if returned by response"""

        note_id_value: str = str(uuid.uuid4())
        base_url = 'https://doubletime.crm.dynamics.com'
        api_uri = base_url+'/api/data/v9.1'+Note.NOTE_ENDPOINT.format(note_id=note_id_value)

        rest_headers = {}
        responses.add(responses.GET, api_uri,
                      json=fake_note_with_video_attachment, status=HTTPStatus.OK)
        a_note = Note.find(base_url+'/api/data/v9.1', rest_headers,
                           note_id_value)
        assert a_note == Note.from_dict(
            note_id_value, fake_note_with_video_attachment)
        assert len(responses.calls) == 1    

def test_note_related_with_work_order_has_video_attachment(fake_note_with_video_attachment):
        """Test note with video attachment returns true """

        note_id_value: str = str(uuid.uuid4())
        a_note = Note.from_dict(note_id_value, fake_note_with_video_attachment)
        assert a_note.has_video_attachment()
        assert a_note.is_document
        assert "video" in a_note.mime_type
        assert a_note.object_type == "msdyn_workorder"
       

def test_note_asdict(fake_note_with_video_attachment):
        """Test note asDict method """

        note_id_value: str = str(uuid.uuid4())
        a_note = Note.from_dict(note_id_value, fake_note_with_video_attachment)
        assert  "msdyn_workorder" == a_note.asdict()['object_type'] 
        assert  a_note.work_order_id == a_note.asdict()['work_order_id'] 
        assert  a_note.filename == a_note.asdict()['filename'] 
        



def test_note_has_video_attachment_is_false_for_note_with_other_mime_type(fake_note_with_pdf_attachment):
        """Test note without video attachment returns false """

        note_id_value: str = str(uuid.uuid4())
        a_note = Note.from_dict(note_id_value, fake_note_with_pdf_attachment)
        assert not a_note.has_video_attachment()
        assert a_note.is_document
        assert not ("video" in a_note.mime_type)
        assert a_note.object_type == "msdyn_workorder"

@responses.activate
def test_download_attachment_gets_bytearray_from_base64_file(fake_note_with_video_attachment, fake_attachment):
        """Test return note's attachment as bytearray """

        note_id_value: str = str(uuid.uuid4())
        base_url = 'https://doubletime.crm.dynamics.com'

        api_uri = base_url+Note.ATTACHMENT_ENDPOINT.format(note_id=note_id_value)
        a_note = Note.from_dict(note_id_value, fake_note_with_video_attachment)
        rest_headers = {}
        responses.add(responses.GET, api_uri, json=fake_attachment, status=HTTPStatus.OK)

        downloaded_file = a_note.download_attachment(base_url,rest_headers)

        assert downloaded_file is not None
        assert base64.b64decode(fake_attachment) == downloaded_file
        assert len(responses.calls) == 1

def test_get_storage_request_header(fake_note_with_video_attachment):
        """ get_storage_request_header returns a properly formatted header for REST storage request to create blob file """
        meta_prefix = "x-ms-meta-"
        note_id_value: str = str(uuid.uuid4())
        a_note = Note.from_dict(note_id_value, fake_note_with_video_attachment)
        oauth_token="AAABBBCCCDDDEEE"
        TAG_A = "tag_a"
        TAG_B = "tag_b"
        metadata_tags = {TAG_A:"value_a", TAG_B:"value_b"}
        datetime_value = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        note_length = 1054

        storage_request_header = a_note.get_storage_request_header(note_length,metadata_tags, datetime_value,oauth_token)

        assert storage_request_header['Authorization'] == f"Bearer {oauth_token}"
        assert storage_request_header['Content-Length'] == '1054'
        assert storage_request_header['x-ms-blob-type'] == 'BlockBlob'
        assert storage_request_header['x-ms-date'] == datetime_value
        assert storage_request_header[meta_prefix+TAG_A] == "value_a"
        assert storage_request_header[meta_prefix+TAG_B] == "value_b"
        


@responses.activate
def test_upload_attachment_to_container(fake_note_with_video_attachment, fake_attachment):
        """Test return note's attachment as bytearray """

        note_id_value: str = str(uuid.uuid4())
        base_url = 'https://dt-fs-test2.crm.crm.dynamics.com'
        oauth_url = 'https://dtdv-video-index-uspklrodz4yzi.azurewebsites.net/api/Dynamic365AuthToken?code=V5UYqIu=='

        oauth_token="AAABBBCCCDDDEEE"

        account_name = "storage_account_a"
        container = "container_a"

        api_uri = base_url+Note.ATTACHMENT_ENDPOINT.format(note_id=note_id_value)
        a_note = Note.from_dict(note_id_value, fake_note_with_video_attachment)
        filename = a_note.filename

        blob_storage_endpoint = f"https://{account_name}.blob.core.windows.net/{container}/{filename}"

        rest_headers = {}
        responses.add(responses.GET, api_uri, json=fake_attachment, status=HTTPStatus.OK)
        responses.add(responses.POST, oauth_url, json={"token": oauth_token}, status=HTTPStatus.OK)
        responses.add(responses.PUT,blob_storage_endpoint, json={}, status=HTTPStatus.CREATED)

        downloaded_file = a_note.download_attachment(base_url, rest_headers)
        TAG_A = "tag_a"
        TAG_B = "tag_b"
        metadata_tags = {TAG_A:"value_a", TAG_B:"value_b"}
        assert a_note.upload_attachment_to_container(downloaded_file, metadata_tags, account_name, container, oauth_url)
        assert len(responses.calls) == 3
        assert responses.calls[0].request.url == api_uri
        assert responses.calls[1].request.url == oauth_url
        assert responses.calls[2].request.url == blob_storage_endpoint



@responses.activate
def test_upload_attachment_throws_exception_if_storage_api_returns_forbidden_or_internal_server_error(fake_note_with_video_attachment, fake_attachment):
        """Test return note's attachment as bytearray """

        note_id_value: str = str(uuid.uuid4())
        base_url = 'https://dt-fs-test2.crm.crm.dynamics.com'
        oauth_url = 'https://dtdv-video-index-uspklrodz4yzi.azurewebsites.net/api/Dynamic365AuthToken?code=V5UYqIu=='

        oauth_token="AAABBBCCCDDDEEE"

        account_name = "storage_account_a"
        container = "container_a"

        api_uri = base_url+Note.ATTACHMENT_ENDPOINT.format(note_id=note_id_value)
        a_note = Note.from_dict(note_id_value, fake_note_with_video_attachment)
        filename = a_note.filename

        blob_storage_endpoint = f"https://{account_name}.blob.core.windows.net/{container}/{filename}"

        rest_headers = {}
        responses.add(responses.GET, api_uri, json=fake_attachment, status=HTTPStatus.OK)
        responses.add(responses.POST, oauth_url, json={"token": oauth_token}, status=HTTPStatus.OK)
        responses.add(responses.PUT,blob_storage_endpoint, json={}, status=HTTPStatus.BAD_REQUEST)

        downloaded_file = a_note.download_attachment(base_url, rest_headers)
        TAG_A = "tag_a"
        TAG_B = "tag_b"
        metadata_tags = {TAG_A:"value_a", TAG_B:"value_b"}
        with pytest.raises(Exception) as e_info:
                a_note.upload_attachment_to_container(downloaded_file, metadata_tags, account_name, container, oauth_url)

        responses.add(responses.PUT,blob_storage_endpoint, json={}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        downloaded_file = a_note.download_attachment(base_url, rest_headers)
        TAG_A = "tag_a"
        TAG_B = "tag_b"
        metadata_tags = {TAG_A:"value_a", TAG_B:"value_b"}
        with pytest.raises(Exception) as e_info:
                a_note.upload_attachment_to_container(downloaded_file, metadata_tags, account_name, container, oauth_url)     
        

        

