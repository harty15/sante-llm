from typing import Dict, List, Optional
from dealcloud.endpoints.base import APIEndpoint

class UserManagementEndpoint(APIEndpoint):
    def get(self, params: Optional[Dict] = None) -> List[Dict]:
        """Get users with optional filtering parameters"""
        return self._make_request("GET", "/api/rest/v1/management/user", params=params)

    def get_users(self, modified_since: Optional[str] = None, email: Optional[str] = None) -> List[Dict]:
        """
        Get users with optional filters for modification date and email
        """
        params = {}
        if modified_since:
            params["modifiedSince"] = modified_since
        if email:
            params["email"] = email
        return self.get(params=params)

    def create_user(self, user_data: Dict) -> Dict:
        """Create a new user"""
        return self._make_request("POST", "/api/rest/v1/management/user", data=user_data)

    def update_user(self, user_data: Dict) -> Dict:
        """Update an existing user"""
        return self._make_request("PUT", "/api/rest/v1/management/user", data=user_data)

    def delete_user(self, user_id: int) -> None:
        """Delete a user by ID"""
        self._make_request("DELETE", f"/api/rest/v1/management/user?userId={user_id}")

    # ... rest of UserManagementEndpoint methods ... 