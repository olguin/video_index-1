import os
from D365NotesHttpTrigger.notes_trigger_function import NotesTriggerFunction
from D365NotesHttpTrigger.note import Note
import pytest
import uuid
import responses

import json
from http import HTTPStatus


@pytest.fixture()
def fake_note_with_video_attachment():
    """Fixture that returns a static D365 note  record in json format."""
    with open("tests/data/note_with_video_attach.json") as f:
        return json.load(f)


@pytest.fixture()
def fake_config_file():
    """Fixture that returns a sample configuration file"""
    with open("tests/data/dt_config_example.json") as f:
        return json.load(f)


@pytest.fixture()
def fake_attachment():
    """Fixture that returns base64 encoded file attachment"""
    return "AAAAFGZ0eXBxdCAgAAAAAHF0ICAAAAAId2lkZQHqCnxtZGF0ANBABwDmm8w+vmGhA3IrMS+Tn8XvKc8/2fXz51rjXl8gn8qvXBK9zHBbcz2awgSsYhBQTCTBCd02dEs0"


@pytest.fixture()
def fake_work_order():
    """Fixture that returns work order data and related fields"""
    with open("tests/data/work_order_record.json") as f:
        return json.load(f)


@responses.activate
def test_copy_note_attachment_to_blob_container_returns_status_ok_on_success(fake_note_with_video_attachment, fake_attachment, fake_config_file, fake_work_order):
    """Test return note's attachment as bytearray """

    note_id_value: str = str(uuid.uuid4())
    base_url = 'https://doubletime.crm.dynamics.com'
    oauth_url = 'https://dtdv-video-index-uspklrodz4yzi.azurewebsites.net/api/Dynamic365AuthToken?code=V5UYqIu=='
    oauth_token = "AAABBBCCCDDDEEE"
    config_file_name = "dt_config_example.json"
    os.environ["CONFIG_FILE"] = config_file_name

    os.environ["AUTH_TOKEN_ENDPOINT"] = oauth_url
    account_name = "storage_account_a"
    container = "container_a"
    os.environ["STORAGE_ACCOUNT_NAME"] = account_name
    os.environ["STORAGE_CONTAINER"] = container

    conf_file_storage_endpoint = f"https://{account_name}.blob.core.windows.net/{container}/{config_file_name}"

    # mock to return fake conf file
    responses.add(responses.GET, conf_file_storage_endpoint, json=fake_config_file, status=HTTPStatus.OK)

    attachment_api_uri = base_url + '/api/data/v9.1' + Note.ATTACHMENT_ENDPOINT.format(note_id=note_id_value)
    crm_api_uri = base_url + '/api/data/v9.1' + Note.NOTE_ENDPOINT.format(note_id=note_id_value)

    # Mock for Note.find
    responses.add(responses.GET, crm_api_uri, json=fake_note_with_video_attachment, status=HTTPStatus.OK)

    filename = "deltajet_engines.mp4"

    blob_storage_endpoint = f"https://{account_name}.blob.core.windows.net/{container}/{filename}"

    # mock for note.download_attachment
    responses.add(responses.GET, attachment_api_uri, json=fake_attachment, status=HTTPStatus.OK)
    # mock for oauth get_token
    responses.add(responses.POST, oauth_url, json={"token": oauth_token}, status=HTTPStatus.OK)
    # mock for saving attachment to blob storage container
    responses.add(responses.PUT, blob_storage_endpoint, json={}, status=HTTPStatus.CREATED)

    metadata_url = "{base_url}/api/data/v9.1/msdyn_workorders({query_key})?$expand=msdyn_customerasset($select=msdyn_name;$expand=msdyn_product($select=name,productid)),msdyn_serviceaccount($select=name),msdyn_billingaccount($select=name)" # noqa 

    work_order_id = "be343d0c-60c9-43e6-a1ba-9ea03a0a34ea"
    format_params = {"base_url": base_url, "query_key": work_order_id}
    object_rest_api_query = metadata_url.format(**format_params)

    # mock  object_rest_api_query to get metadata tags
    responses.add(responses.GET, object_rest_api_query, json=fake_work_order, status=HTTPStatus.OK)

    copy_response = NotesTriggerFunction.copy_note_attachment_to_blob_container(base_url, note_id_value, oauth_token)

    assert copy_response.status_code == 200


@responses.activate
def test_copy_note_attachment_to_blob_container_returns_invalid_request_on_failure(fake_note_with_video_attachment, fake_attachment, fake_config_file, fake_work_order):
    """Test return note's attachment as bytearray """

    note_id_value: str = str(uuid.uuid4())
    base_url = 'https://doubletime.crm.dynamics.com'
    oauth_url = 'https://dtdv-video-index-uspklrodz4yzi.azurewebsites.net/api/Dynamic365AuthToken?code=V5UYqIu=='
    oauth_token = "AAABBBCCCDDDEEE"
    config_file_name = "dt_config_example.json"
    os.environ["CONFIG_FILE"] = config_file_name

    os.environ["AUTH_TOKEN_ENDPOINT"] = oauth_url
    account_name = "storage_account_a"
    container = "container_a"
    os.environ["STORAGE_ACCOUNT_NAME"] = account_name
    os.environ["STORAGE_CONTAINER"] = container

    conf_file_storage_endpoint = f"https://{account_name}.blob.core.windows.net/{container}/{config_file_name}"

    # mock to return fake conf file
    responses.add(responses.GET, conf_file_storage_endpoint, json=fake_config_file, status=HTTPStatus.OK)

    attachment_api_uri = base_url + '/api/data/v9.1' + Note.ATTACHMENT_ENDPOINT.format(note_id=note_id_value)
    crm_api_uri = base_url + '/api/data/v9.1' + Note.NOTE_ENDPOINT.format(note_id=note_id_value)

    # Mock for Note.find
    responses.add(responses.GET, crm_api_uri, json=fake_note_with_video_attachment, status=HTTPStatus.OK)

    filename = "deltajet_engines.mp4"

    blob_storage_endpoint = f"https://{account_name}.blob.core.windows.net/{container}/{filename}"

    # mock for note.download_attachment
    responses.add(responses.GET, attachment_api_uri, json=fake_attachment, status=HTTPStatus.OK)
    # mock for oauth get_token
    responses.add(responses.POST, oauth_url, json={"token": oauth_token}, status=HTTPStatus.OK)

    metadata_url = "{base_url}/api/data/v9.1/msdyn_workorders({query_key})?$expand=msdyn_customerasset($select=msdyn_name;$expand=msdyn_product($select=name,productid)),msdyn_serviceaccount($select=name),msdyn_billingaccount($select=name)"  # noqa 
    work_order_id = "be343d0c-60c9-43e6-a1ba-9ea03a0a34ea"
    format_params = {"base_url": base_url, "query_key": work_order_id}
    object_rest_api_query = metadata_url.format(**format_params)
    # mock  object_rest_api_query to get metadata tags
    responses.add(responses.GET, object_rest_api_query, json=fake_work_order, status=HTTPStatus.OK)

    # mock for saving attachment to blob storage container BUT RETURNUNG FORBIDDEN!!!
    responses.add(responses.PUT, blob_storage_endpoint, json={}, status=HTTPStatus.FORBIDDEN)

    copy_response = NotesTriggerFunction.copy_note_attachment_to_blob_container(base_url, note_id_value, oauth_token)
    assert copy_response.status_code == 400
