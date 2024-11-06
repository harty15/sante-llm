from datetime import datetime, timedelta
from typing import Dict, Any
import requests

class TokenManager:
    def __init__(self, client_id: str, client_secret: str, base_url: str):
        """Initialize the token manager with client credentials"""
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None

    def get_valid_token(self) -> str:
        """Get a valid access token, refreshing if necessary"""
        if self._is_token_valid():
            return self.access_token
        elif self.refresh_token:
            self._refresh_token()
        else:
            self._request_new_token()
        return self.access_token

    def _is_token_valid(self) -> bool:
        """Check if the current token is still valid"""
        return self.access_token and self.token_expiry and datetime.now() < self.token_expiry

    def _request_new_token(self) -> None:
        """Request a new token using client credentials"""
        url = f"{self.base_url}/api/rest/v1/oauth/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "data user_management"
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        self._update_token_info(response.json())

    def _refresh_token(self) -> None:
        """Refresh the access token using the refresh token"""
        url = f"{self.base_url}/api/rest/v1/oauth/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        self._update_token_info(response.json())

    def _update_token_info(self, token_data: Dict[str, Any]) -> None:
        """Update token information from response data"""
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data.get("refresh_token")  # May not always be present
        self.token_expiry = datetime.now() + timedelta(seconds=token_data["expires_in"])

    # ... rest of TokenManager class methods ... 