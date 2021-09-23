import azure.functions as func
import logging
import requests
import json
import os


def main(req: func.HttpRequest) -> func.HttpResponse:
    # set these values to retrieve the oauth token

    resource_id = req.get_json()["resource_id"]
    logging.info(f"NOTE OAUTH HTTP function resource parameter: {resource_id}.")
    client_id = '87704f6a-f56f-4992-95f5-5aa57e17388e' # application client id
    username = os.environ["DT_CRM_USER_NAME"]
    user_password = os.environ["DT_CRM_USER_PASSWORD"]
    token_endpoint = 'https://login.microsoftonline.com/639be87d-9250-4b32-afb6-3ec84932b34b/oauth2/token' # oauth token endpoint
    # build the authorization token request
    token_body = {
        'client_id':client_id,
        'resource':resource_id,
        'username':username,
        'password':user_password,
        'grant_type':'password'
    }

    # make the token request
    token_res = requests.post(token_endpoint, data=token_body)

    # set access_token variable to empty string
    access_token = ''
    result = {}

    # extract the access token
    try:
        access_token = token_res.json()['access_token']
        result = {"token": access_token}

    except Exception as ex:
        # handle any missing key errors
        result = json.dumps(ex)

    finally:
        logging.info(f'Python HTTP trigger function processed a request. {token_res.json()} response')
        return func.HttpResponse(json.dumps(result, ensure_ascii=False), mimetype="application/json")
