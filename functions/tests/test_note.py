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
        api_uri = base_url+Note.NOTE_ENDPOINT.format(note_id=note_id_value)

        rest_headers = {}
        responses.add(responses.GET, api_uri,
                      json=fake_note_with_video_attachment, status=HTTPStatus.OK)
        error_messages = {}
        a_note = Note.find(base_url, rest_headers,
                           note_id_value, error_messages)
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
        error_messages = {}

        downloaded_file = a_note.download_attachment(base_url,rest_headers, error_messages)

        assert downloaded_file is not None
        assert base64.b64decode(fake_attachment) == downloaded_file
        assert len(responses.calls) == 1
