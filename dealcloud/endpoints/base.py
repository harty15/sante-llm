from abc import ABC, abstractmethod
from typing import Dict, Optional
import requests

class APIEndpoint(ABC):
    def __init__(self, token_manager, base_url: str):
        self.token_manager = token_manager
        self.base_url = base_url

    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict:
        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {self.token_manager.get_valid_token()}"}
        response = requests.request(method, url, headers=headers, params=params, json=data)
        response.raise_for_status()
        return response.json()

    @abstractmethod
    def get(self, *args, **kwargs):
        pass 