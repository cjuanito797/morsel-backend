import requests
from django.conf import settings

def get_uber_access_token():
    token_url = settings.UBER_TOKEN_URL
    client_id = settings.UBER_CLIENT_ID
    client_secret = settings.UBER_CLIENT_SECRET
    scope = settings.UBER_SCOPE

    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
        'scope': scope,
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    response = requests.post(token_url, data=payload, headers=headers)
    response.raise_for_status()

    token_data = response.json()
    return token_data.get('access_token')