import datetime
from shared_code.configuration_file import ConfigurationFile
import pytest
import uuid
import responses
import os

import json
from http import HTTPStatus


@pytest.fixture()
def fake_config_file():
    """Fixture that returns a sample configuration file"""
    with open("tests/data/dt_config_example.json") as f:
        return json.load(f)


@pytest.fixture()
def fake_work_order():
    """Fixture that returns work order data and related fields"""
    with open("tests/data/work_order_record.json") as f:
        return json.load(f)


@responses.activate
def test_load_config_file(fake_config_file):
    """Test load config file """
    oauth_url = 'https://dtdv-video-index-uspklrodz4yzi.azurewebsites.net/api/Dynamic365AuthToken?code=V5UYqIu=='
    os.environ["AUTH_TOKEN_ENDPOINT"] = oauth_url

    oauth_token = "AAABBBCCCDDDEEE"

    account_name = "storage_account_a"
    container = "container_a"
    config_file_name = "dt_config_example.json"
    blob_storage_endpoint = f"https://{account_name}.blob.core.windows.net/{container}/{config_file_name}"

    responses.add(responses.POST, oauth_url, json={"token": oauth_token}, status=HTTPStatus.OK)
    responses.add(responses.GET, blob_storage_endpoint, json=fake_config_file, status=HTTPStatus.OK)

    conf_file = ConfigurationFile.load(account_name, container, config_file_name)

    assert len(responses.calls) == 2
    assert responses.calls[0].request.url == oauth_url
    assert responses.calls[1].request.url == blob_storage_endpoint

    assert fake_config_file == conf_file.json_file_content
    assert config_file_name == conf_file.actual_file_name
    assert fake_config_file['metadata'] == conf_file.get_metadata_definition()


@responses.activate
def test_get_metadata_values(fake_config_file, fake_work_order):
    """Test load config file """
    config_file = ConfigurationFile(fake_config_file, "dt_config_example.json")

    metadata_url = "{base_url}/api/data/v9.1/msdyn_workorders({query_key})?$expand=msdyn_customerasset($select=msdyn_name;$expand=msdyn_product($select=name,productid)),msdyn_serviceaccount($select=name),msdyn_billingaccount($select=name)"

    base_url = "https://doubletime.crm.dynamics.com"
    work_order_id = str(uuid.uuid4())
    format_params = {"base_url": base_url, "query_key": work_order_id}
    object_rest_api_query = metadata_url.format(**format_params)

    note_dict = {"work_order_id": work_order_id}

    responses.add(responses.GET, object_rest_api_query, json=fake_work_order, status=HTTPStatus.OK)

    metadata_values = config_file.get_metadata_values(base_url, {}, note_dict)
    assert "00500" == metadata_values['Work_Order']
    assert "https://doubletime.crm.dynamics.com/main.aspx?cmdbar=false&navBar=off&newWindow=true&pagetype=entityrecord&etn=msdyn_workorder&id=be343d0c-60c9-43e6-a1ba-9ea03a0a34ea" == metadata_values[
        'Work_Order_URL']
    assert "National Grid" == metadata_values["Service_Account"]
    assert "National Grid" == metadata_values["Billing_Account"]
    assert "Step Down Transformer 5000V" == metadata_values["Customer_Asset"]
    assert "ABS Filament 3D Printer 4\"" == metadata_values["Product"]
