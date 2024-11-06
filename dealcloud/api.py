from .auth import TokenManager
from dealcloud.endpoints.schema import SchemaEndpoint
from dealcloud.endpoints.data import DataEndpoint
from dealcloud.endpoints.user import UserManagementEndpoint

class DealCloudAPI:
    def __init__(self, client_id: str, client_secret: str, base_url: str):
        self.token_manager = TokenManager(client_id, client_secret, base_url)
        self.schema = SchemaEndpoint(self.token_manager, base_url)
        self.data = DataEndpoint(self.token_manager, base_url)
        self.user_management = UserManagementEndpoint(self.token_manager, base_url) 