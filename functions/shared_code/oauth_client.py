import requests
from requests.models import Response

class OauthClient:
    @classmethod
    def get_oauth_token_response(cls, auth_token_endpoint, resource)-> Response:

        oauth_data_params = {'resource_id': f"{resource}"}
        auth_token_result = requests.post(
            auth_token_endpoint, json=oauth_data_params)
        return auth_token_result